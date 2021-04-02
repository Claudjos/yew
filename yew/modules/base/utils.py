from yew.core.buffer import Buffer, EndOfBuffer


def buffered(f):
	def wrapper(self, sock, info):
		try:
			info.input.mark();
			info.server.read_input(sock, info)
			f(self, sock, info)
			info.input.clear();
		except EndOfBuffer as e:
			info.input.restore()
	return wrapper


def message(MessageType):
	def wrap(f):
		@buffered
		def wrapper(self, sock, info):
			f(self, MessageType.from_buffer(info.input), sock, info)
		return wrapper
	return wrap


def message_out(f):
	def wrapper(self, sock, info):
		info.server.write_message(f(self, sock, info), sock, info)
	return wrapper
