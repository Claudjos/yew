from yew.core.components import Component
from yew.core.info import Info
import socket


class UpStream(Component):

	def open_connection(self, server, host: str, port: int, info: Info) -> tuple[socket.socket, Info]:
		raise NotImplementedError()

	def create_info(self, server):
		raise NotImplementedError()


class UpStreamError(Exception):
	pass
