from typing import Tuple
import socket
from ipaddress import ip_network, ip_address

from yew.core.looper import Looper, EndOfStream
from yew.core.info import Info
from yew.core.components import Component


class Server(Component):

	def set_looper(self, looper: Looper):
		self.looper = looper

	def __init__(self, name: str, config: dict):
		super().__init__(name, config)

	def parse_config(self, config: dict):
		"""
		Reads configuration. Here a YAML example:

		binding:
			port: 8080
			device: wlan0
			ip: 123.34.34.21
		accept:
			- ::ffff:127.0.0.0/120
		refuse:
			- ::ffff:192.168.1.1/120
		"""
		super().parse_config(config)

		# binding
		self.binding = config.get("binding", {})
		if not "port" in self.binding:
			raise ValueError("binding.port is mandatory")

		# subnet filter
		accept = config.get("accept", None)
		refuse = config.get("refuse", None)
		if accept is not None and refuse is not None:
			raise ValueError("Use either accept or refuse, not both.")

		self._filter_ip = None
		self._filter_subnets = []
		t = []
		if accept is not None:
			self._filter_ip = True
			t = accept
		if refuse is not None:
			self._filter_ip = False
			t = refuse
		for subnet in t:
			self._filter_subnets.append(ip_network(subnet))

	def can_accept_ip(self, ip):
		if self._filter_ip is None:
			return True
		else:
			target = ip_address(ip)
			for subnet in self._filter_subnets:
				if target in subnet:
					if self._filter_ip is True:
						return True
					else:
						return False
			if self._filter_ip is True:
				return False
			else:
				return True

	def create_server_socket() -> Tuple[socket.socket, Info]:
		"""
		Create a server socket for this server.
		"""
		raise NotImplementedError()

	def remove_sock(self, sock, info):
		self.looper.remove_sock(sock)

	def on_handler_error(self, sock: socket.socket, info, e: Exception):
		self.remove_sock(sock, info)
		self.logger.exception("An handler failed.")

	def on_connection_failure(self, sock: socket.socket, info, e: Exception):
		self.remove_sock(sock, info)
		if isinstance(e, EndOfStream):
			self.logger.debug("connection closed by the client.")
		else:
			self.logger.exception("Connection failure.")
