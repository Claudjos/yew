from yew.core.buffer import Buffer
from typing import List
from ipaddress import IPv4Address, IPv6Address, ip_address


SOCKS5_VERSION = 0x05

SOCKS5_COMMAND_CONNECT = 0x01

SOCKS5_AUTH_VERSION = 0x01
SOCKS5_AUTH_OK = 0x00
SOCKS5_AUTH_KO = 0x01

SOCKS5_AUTH_NONE = 0x00
SOCKS5_AUTH_USER_PWD = 0x02
SOCKS5_AUTH_NO_ACCEPTABLE_METHODS = 0xFF

SOCKS5_ADDRESS_IPV4 = 0x01
SOCKS5_ADDRESS_DOMAIN_NAME =  0x03
SOCKS5_ADDRESS_IPV6 = 0x04

SOCKS5_RESERVED = 0x00

SOCKS5_REPLY_SUCCESS = 0x00
SOCKS5_REPLY_GENERIC_ERROR = 0x01
SOCKS5_REPLY_NOT_ALLOWED = 0x02
SOCKS5_REPLY_NETWORK_UNREACHABLE = 0x03
SOCKS5_REPLY_HOST_UNREACHABLE = 0x04
SOCKS5_REPLY_CONNECTION_REFUSED = 0x05
SOCKS5_REPLY_TTL_EXPIRED = 0x06
SOCKS5_REPLY_UNSUPPORTED_COMMAND = 0x07
SOCKS5_REPLY_UNSUPPORTED_ADDR_TYPE = 0x08


class Socks5ParsingError(Exception):
	pass


class UnsupportedVersion(Socks5ParsingError):
	pass


class UnsupportedAddressType(Socks5ParsingError):
	pass


class UnsupportedAuthenticationVersion(Socks5ParsingError):
	pass


class UnsupportedCommand(Socks5ParsingError):
	pass


class HandshakeRequest:

	def __init__(self, methods: List[int]):
		self.methods = methods

	def to_bytes(self):
		return bytes([SOCKS5_VERSION, len(self.methods)]) + bytes(self.methods)

	@classmethod
	def from_buffer(cls, buf):
		version = buf.readUByte()
		if version != SOCKS5_VERSION:
			raise UnsupportedVersion("{}".format(version))
		nmethods = buf.readUByte()
		return cls([buf.readUByte() for _ in range(0, nmethods)])

	def client_supports_username_password(self):
		return SOCKS5_AUTH_USER_PWD in self.methods

	@classmethod
	def build(cls):
		return cls([SOCKS5_AUTH_NONE, SOCKS5_AUTH_USER_PWD])


class HandshakeResponse:

	def __init__(self, version, method):
		self.version = version
		self.method = method

	def to_bytes(self):
		return bytes([self.version, self.method])

	@classmethod
	def from_buffer(cls, buf):
		version = buf.readUByte()
		if version != SOCKS5_VERSION:
			raise UnsupportedVersion("{}".format(version))
		method = buf.readUByte()
		return cls(version, method)

	def requires_username_password(self):
		return self.method == SOCKS5_AUTH_USER_PWD

	def requires_no_authentication(self):
		return self.method == SOCKS5_AUTH_NONE

	@classmethod
	def no_acceptable_methods(cls):
		return HandshakeResponse(SOCKS5_VERSION, SOCKS5_AUTH_NO_ACCEPTABLE_METHODS)

	@classmethod
	def no_authentication_required(cls):
		return HandshakeResponse(SOCKS5_VERSION, SOCKS5_AUTH_NONE)

	@classmethod
	def require_username_password(cls):
		return HandshakeResponse(SOCKS5_VERSION, SOCKS5_AUTH_USER_PWD)


