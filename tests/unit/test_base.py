import unittest
from ddt import ddt, data, unpack


from yew.core.components import Component
from tests import load_file
servers = load_file("examples/configuration/base.yaml")


@ddt
class BaseTestCases(unittest.TestCase):

	@data(
		["ProxyAccept", "::ffff:192.168.1.1", True],
		["ProxyAccept", "::ffff:127.0.0.0", True],
		["ProxyAccept", "::ffff:127.1.0.0", False],
		["ProxyRefuse", "::ffff:127.0.0.1", False],
		["ProxyRefuse", "::ffff:192.168.1.10", False],
		["ProxyRefuse", "::ffff:192.168.1.11", True],
	)
	@unpack
	def test_accept_filter(self, server_name, ip, result):
		assert servers[server_name].can_accept_ip(ip) is result

	@data(
		["Group1", "io", "pwd", True],
		["Group1", "foo", "bar", True],
		["Group1", "io", "bar", False],
	)
	@unpack
	def test_user_authentication(self, component_name, usr, pwd, result):
		assert Component.get("groups", component_name).validate_user(usr, pwd) is result

	@data(
		["WithAllow", "www.foobar.com", True],
		["WithAllow", "www.foobar.com.lol.tk", False],
		["WithAllow", "static22.com", True],
		["WithAllow", "static22.com.lol.tk", True],
		["WithAllow", "static2.com", False],
		["WithDisallow", "static-traffic-funky.net", False],
		["WithDisallow", "www.ads.com", False],
		["WithDisallow", "www.ads.net", True],
	)
	@unpack
	def test_host_filter(self, component_name, host, result):
		assert Component.get("upstreams", component_name).can_connect_host(host) is result
