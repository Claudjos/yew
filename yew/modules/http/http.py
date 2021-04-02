from yew.core.buffer import Buffer
from urllib import parse


class MalformedHTTPPacket(BaseException):
	pass


class HTTPPacket:

	@classmethod
	def from_buffer(cls, buf):
		return cls(buf)

	def to_bytes(self):
		return self.get()

	def __init__(self,buf=None):
		self.body = b''
		self.headers = {}
		self.buf = buf
		if self.buf != None:
			self.read()

	def get(self):

		self.make()
		packet = self.make_first()

		for key in self.headers:

			if not key.startswith("proxy"):
				packet+= key+": "+self.headers[key]+"\r\n"

		packet+="\r\n"
		packet = packet.encode()
		packet+=self.body

		return packet

	def make(self):
		self.headers["content-length"] = str(len(self.body))

	def read(self):
		self.parse_headers()
		self.parse_body()
		
	def parse_first(self):
		self.first_line = self.first = self.buf.readLine()

	def make_first(self):
		return self.first_line

	def parse_headers(self):

		try:
			# reading request/status line
			self.parse_first()
			# parsing headers
			headers = {}
			line = self.buf.readLine()
			while line != "\r\n":
				temp = line.split(":", 1)
				headers[temp[0].lower()] = temp[1][1:-2]
				line = self.buf.readLine()

			self.headers = headers

		except IndexError as e:
			raise MalformedHTTPPacket()

	def getContent(self):
		return self.body

	def parse_body(self):

		# TODO - handling content-encoded chunked
		# though I found unsual that I client sends data with this encoding 
		# and since this proxy doesn't parse any response except the one for 
		# opening tunnel, it's not that important - also it could be a problem
		# just with plain http with http client

		if "content-length" in self.headers and int(self.headers["content-length"])>0:
			self.body = self.buf.bread(int(self.headers["content-length"]))
		else:
			self.body = b''

class HTTPResponse(HTTPPacket):

	def parse_first(self):

		super().parse_first()
	
		t = self.first.split(" ")
		self.protocol = t[0]
		self.status_code = self.statusCode = int(t[1])

		# Some servers don't send status message

		if len(t) > 2:
			self.status_msg = self.statusMsg = t[2]
		else:
			self.status_msg = self.statusMsg = ""

	def make_first(self):
		if not self.statusMsg.endswith("\r\n"):
			self.statusMsg += "\r\n"
		return self.protocol+" "+str(self.statusCode)+" "+self.statusMsg

	def get_status_code(self):
		return self.status_code

	def get_status_line(self):
		return self.first_line

	@property
	def status(self):
		return self.status_code
	

class HTTPRequest(HTTPPacket):

	def __str__(self) :
		return self.make_first()

	def make(self):
		if self.method.upper() != "GET":
			super().make()

	def make_first(self):
		q = self._parsed.query
		if q is not None:
			q = "?" + q
		return "{} {}{} {}".format(self.method, self.uri, q, self.protocol)

	def parse_first(self):
		super().parse_first()
		self.method, self.uri, self.protocol = self.first.split(" ")
		self._parsed = parse.urlparse(self.uri)
		self.uri = self._parsed.path
		self.params = parse.parse_qs(self._parsed.query)

	def isConnect(self):
		return self.method.upper() == "CONNECT"

	def getHostPort(self):
		if "host" not in self.headers:
			if self._parsed.hostname is not None:
				self.headers["host"] = self._parsed.hostname
			else:
				# This is for python requests
				self.headers["host"] = self._parsed.path
		if ":" in self.headers["host"]:
			tt = self.headers["host"].split(":")
			host = tt[0]
			port = int(tt[1])
		else:
			host = self.headers["host"]
			if self.isConnect():
				port = 443
			else:
				port = 80
		return (host, port)

	@property
	def host(self):
		return self.getHostPort()[0]
	



from base64 import b64encode, b64decode
from typing import Tuple


def encode_basic_auth(username: str, password: str) -> str:
	return "Basic "+b64encode((username+":"+password).encode()).decode()

def decode_basic_auth(authorization: str) -> Tuple[str, str]:
	if "Basic " in authorization:
		basic = authorization.split("Basic ")
	else:
		return None, None
	try:
		auth = b64decode(basic[1]).decode().split(":")
		return auth[0], auth[1]
	except:
		return None, None
