import selectors


class EndOfStream(BaseException):
	pass


class Looper:

	def __init__(self):
		self.sel = selectors.DefaultSelector()

	def run(self):
		while True:
			events = self.sel.select()
			for key, mask in events:
				sock = key.fileobj
				info = key.data
				try:
					if mask & selectors.EVENT_READ == selectors.EVENT_READ:
						info.data.get("handlers.read")(sock, info)
					if mask & selectors.EVENT_WRITE == selectors.EVENT_WRITE:
						info.data.get("handlers.write")(sock, info)
				except (EndOfStream, ConnectionResetError, OSError) as e:
					if info is not None:
						info.server.on_connection_failure(sock, info, e)
					else:
						self.remove_sock(sock)
				except BaseException as e:
					if info is not None:
						info.server.on_handler_error(sock, info, e)
					else:
						self.remove_sock(sock)

	def remove_sock (self, sock, info=None):
		try:
			self.unregister_for_read(sock)
		except (ValueError, KeyError):
			pass
		try:
			self.unregister_for_write(sock)
		except (ValueError, KeyError):
			pass
		sock.close()

	def register_for_read ( self, sock, data):
		self.register_for(sock, selectors.EVENT_READ, data)

	def register_for_write ( self, sock, data):
		self.register_for(sock, selectors.EVENT_WRITE, data)

	def register_for ( self, sock, value, data):
		"""
		NOTE
			- not handling value error for invalid fileobject or fileno<0
		"""
		try:
			key = self.sel.get_key(sock)
			self.sel.unregister(sock)
			events = key.events
		except KeyError:
			events = 0

		self.sel.register(sock, events | value, data)

	def unregister_for_read ( self, sock ):
		self.unregister_for(sock,selectors.EVENT_READ)

	def unregister_for_write ( self, sock ):
		self.unregister_for(sock,selectors.EVENT_WRITE)

	def unregister_for(self, sock, value):
		key = self.sel.get_key(sock)
		self.sel.unregister(sock)
		events = key.events
		events = events & ~ value
		if events != 0:
			self.sel.register(sock, events, key.data)
