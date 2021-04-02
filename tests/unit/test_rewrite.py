import unittest
from ddt import ddt, data, unpack

from yew.modules.http.http import HTTPRequest
from yew.core.buffer import Buffer
from yew.core.components import Component

from tests import load_file
servers = load_file("examples/configuration/rewrite.yaml")


@ddt
class RewriteTestCases(unittest.TestCase):
	
	@data(
		["ReverseProxy", "SiteA", 
			"GET / HTTP/1.1\r\nHost: www.site-a.com\r\n\r\n"],
		["ReverseProxy", "SiteB", 
			"GET / HTTP/1.1\r\nHost: www.site-b.com\r\n\r\n"],
		["ReverseProxy", "ReverseDefault", 
			"GET / HTTP/1.1\r\nHost: www.foo-bar.com\r\n\r\n"],
	)
	@unpack
	def test_upstream_selection(self, server_name, upstream_name, request):
		request = HTTPRequest.from_buffer(Buffer(request.encode()))
		assert servers[server_name].get_upstream(request) == Component.get(
			"upstreams", upstream_name)

	@data(
		["APIGateway", "/v1/shop/1/products", 
			"GET /api/shop/1/products?foo=bar HTTP/1.1\r\nHost: www.fancy-service.com\r\n\r\n"
		],
		["APIGateway", "/v2/admin/login", 
			"GET /api/admin/login?foo=bar HTTP/1.1\r\nHost: www.fancy-service.com\r\n\r\n"
		],
	)
	@unpack
	def test_uri_rewrite(self, server_name, uri, request):
		request = HTTPRequest.from_buffer(Buffer(request.encode()))
		servers[server_name].get_upstream(request)
		assert request.uri == uri
