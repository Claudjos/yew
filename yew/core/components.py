import logging


class Component:

	_MAP = {}

	@classmethod
	def build(cls, name, config: dict):
		return cls(name, config)

	def __init__(self, name: str, config: dict):
		self.name = name
		self.logger = self.create_logger()
		self.parse_config(config)

	def parse_config(self, config: dict):
		pass

	def create_logger(self):
		"""
		Returns a logger for this instance
		"""
		return logging.getLogger(self.name)

	@staticmethod
	def install(category: str, component: "Component"):
		if category not in Component._MAP:
			Component._MAP[category] = {}
		Component._MAP[category][component.name] = component

	@staticmethod
	def get(category: str, name: str) -> "Component":
		return Component._MAP[category][name]

	@staticmethod
	def get_by_category(category: str) -> "List[Component]":
		return [value for key, value in Component._MAP[category].items()]
