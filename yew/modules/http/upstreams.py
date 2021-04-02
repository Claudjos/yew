from yew.core.info import Info
from yew.modules.tcp import (
	ParentUpStream,
	UPSTREAM_ERROR_PARENT_UNREACHABLE,
	UPSTREAM_ERROR_PARENT_AUTHENTICATION,
	UPSTREAM_ERROR_GENERIC,
)
from yew.modules.base import message
from typing import Tuple
from .http import encode_basic_auth, HTTPResponse
from .servers import Proxy



class WebServer(ParentUpStream):
	pass


class ParentProxy(WebServer):

	def parse_config(self, config: dict):
		super().parse_config(config)
		if self.parent_usr is not None and self.parent_pwd is not None:
			self.parent_credentials = encode_basic_auth(self.parent_usr, self.parent_pwd)
		else:
			self.parent_credentials = None

	def create_info(self, server):
		i = Info(server)
		i["handlers.write"] = self.send_connect
		i["handlers.read"] = self.recv_connect
		return i

	def create_connect_message(self, host, port):
		return "CONNECT {}:{} HTTP/1.1\r\nhost: {}:{}\r\nproxy-authorization: {}\r\n\r\n".format(
				host,
				port,
				host,
				port,
				self.parent_credentials
			).encode()

	def send_connect(self, sock, info):
		info.server.looper.unregister_for_write(sock)
		try:
			sock.send(self.create_connect_message(*info["upstream.host_port"]))
			info.server.logger.debug("CONNECT sent to parent proxy")
		except ConnectionRefusedError:
			info.server.connect_fail(UPSTREAM_ERROR_PARENT_UNREACHABLE, sock, info)
		else:
			info.server.looper.register_for_read(sock, info)

	@message(HTTPResponse)
	def recv_connect(self, response, sock, info):
		error = self.recv_connect_handle(response)
		if error == 0:
			info.server.logger.debug("PP CONNECT success")
			info.server.connect_success(sock, info)
		else:
			info.server.logger.debug(f"PP CONNECT error {response.status}")
			info.server.connect_fail(error, sock, info)

	def recv_connect_handle(self, response) -> int:
		if response.status == 407:
			return UPSTREAM_ERROR_PARENT_AUTHENTICATION
		elif response.status != 200:
			return UPSTREAM_ERROR_GENERIC
		else:
			return 0
