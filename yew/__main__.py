import logging
import sys
from .core.looper import Looper
from .core.settings import *


def run(configurations):
	looper = Looper()
	load_components(configurations)
	load_servers(looper, configurations)
	# Add the sockets to the looper
	for server in build_server_sockets(looper, configurations):
		looper.register_for_read(server[0], server[1])
	# Run forever
	try:
		looper.run()
	except KeyboardInterrupt:
		logging.info("Bye bye !")
	except BaseException as e:
		logging.exception("Something unexpected happened {}".format(e))


if __name__ == "__main__":
	# Init
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
	if len(sys.argv) < 2:
		configfile = "config.yaml"
	else:
		configfile = sys.argv[1]
	configurations = read_configuration_from_file(configfile)
	run(configurations)
