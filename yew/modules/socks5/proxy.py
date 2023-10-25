from yew.core.components import Component
from yew.core.info import Info
from yew.modules.tcp import TCPServer
from yew.modules.base import UpStreamError, message
from yew.modules.tcp.upstreams import ForbiddenHostError, GAIError, BindIPError, BindDeviceError
from typing import Tuple
from .socks5 import *
from .rules import Rules


class Proxy(TCPServer):

	def get_new_client_info(self):
		i = Info(self)
		i["handlers.read"] = self.read_wait_handshake
		return i

	def parse_config(self, config: dict):
		super().parse_config(config)
		self._upstream = Component.get("upstreams", config.get("upstream"))
		self.groups = config.get("group", None)
		if self.groups is not None:
			self.groups = Component.get("groups", self.groups)
		self.rules = config.get("rules", None)
		if self.rules is None:
			self.rules = Rules.build("", {})
		else:
			self.rules = Component.get("rules", self.rules)

	def get_upstream(self, request: ConnectRequest):
		return self.rules.get_upstream(request, self._upstream)

	def connect_fail(self, error, sock, info):
		"""
		Called by the upstream when socket/tunnel creation fails.
		TODO:
			- send something more specific to client
		"""
		self.logger.error(error)
		self.final_message(ConnectResponse.error(SOCKS5_REPLY_GENERIC_ERROR), sock, info)

	def connect_success(self, sock, info):
		"""
		Called by the upstream when socket/tunnel is ready for write.
		"""
		self.looper.unregister_for_write(sock)
		try:
			self.write_message(ConnectResponse.success(*sock.getsockname()),
				info["mate"], info["mate_info"])
		except ConnectionRefusedError:
			self.final_message(ConnectResponse.error(SOCKS5_REPLY_CONNECTION_REFUSED),
				info["mate"], info["mate_info"])
		else:
			self.begin_forward(sock, info)

	@message(HandshakeRequest)
	def read_wait_handshake(self, request, sock, info):
		if self.groups is None:
			info["handlers.read"] = self.read_wait_connect
			self.write_message(HandshakeResponse.no_authentication_required(), sock, info)
		else:
			if request.client_supports_username_password():
				info["handlers.read"] = self.read_wait_authentication
				self.write_message(HandshakeResponse.require_username_password(), sock, info)
			else:
				self.final_message(HandshakeResponse.no_acceptable_methods(), sock, info)

	@message(AuthenticationRequest)
	def read_wait_authentication(self, request, sock, info):
		if self.groups.validate_user(request.username, request.password):
			info["handlers.read"] = self.read_wait_connect
			self.write_message(AuthenticationResponse.success(), sock, info)
		else:
			self.final_message(AuthenticationResponse.fail(), sock, info)

	@message(ConnectRequest)
	def read_wait_connect(self, request, sock, info):
		error, response = self.process_connect(request)
		if error is True:
			self.final_message(response, sock, info)
		else:
			try:
				psock, pinfo = self.get_upstream(ConnectRequest).open_connection(
					info.server, request.host, request.port)
			except ForbiddenHostError as e:
				info.server.logger.info(f"Requested forbidden host: {e}.")
				self.final_message(
					ConnectResponse.error(SOCKS5_REPLY_NOT_ALLOWED), sock, info)
			except GAIError:
				self.final_message(
					ConnectResponse.error(SOCKS5_REPLY_HOST_UNREACHABLE), sock, info)
			except (BindDeviceError, BindIPError):
				self.final_message(
					ConnectResponse.error(SOCKS5_REPLY_NETWORK_UNREACHABLE), sock, info)
			except UpStreamError:
				self.final_message(
					ConnectResponse.error(SOCKS5_REPLY_GENERIC_ERROR), sock, info)
			else:
				self.mate(sock, info, psock, pinfo)
				info.server.looper.register_for_write(psock, pinfo)

	def process_connect(self, request: ConnectRequest) -> Tuple[bool, ConnectResponse]:
		self.logger.info("CONNECT {}:{}".format(request.host, request.port))
		# TODO: apply rules
		return False, None
