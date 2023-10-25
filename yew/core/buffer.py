from io import BytesIO


class EndOfBuffer(BaseException):
	pass


class Buffer:

	def __init__(self, data: bytes = b'', index: int = 0):
		self.data = BytesIO(data)
		self.len = len(data)
		self._mark = 0

	def mark(self):
		self._mark = self.data.tell()

	def restore(self):
		self.data.seek(self._mark)

	def clear(self):
		self.data = BytesIO()
		self._mark = 0
		self.len = 0

	def readUByte(self) -> int:
		return int.from_bytes(self.bread(1), byteorder = "big");

	def readUShort(self) -> int:
		return int.from_bytes(self.bread(2), byteorder = "big");

	def readUInt(self) -> int:
		return int.from_bytes(self.bread(4), byteorder = "big");

	def read(self, n: int = 1) -> str:
		if n==0:
			return ""
		elif n>1:
			return self.bread(n).decode()
		else:
			return chr(self.readUByte())

	def bread(self, n: int = 1) -> bytes:
		t = self.data.read(n)
		if t == b'':
			raise EndOfBuffer()
		return t

	def readLine(self) -> str:
		res = b = self.read()
		while b!= '\n':
			b = self.read()
			res += b
		return res

	def getRemaining(self) -> bytes:
		return self.data.read()

	def rewind(self):
		self.data.seek(0)

	def merge(self, newdata: bytes):
		self.mark()
		self.data.seek(self.len)
		self.data.write(newdata)
		self.restore()
		self.len += len(newdata)

	def __str__(self) -> str:
		return "none"

	def __len__ (self) -> int:
		return self.len - self.data.tell()
