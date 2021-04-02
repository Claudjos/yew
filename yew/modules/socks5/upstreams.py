from yew.modules.tcp import (
	ParentUpStream,
	UPSTREAM_ERROR_PARENT_UNREACHABLE,
	UPSTREAM_ERROR_PARENT_AUTHENTICATION,
	UPSTREAM_ERROR_GENERIC,
)
from yew.modules.base import message, message_out
from yew.core.info import Info
from typing import Tuple
from .socks5 import *


class ParentProxy(ParentUpStream):

	def parse_config(self, config: dict):
		super().parse_config(config)
		if self.parent_usr is not None and self.parent_pwd is not None:
			self.auth_request = AuthenticationRequest.build(
				self.parent_usr, self.parent_pwd
			)

	def create_info(self, server):
		i = Info(server)
		i["handlers.write"] = self.ready_for_write
		i["handlers.read"] = self.read_handshake_sent
		return i

	def ready_for_write(self, sock, info):
		info.server.looper.unregister_for_write(sock)
		try:
			info.server.write_output(
				HandshakeRequest.build().to_bytes(),
				sock, info
			)
			del info.data["handlers.write"]
			info.server.logger.debug("Handshake sent")
		except ConnectionRefusedError:
			self.logger.error("Unable to connect parent proxy")
			info.server.connect_fail(UPSTREAM_ERROR_PARENT_UNREACHABLE, sock, info)
		else:
			info.server.looper.register_for_read(sock, info)

	@message_out
	def send_auth(self, sock, info):
		info["handlers.read"] = self.read_authentication_sent
		return self.auth_request
		
	@message_out
	def send_connect(self, sock, info):
		info["handlers.read"] = self.read_connect_sent
		return ConnectRequest.build(*info["upstream.host_port"])

	@message(HandshakeResponse)
	def read_handshake_sent(self, response, sock, info):
		if response.requires_no_authentication():
			self.send_connect(sock, info)
		elif response.requires_username_password():
			self.send_auth(sock, info)
		else:
			self.logger.error("No authentication method available.")
			info.server.connect_fail(UPSTREAM_ERROR_PARENT_AUTHENTICATION, sock, info)

	@message(AuthenticationResponse)
	def read_authentication_sent(self, response, sock, info):
		if response.is_success():
			self.send_connect(sock, info)
		else:
			self.logger.error("Authentication failed.")
			info.server.connect_fail(UPSTREAM_ERROR_PARENT_AUTHENTICATION, sock, info)

	@message(ConnectResponse)
	def read_connect_sent(self, response, sock, info):
		if response.is_success():
			info.server.connect_success(sock, info)
		else:
			info.server.connect_fail(UPSTREAM_ERROR_GENERIC, sock, info)
