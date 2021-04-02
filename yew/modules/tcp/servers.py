from yew.modules.base import Server
from yew.core.info import Info
from yew.core.buffer import EndOfBuffer
from yew.core.looper import EndOfStream
from typing import Tuple
import socket


class TCPServer(Server):
	"""
	Generic TCP server
	"""

	def create_server_socket(self) -> Tuple[socket.socket, Info]:
		"""
		Create a server socket for this server.
		"""
		bind_ip = self.binding.get("ip", "::")
		
		l = socket.getaddrinfo(bind_ip, None)
		family = False
		for i in l:
			if i[1] == socket.SocketKind.SOCK_STREAM:
				family = i[0]
				bind = i[4]

		if family is None:
			self.logger.error("init {} does not support SOCK_STREAM".format(str(bind_ip)))

		if len(bind) > 2:
			# ipv4 tupla
			bind = (bind[0], self.binding.get("port"), bind[1], bind[2])
		else:
			bind = (bind[0], self.binding.get("port"))

		server_socket = socket.socket(family, socket.SOCK_STREAM)
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind(bind)
		server_socket.setblocking(0)
		server_socket.listen(5)
		info = Info(self)
		info["handlers.read"] = self.accepted
		return (server_socket, info)

	def accepted(self, sock, info):
		"""
		Accept a client
		"""
		(csock, caddr) = sock.accept()
		cinfo = self.get_new_client_info()
		if self.can_accept_ip(caddr[0]):
			csock.setblocking(0)
			self.looper.register_for_read(csock, cinfo)
			self.logger.debug("Client accepted {}:{}".format(caddr[0], caddr[1]))
		else:
			self.logger.info("Client refused {}:{}".format(caddr[0], caddr[1]))
			self.remove_sock(csock, cinfo)

	def connect_success(self, sock, info):
		"""
		Called by upstream.
		"""
		raise NotImplementedError()

	def connect_fail(self, error: int, sock, info):
		"""
		Called by upstream.
		"""
		raise NotImplementedError()

	def get_new_client_info(self) -> int:
		"""
		RETURNS
			the info for a newly accepted client
		"""
		return Info(self)
	
	def read_input(self, sock, info):
		"""
		Read available data to the input buffer
		"""
		data = sock.recv(65536)
		if data == b'':
			raise EndOfStream()
		else:
			info.input.merge(data)

	def write_output(self, data, sock, info):
		"""
		CAUTION: not handling incomplete transmissions here !!!
		"""
		sock.send(data)

	def write_error(self, data, sock, info):
		"""
		CAUTION: not handling incomplete transmissions here !!!
		"""
		sock.send(data)
		self.remove_sock(sock, info)

	def write_message(self, message, sock, info):
		self.write_output(message.to_bytes(), sock, info)

	def final_message(self, message, sock, info):
		self.write_error(message.to_bytes(), sock, info)

	def buffer_reader(f):
		def wrapper(sock, info):
			try:
				info.input.mark();
				info.server.read_input(sock, info)
				f(sock, info)
				info.input.clear();
			except EndOfBuffer as e:
				info.input.restore()
		return wrapper

	def write_tcp_forward(self, sock, info):
		# this can be improved a lot by not clearing and merging the data every time
		t = info.output.getRemaining()
		datalen = len(t)
		info.output.clear()
		try:
			datasent = sock.send(t)
			if datasent < datalen:
				info.output.merge(t[datasent:])
			else:
				info.server.looper.unregister_for_write(sock)
				info.server.looper.register_for_read(info["mate"], info["mate_info"])
		except BlockingIOError:
			info.output.merge(t)

	def read_tcp_forward(self, sock, info):
		t = sock.recv(65535)
		if t == b'':
			raise EndOfStream()
		datalen = len(t)
		try:
			datasent = info["mate"].send(t)
			if datasent < datalen:
				info["mate_info"].output.merge(t[datasent:])
				info.server.looper.unregister_for_read(sock)
				info.server.looper.register_for_write(info["mate"], info["mate_info"])
		except BlockingIOError:
			info["mate_info"].output.merge(t)
			info.server.looper.unregister_for_read(sock)
			info.server.looper.register_for_write(info["mate"], info["mate_info"])

	def begin_forward(self, sock, info):
		
		info["handlers.read"] = self.read_tcp_forward
		info["handlers.write"] = self.write_tcp_forward
		info["mate_info"]["handlers.read"] = self.read_tcp_forward
		info["mate_info"]["handlers.write"] = self.write_tcp_forward

		self.looper.register_for_read(sock, info)
		self.looper.register_for_read(info["mate"], info["mate_info"])

	def mate(self, a_sock, a_info, b_sock, b_info):
		a_info["mate"] = b_sock
		a_info["mate_info"] = b_info
		b_info["mate"] = a_sock
		b_info["mate_info"] = a_info

	def remove_sock(self, sock, info):
		super().remove_sock(sock, info)
		if "mate" in info.data and info["mate"] is not None:
			super().remove_sock(info["mate"], info["mate_info"])
