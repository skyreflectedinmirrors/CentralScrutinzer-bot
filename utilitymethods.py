import praw.handlers as h
import praw as p
import logging
import praw.errors as errors

import psutil
import subprocess
def create_multiprocess_praw(credentials):
    #create my reddit
    my_handler = h.MultiprocessHandler()
    try:
        r = p.Reddit(user_agent=credentials['USERAGENT'], handler=my_handler)
        r.login(username=credentials['USERNAME'], password=credentials['PASSWORD'])
        logging.info("Multi-process handler sucessfully started")
        return r
    except Exception, e:
        logging.error(str(e))
        logging.warning("Failed to create Multi-process PRAW object")
        return None

def create_praw(credentials):
    try:
        r = p.Reddit(user_agent=credentials['USERAGENT'])
        r.login(username=credentials['USERNAME'], password=credentials['PASSWORD'])
        return r
    except Exception, e:
        logging.error(str(e))
        logging.warning("Failed to create PRAW object")
        return None

def get_subreddit(credentials, praw):
    try:
        sub = praw.get_subreddit(credentials['SUBREDDIT'])
        logging.info("Retrieved subreddit object")
        return sub
    except Exception, e:
        logging.error(str(e))
        logging.warning("Failed to retrieve subreddit object")
        return None

def getCaptcha(sub):
    captcha = {}
    try:
        post = sub.submit("testpost", text="please ignore", raise_captcha_exception=True)
    except errors.InvalidCaptcha, err:
        captcha['iden'] = err.response['captcha']
        print 'please enter captcha resposne for\n' + "www.reddit.com/captcha/" + captcha['iden'] + ".png"
        captcha['captcha'] = raw_input()
    return captcha
