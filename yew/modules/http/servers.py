from .http import *
from .rules import Rules
from yew.modules.tcp import TCPServer
from yew.modules.base import UpStreamError, message
from yew.modules.tcp.upstreams import ForbiddenHostError
from yew.core.components import Component
from yew.core.info import Info


# Messages
HTTP_CONNECTION_ESTABLISHED = b'HTTP/1.1 200 Connection Established\r\n\r\n'
HTTP_REFUSE_CREDENTIALS = b'HTTP/1.1 407 Proxy Authorization Required\r\ncontent-length: 0\r\n\r\n'
HTTP_FORBIDDEN_HOST = b'HTTP/1.1 403 Forbidden\r\ncontent-length: 0\r\n\r\n'
HTTP_BAD_GATEWAY = b'HTTP/1.1 502 Bad Gateway\r\ncontent-length: 0\r\n\r\n'
HTTP_SERVICE_UNAVAILABLE = b'HTTP/1.1 503 Service Unavailable\r\ncontent-length: 0\r\n\r\n'


class Proxy(TCPServer):

	def get_new_client_info(self):
		i = Info(self)
		i["handlers.read"] = self.read_wait_request
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

	def get_upstream(self, request):
		return self.rules.get_upstream(request, self._upstream)

	def connect_success(self, sock, info):
		"""
		BUGS:
			- ConnectionRefusedError is not handled for tunnel
		"""
		self.looper.unregister_for_write(sock)
		request = info["mate_info"]["request"]

		if request.isConnect():
			self.write_output(HTTP_CONNECTION_ESTABLISHED, info["mate"], info["mate_info"])
			self.begin_forward(sock, info)
		else:
			info["handlers.read"] = self.read_tcp_forward
			info["handlers.write"] = self.write_tcp_forward
			info["mate_info"]["handlers.read"] = self.read_wait_request
			self.write_output(request.to_bytes(), sock, info)
		
		self.looper.register_for_read(sock, info)
		self.looper.register_for_read(info["mate"], info["mate_info"])

	def connect_fail(self, error, sock, info):
		"""
		Called by the upstream when socket/tunnel creation fails.
		TODO:
			- send something more specific to client
		"""
		self.logger.error(error)
		self.write_output(HTTP_SERVICE_UNAVAILABLE, sock, info)

	def handle_authentication(self, request):
		if self.groups is not None:
			return self.groups.validate_user(
				*decode_basic_auth(request.headers.get("proxy-authorization", ""))
			)
		else:
			return True

	@message(HTTPRequest)
	def read_wait_request(self, request, sock, info):
		info["request"] = request
		if self.handle_authentication(request):
			try:
				info.server.logger.info(str(request))
				psock, pinfo = info.server.get_upstream(request).open_connection(
					info.server, *request.getHostPort())
			except ForbiddenHostError:
				self.write_output(HTTP_FORBIDDEN_HOST, sock, info)
				info.server.logger.info("requested forbidden host.")
			except UpStreamError:
				self.write_output(HTTP_BAD_GATEWAY, sock, info)
				info.server.logger.exception("upstreamerror")
			else:
				self.mate(sock, info, psock, pinfo)
				info.server.looper.register_for_write(psock, pinfo)
		else:
			self.write_output(HTTP_REFUSE_CREDENTIALS, sock, info)
