from yew.modules.base import UpStream, UpStreamError
from yew.core.info import Info
import socket
from typing import Tuple
import re


UPSTREAM_ERROR_PARENT_AUTHENTICATION = 0x01
UPSTREAM_ERROR_PARENT_UNREACHABLE = 0x02
UPSTREAM_ERROR_DESTINATION_UNREACHABLE = 0x03
UPSTREAM_ERROR_GENERIC = 0x04


class BindDeviceError(UpStreamError):
	pass


class BindIPError(UpStreamError):
	pass


class GAIError(UpStreamError):
	pass

class ForbiddenHostError(UpStreamError):
	pass


class TCPUpStream(UpStream):

	def open_connection(self, server, host: str, port: int, bind_device: str = None,
		bind_ip: str = None) -> tuple[socket.socket, Info]:
		"""Applies rules and creates a new socket.

		Raises:
			- ForbiddenHostError: Connections to this host are not allowed.
		"""
		if not self.can_connect_host(host):
			raise ForbiddenHostError(host)
		else:
			return self.create_socket(server, host, port, bind_device, bind_ip)

	def create_socket(self, server, host: str, port: int, bind_device: str = None,
		bind_ip: str = None) -> tuple[socket.socket, Info]:
		"""Creates a new socket.

		Args:
			- server: The server.
			- host: Remote host to connect.
			- port: Remote port to connect.
			- bind_device: Device to use (just for Linux).
			- bind_ip: IP address to bind (for Windows).

		Returns:
			The new socket paired with its Info.

		Raises:
			- BindDeviceError: If it was not possible to bound the socket to given device.
			- BindIPError: If it was not possible to bound the socket to given IP.
			- GAIError: If it was not possible to resolve the host address.
		"""
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setblocking(0)

		if bind_device != None:
			try:
				sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, bind_device.encode())
			except BaseException as e:
				raise BindDeviceError(f"unable to bind device {bind_device}")

		if bind_ip != None:
			try:
				sock.bind((bind_ip, 0))	# this is just for ipv4 - TODO check the address family - just for windows
			except BaseException as e:
				raise BindIPError(f"unable to bind ip {bind_ip}")

		try:
			sock.connect((host, port))
		except socket.gaierror as e:
			raise GAIError(f"unable to resolve address {host}")
		except BlockingIOError:
			pass
		info = self.create_info(server)
		info["upstream"] = self
		return sock, info

	def create_info(self, server):
		i = Info(server)
		i["handlers.write"] = server.connect_success
		return i

	def parse_config(self, config: dict):
		"""
		CONFIG:
			- allow (list[str], optional): regex to match allowed host.
			- disallow (list[str], optional): regex to match host to block.
		"""
		super().parse_config(config)

		self.allowed_host = config.get("allow", None)
		self.disallowed_host = config.get("disallow", None)
		if self.allowed_host is not None and self.disallowed_host is not None:
			raise ValueError("Cannot define both allow and disallow list.")
		# build regex
		self._filter_host_allow = None
		if self.allowed_host is not None:
			self._filter_host_allow = True
			self._filter_host_regex = re.compile("|".join(self.allowed_host))
		if self.disallowed_host is not None:
			self._filter_host_allow = False
			self._filter_host_regex = re.compile("|".join(self.disallowed_host))

	def can_connect_host(self, host: str) -> bool:
		if self._filter_host_allow is None:
			return True
		elif self._filter_host_allow is True:
			return self._filter_host_regex.search(host) is not None
		else:
			return self._filter_host_regex.search(host) is None


class ParentUpStream(TCPUpStream):

	def parse_config(self, config: dict):
		"""
		CONFIG:
			- host (str, required): hostname to connect to.
			- port (int ,required): port to connect to.
			- username (str, optional): username to use for authentication.
			- password (str, optional): password to use for authentication.
		"""
		super().parse_config(config)
		self.parent_host = config.get("host")
		self.parent_port = config.get("port")
		self.parent_usr = config.get("username", None)
		self.parent_pwd = config.get("password", None)

	def open_connection(self, server, host: str, port: int, bind_device: str = None,
		bind_ip: str = None) -> tuple[socket.socket, Info]:
		"""Applies rules and opens a new connection with the parent proxy. Original 
		tuple (host, port) is stored in the info.

		Raises:
			- ForbiddenHostError: Connections to this host are not allowed.
		"""
		if not self.can_connect_host(host):
			raise ForbiddenHostError(host)
		else:
			sock, info = self.create_socket(server, self.parent_host, self.parent_port, 
				bind_device, bind_ip)
			info["upstream.host_port"] = (host, port)
			return sock, info
