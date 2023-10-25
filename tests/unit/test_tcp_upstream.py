import unittest
from yew.modules.tcp.upstreams import (
	TCPUpStream, ParentUpStream, ForbiddenHostError,
	BindDeviceError, BindIPError, GAIError
)


class TCPUpStreamTestCase(unittest.TestCase):

	def test_filtering_allow(self):
		upstream = TCPUpStream("test", {"allow": ["abc.com", "^def.net"]})
		self.assertTrue(upstream.can_connect_host("www.abc.com"))
		self.assertTrue(upstream.can_connect_host("def.net"))
		self.assertFalse(upstream.can_connect_host("www.def.net"))
		self.assertFalse(upstream.can_connect_host("www.google.com"))

	def test_filtering_disallow(self):
		upstream = TCPUpStream("test", {"disallow": ["abc.com", "^def.net"]})
		self.assertFalse(upstream.can_connect_host("www.abc.com"))
		self.assertFalse(upstream.can_connect_host("def.net"))
		self.assertTrue(upstream.can_connect_host("www.def.net"))
		self.assertTrue(upstream.can_connect_host("www.google.com"))

	def test_filtering_cannot_use_both(self):
		with self.assertRaises(ValueError):
			TCPUpStream("test", {"disallow": ["abc.com"], "allow": ["^def.net"]})

	def test_TCPUpStream_open_connection_forbidden(self):
		upstream = TCPUpStream("test", {"disallow": ["abc.com", "^def.net"]})
		with self.assertRaises(ForbiddenHostError):
			upstream.open_connection(None, "abc.com", 443)

	def test_ParentUpStream_open_connection_forbidden(self):
		upstream = ParentUpStream("test", {"disallow": ["abc.com", "^def.net"]})
		with self.assertRaises(ForbiddenHostError):
			upstream.open_connection(None, "abc.com", 443)

	def test_create_socket_bind_device_fails(self):
		upstream = ParentUpStream("test", {})
		with self.assertRaises(BindDeviceError):
			upstream.create_socket(None, "abc.com", 443, bind_device="not_existing_device")

	def test_create_socket_bind_ip_fails(self):
		upstream = ParentUpStream("test", {})
		with self.assertRaises(BindIPError):
			upstream.create_socket(None, "abc.com", 443, bind_ip="200.0.0.0")

	def test_create_socket_gai_error(self):
		upstream = ParentUpStream("test", {})
		with self.assertRaises(GAIError):
			upstream.create_socket(None, "not-existing.www", 443)
