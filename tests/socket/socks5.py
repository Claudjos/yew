from yew.modules.socks5.socks5 import *

import unittest
from ddt import ddt, data, unpack

from yew.core.components import Component

from threading import Thread
from yew.__main__ import *
import requests
import time

def setUpModule():
	global thread
	def run_yew(configfile):
		configurations = read_configuration_from_file(configfile)
		run(configurations)
	thread = Thread(target=run_yew, args=("examples/configuration/socks5.yaml", ))
	thread.start()
	time.sleep(0.5)


def tearDownModule():
	global thread
	pass


@ddt
class Socks5TestCases(unittest.TestCase):
	
	def test_example(self):

		response = requests.get("https://www.google.com",
			proxies=dict(
				http='socks5://io:pwd@localhost:1080',
				https='socks5://io:pwd@localhost:1080'
			)
		)
		assert response.status_code == 200

	def test_example2(self):

		response = requests.get("https://www.google.com",
			proxies=dict(
				http='socks5://io:pwd@localhost:1081',
				https='socks5://io:pwd@localhost:1081'
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
