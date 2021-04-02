from yew.core.components import Component


class Group(Component):

	def parse_config(self, config: dict):
		"""
		Reads configuration. Here a YAML example:

		users:
			- username: usr
			  password: pwd
		"""
		super().parse_config(config)
		self.map = {}
		for item in config.get("users", []):
			self.map[item.get("username")] = item.get("password")

	def validate_user(self, username: str, password: str) -> bool:
		if username in self.map:
			if self.map[username] == password:
				return True
		return False
