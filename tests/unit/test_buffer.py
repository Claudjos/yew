import unittest
from yew.core.buffer import Buffer, EndOfBuffer


class BufferTestCases(unittest.TestCase):

	def test_buffer_clear(self):
		buf = Buffer(b'abcdefghijklmnopqrstuvwxyz')
		buf.clear()
		assert len(buf) == 0

	def test_buffer_mark_restore(self):
		"""Checks that Buffer.mark() and Buffer.restore() work as intended."""
		buf = Buffer(b'abcdefghijklmnopqrstuvwxyz')
		buf.read(10)
		buf.mark()
		assert buf.read(1) == "k"
		buf.read(5)
		buf.restore()
		assert buf.read(1) == "k"

	def test_buffer_get_remaining(self):
		buf = Buffer(b'abcdefghijklmnopqrstuvwxyz')
		assert buf.getRemaining() == b'abcdefghijklmnopqrstuvwxyz'
		with self.assertRaises(EndOfBuffer):
			buf.read()
