import unittest
from yew.modules.tcp.servers import TCPServer
from yew.core.info import Info
from yew.core.looper import Looper
from yew.core.buffer import Buffer


class DummySock:

	def send(self, data: bytes) -> int:
		return 2

	def recv(self, length: int) -> bytes:
		return b'abcdef'


class DummySock2:

	def send(self, data: bytes) -> int:
		raise BlockingIOError()

	def recv(self, length: int) -> bytes:
		raise BlockingIOError()


class DummyLooper(Looper):

	def run(self):
		pass

	def register_for(self, sock, value, data):
		pass

	def unregister_for(self, sock, value):
		pass

	def remove_sock(self, sock, info = None):
		pass


class DummyServer:

	def set_looper(self, looper: Looper):
		self.looper = looper


class TCPServerTestCases(unittest.TestCase):

	def test_write_tcp_forward_incomplete_send(self):
		# Initialize stubs
		srv = DummyServer()
		srv.set_looper(DummyLooper())
		info = Info(srv)
		info["remaining"] = b"abcdef"
		info["mate"] = info["mate_info"] = None
		sock = DummySock()
		# Tests - 2 bytes per call are sent
		TCPServer.write_tcp_forward(None, sock, info)
		assert len(info["remaining"]) == 4
		assert info["remaining"] == b"cdef"
		# Tests - 2 bytes per call are sent
		TCPServer.write_tcp_forward(None, sock, info)
		assert len(info["remaining"]) == 2
		assert info["remaining"] == b"ef"
		# Writes the last 2 bytes of info["remaining"]
		TCPServer.write_tcp_forward(None, sock, info)

	def test_write_tcp_forward_BlockingIOError(self):
		# Initialize stubs
		srv = DummyServer()
		srv.set_looper(DummyLooper())
		info = Info(srv)
		info["remaining"] = b"abcdef"
		info["mate"] = info["mate_info"] = None
		sock = DummySock2()
		# Tests - all data read are in remaining
		TCPServer.write_tcp_forward(None, sock, info)
		assert len(info["remaining"]) == 6
		assert info["remaining"] == b"abcdef"

	def test_read_tcp_forward(self):
		# Initialize stubs
		srv = DummyServer()
		srv.set_looper(DummyLooper())
		info = Info(srv)
		info["mate"] = DummySock()
		info["mate_info"] = Info(srv)
		sock = DummySock()
		# Tests - checks remaining data
		TCPServer.read_tcp_forward(None, sock, info)
		assert len(info["mate_info"]["remaining"]) == 4
		assert info["mate_info"]["remaining"] == b"cdef"

	def test_read_tcp_forward_BlockingIOError(self):
		# Initialize stubs
		srv = DummyServer()
		srv.set_looper(DummyLooper())
		info = Info(srv)
		info["mate"] = DummySock2()
		info["mate_info"] = Info(srv)
		sock = DummySock()
		# Tests - checks remaining data
		TCPServer.read_tcp_forward(None, sock, info)
		assert len(info["mate_info"]["remaining"]) == 6
		assert info["mate_info"]["remaining"] == b"abcdef"
