from .buffer import Buffer


class Info:

	def __init__(self, server):
		self.data = {}
		self["server"] = server
		self["input"] = Buffer()
		self["output"] = Buffer()

	def __getitem__(self, item):
		return self.data[item]

	def __setitem__(self, item, value):
		self.data[item] = value

	@property
	def server(self):
		return self["server"]
	
	@property
	def input(self):
		return self["input"]

	@property
	def output(self):
		return self["output"]