class AuthenticationRequest:

	def __init__(self, user: str, pwd: str):
		self.username = user
		self.password = pwd

	def to_bytes(self):
		ulen = len(self.username)
		plen = len(self.password)
		return bytes([SOCKS5_AUTH_VERSION, ulen]
			) + self.username.encode() + bytes([plen]) + self.password.encode()

	@classmethod
	def from_buffer(cls, buf):
		version = buf.readUByte()
		if version != SOCKS5_AUTH_VERSION:
			raise UnsupportedAuthenticationVersion("unsupported authentication version {}".format(version))
		ulen = buf.readUByte()
		user = buf.read(ulen)
		plen = buf.readUByte()
		pwd = buf.read(plen)
		return cls(user, pwd)

	@classmethod
	def build(cls, usr, pwd):
		return cls(usr, pwd)


class AuthenticationResponse:
	
	def __init__(self, version: int, code: int):
		self.version = version
		self.code = code

	@classmethod
	def from_buffer(cls, buf):
		version = buf.readUByte()
		if version != SOCKS5_AUTH_VERSION:
			raise UnsupportedAuthenticationVersion("{}".format(version))
		code = buf.readUByte()
		return cls(version, code)

	@classmethod
	def success(cls):
		return cls(SOCKS5_AUTH_VERSION, SOCKS5_AUTH_OK)

	@classmethod
	def fail(cls):
		return cls(SOCKS5_AUTH_VERSION, SOCKS5_AUTH_KO)

	def to_bytes(self):
		return bytes([self.version, self.code])

	def is_success(self):
		return self.code == SOCKS5_AUTH_OK


class ConnectBase:
	
	def __init__(self, cmd_rep: int, host: str, port: int):
		self.host = host
		self.port = port
		self.cmd_rep = cmd_rep

	def to_bytes(self):
		if isinstance(self.host, str):
			addr = bytes([len(self.host)]) + self.host.encode()
			atype = SOCKS5_ADDRESS_DOMAIN_NAME
		elif isinstance(self.host, IPv4Address):
			addr = self.host.packed
			atype = SOCKS5_ADDRESS_IPV4
		elif isinstance(self.host, IPv6Address):
			addr = self.host.packed
			atype = SOCKS5_ADDRESS_IPV6
		else:
			TypeError("Host must be of type str, IPv4Address or IPv6Address.")

		return bytes([
			SOCKS5_VERSION,
			self.cmd_rep,
			SOCKS5_RESERVED,
			atype
		]) + addr + self.port.to_bytes(2, byteorder="big")

	@classmethod
	def from_buffer(cls, buf):

		version = buf.readUByte()
		if version != SOCKS5_VERSION:
			UnsupportedVersion(f"{version}")

		cmd_rep = buf.readUByte()
		reserved = buf.readUByte()

		addr_type = buf.readUByte()

		if addr_type == SOCKS5_ADDRESS_IPV4:
			host = str(IPv4Address(buf.bread(4)))
		elif addr_type == SOCKS5_ADDRESS_DOMAIN_NAME:
			alen = buf.readUByte()
			host = buf.read(alen)
		elif addr_type == SOCKS5_ADDRESS_IPV6:
			host = str(IPv6Address(buf.bread(16)))
		else:
			UnsupportedAddressType(f"{addr_type}")

		port = buf.readUShort()

		return cls(cmd_rep, host, port)

	@classmethod
	def build(cls, cmd_rep: int, host: str, port: int):
		return cls(cmd_rep, host, port)


class ConnectRequest(ConnectBase):
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.cmd_rep != SOCKS5_COMMAND_CONNECT:
			UnsupportedCommand(f"{self.cmd_rep}")

	@classmethod
	def build(cls, host: str, port: int):
		return cls(SOCKS5_COMMAND_CONNECT, host, port)


class ConnectResponse(ConnectBase):

	@classmethod
	def error(cls, code: int):
		return cls(code, ip_address("0.0.0.0"), 0)

	@classmethod
	def success(cls, ip: str, port: int):
		return cls(SOCKS5_REPLY_SUCCESS, ip_address(ip), port)

	def is_success(self):
		return self.cmd_rep == SOCKS5_REPLY_SUCCESS
