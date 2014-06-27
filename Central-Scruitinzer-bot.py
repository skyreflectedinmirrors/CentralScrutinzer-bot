#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Central-Scruitinzer-bot.py
#main program for /r/listentothis's centralscrutinizer

#from praw.handlers import MultiprocessHandler
import praw
import filters
from Credentials import *

r = praw.Reddit(user_agent=USERAGENT)  #, handler=MultiprocessHandler())
r.login(USERNAME, PASSWORD)
submissions = r.get_subreddit(SUBREDDIT).get_hot(limit=5)
print [str(x) for x in submissions]