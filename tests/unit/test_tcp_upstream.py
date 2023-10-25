import unittest
from yew.modules.tcp.upstreams import TCPUpStream, ParentUpStream, ForbiddenHostError


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
