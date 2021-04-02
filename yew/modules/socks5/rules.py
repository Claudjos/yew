from yew.core.components import Component
import re


class Rule:

	def __init__(self, match: dict, upstream):
		host = match.get("host", None)
		if host is not None:
			self.regex_host = re.compile(host)
		else:
			self.regex_host = None
		self.upstream = Component.get("upstreams", upstream)

	def match(self, request):
		if self.regex_host is not None and self.regex_host.match(request.host) is None:
			return False
		else:
			return True


class Rules(Component):

	def parse_config(self, config: dict):
		"""
		Reads configuration. Here a YAML example:

		rules:
			- match:
				host: localhost
			  upstream: MyUpStream
		"""
		super().parse_config(config)
		self.rules = []
		for item in config.get("rules", []):
			self.rules.append(Rule(**item))

	def get_upstream(self, request, default):
		for rule in self.rules:
			if rule.match(request):
				return rule.upstream
		return default
