from yew.core.components import Component
import re


class Rule:

	def __init__(self, match: dict, upstream, rewrite: dict = None):
		uri = match.get("uri", None)
		host = match.get("host", None)
		if uri is not None:
			self.regex_uri = re.compile(uri)
		else:
			self.regex_uri = None
		if host is not None:
			self.regex_host = re.compile(host)
		else:
			self.regex_host = None
		self.upstream = Component.get("upstreams", upstream)
		if rewrite is not None:
			self.regex_group_uri = re.compile(rewrite.get("regex"))
			self.format_uri = rewrite.get("format")
		else:
			self.format_uri = None

	def match(self, request):
		if self.regex_host is not None and self.regex_host.match(request.host) is None:
			return False
		elif self.regex_uri is not None and self.regex_uri.match(request.uri) is None:
			return False
		else:
			return True

	def rewrite(self, request):
		if self.format_uri is not None:
			uri = self.format_uri.format(*self.regex_group_uri.match(request.uri).groups())
			request.uri = uri


class Rules(Component):

	def parse_config(self, config: dict):
		"""
		Reads configuration. Here a YAML example:

		rules:
			- match:
				host: localhost
				uri: /api
			  upstream: MyUpStream
		"""
		super().parse_config(config)
		self.rules = []
		for item in config.get("rules", []):
			self.rules.append(Rule(**item))

	def get_upstream(self, request, default):
		for rule in self.rules:
			if rule.match(request):
				rule.rewrite(request)
				return rule.upstream
		return default
