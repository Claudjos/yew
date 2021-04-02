import yaml
import importlib
import logging
from typing import Tuple, List, Type
from .looper import Looper
from .components import Component


def read_configuration_from_file(file: str) -> dict:
	"""
	Reads configuration from YAML file
	"""
	with open(file, "r") as stream:
		try:
			return yaml.safe_load(stream)
		except yaml.YAMLError as exc:
			logging.exception("Unable to parse configurations")
			return {}

def build_server_sockets(looper: Looper, 
	configurations: dict) -> List[Tuple["socket.socket", "data"]]:
	"""
	Builds the server sockets.
	"""
	server_sockets = []
	for server in Component.get_by_category("servers"):
		server.set_looper(looper)
		server_sockets.append(server.create_server_socket())
	return server_sockets


def import_class(value: str) -> Type:
	"""
	PARAMS
		- value: a string in the format module:class (e.g., yew.modules.foo:BarClass)
	"""
	module, klass = value.split(":")
	return getattr(importlib.import_module(module), klass)


def load_component(category, component):
	"""
	- name: MyComponent
	  class: mymodule:MyClass
	  params: {}
	"""
	name = component.get("name")
	klass = import_class(component.get("class"))
	instance = klass.build(name, component.get("params"))
	Component.install(category, instance)
	logging.debug("Component {}:{} loaded".format(
		name,
		str(klass)
	))


def load_components(configurations: dict):
	for category in configurations.get("components", []):
		for component in configurations["components"][category]:
			load_component(category, component)


def load_servers(looper, configurations: dict):
	for category in configurations.get("servers", []):
		for component in configurations["servers"][category]:
			load_component("servers", component)
