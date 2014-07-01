# globals.py
#	global methods and variables

import logging
import sys
import atexit

Debug = True
Exectution = not Debug

def init():
    Log = logging.getLogger()
    if (Debug == True):
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
    elif(Exectution):
        raise Exception()

    #schedule log closing for exit
    atexit.register(close)

def close():
    x = logging._handlers.copy()
    for i in x:
        logging.getLogger().removeHandler(i)
        i.flush()
        i.close()