import unittest
from ddt import ddt, data, unpack

from yew.modules.http.http import HTTPRequest, HTTPResponse
from yew.core.buffer import Buffer
from yew.core.components import Component

from tests import load_file
servers = load_file("examples/configuration/parent.yaml")


@ddt
class ParentTestCases(unittest.TestCase):
	
	@data(
		["ParentProxy", 1,
			"HTTP/1.1 407 whatever\r\nServer: Fancy 1.0\r\n\r\n"
		],
		["ParentProxy", 4,
			"HTTP/1.1 502 whatever\r\nServer: Fancy 1.0\r\n\r\n"
		],
		["ParentProxy", 0,
			"HTTP/1.1 200 whatever\r\nServer: Fancy 1.0\r\n\r\n"
		]
	)
	@unpack
	def test_parent_connect_response(self, componen_name, res, response):
		ret = Component.get(
			"upstreams", componen_name
		).recv_connect_handle(HTTPResponse.from_buffer(Buffer(response.encode())))
		assert ret == res
	
	@data(
		["RemoteProxy", "ParentProxy", True],
		["RemoteProxy", "ParentProxyWrongCredentials", False],
	)
	@unpack
	def test_authentication(self, server_name, upstream_name, result):
		assert servers[server_name].handle_authentication(
			HTTPRequest(Buffer(
				Component.get(
					"upstreams", upstream_name
				).create_connect_message("www.abc.com", 80)
			))
		) is result
