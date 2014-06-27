# Callback.py - contains a definition for a default asynch callback object
#				All jobs and actions must define a callback

class Callback(object):
    def __init__(self):
        self.isCallback = True

    def callback(self, Success):
        raise Exception("")
