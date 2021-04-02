from yew.modules.socks5.socks5 import *

import unittest
from ddt import ddt, data, unpack

from yew.core.components import Component

from threading import Thread
from yew.__main__ import *
import requests, logging
import time

def setUpModule():
	global thread
	def run_yew(configfile):
		configurations = read_configuration_from_file(configfile)
		run(configurations)
	thread = Thread(target=run_yew, args=("examples/configuration/parent.yaml", ))
	thread.start()
	time.sleep(0.5)


def tearDownModule():
	global thread
	pass


@ddt
class HttpTestCases(unittest.TestCase):
	
	def test_example(self):

		response = requests.get("https://www.google.com",
			proxies=dict(
				http='http://io:pwd@localhost:8080',
				https='http://io:pwd@localhost:8080'
			)
		)
		assert response.status_code == 200

	def test_example3(self):

		response = requests.get("http://www.google.com",
			proxies=dict(
				http='http://io:pwd@localhost:8080',
				https='http://io:pwd@localhost:8080'
			)
		)
		assert response.status_code == 200

	def test_example2(self):

		response = requests.get("https://www.google.com",
			proxies=dict(
				http='http://localhost:8081',
				https='http://localhost:8081'
			)
		)
		assert response.status_code == 200

	"""
	def test_example3(self):

		response = requests.get("https://www.google.com",
			proxies=dict(
				http='socks5://io:pwd@localhost:1082',
				https='socks5://io:pwd@localhost:1082'
			)
		)
		print(response.text)
		assert response.status == 200
	"""
	