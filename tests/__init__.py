from yew.core.settings import read_configuration_from_file, load_components, load_servers
from yew.core.components import Component
from yew.core.looper import Looper


import logging
logging.getLogger("urllib3.connectionpool").propagate = False


def load_file(name):
	configurations = read_configuration_from_file(name)
	load_components(configurations)
	load_servers(Looper(), configurations)
	return Component._MAP["servers"]
