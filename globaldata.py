#globals.py
#	global methods and variables

import logging
import sys

def init():
	global Log
	Log = logging.getLogger()
	Log.setLevel(logging.DEBUG)
	# create file handler which logs even debug messages
	fh = logging.FileHandler('error.log')
	fh.setLevel(logging.DEBUG)
	# create console handler with a higher log level
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(logging.ERROR)
	# create formatter and add it to the handlers
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fh.setFormatter(formatter)
	ch.setFormatter(formatter)
	# add the handlers to the logger
	Log.addHandler(fh)
	Log.addHandler(ch)