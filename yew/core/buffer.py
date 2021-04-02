from io import BytesIO


class EndOfBuffer(BaseException):
	pass


class Buffer:

	def __init__ ( self, data=b'', index=0 ):
		self.data = BytesIO(data)
		self.len = len(data)
		self._mark = 0

	def mark(self):
		self._mark = self.data.tell()

	def restore(self):
		self.data.seek(self._mark)

	def clear ( self ):
		self.data = BytesIO()
		self._mark = 0
		self.len = 0

	def readUByte(self):
		return int.from_bytes(self.bread(1), byteorder="big");

	def readUShort(self):
		return int.from_bytes(self.bread(2), byteorder="big");

	def readUInt(self):
		return int.from_bytes(self.bread(4), byteorder="big");

	def read(self, n=1):
		if n==0:
			return ""
		elif n>1:
			return self.bread(n).decode()
		else:
			return chr(self.readUByte())

	def bread(self, n=1):
		t = self.data.read(n)
		if t == b'':
			raise EndOfBuffer()
		return t

	def readLine ( self ):
		res = b = self.read()
		while b!= '\n':
			b = self.read()
			res += b
		return res

	def getRemaining(self):
		return self.data.read()

	def rewind(self):
		self.data.seek(0)

	def merge(self, newdata: bytes):
		self.mark()
		self.data.seek(self.len)
		self.data.write(newdata)
		self.restore()
		self.len += len(newdata)

	def __str__(self):
		return "none"

	def __len__ (self):
		return self.len - self.data.tell()
