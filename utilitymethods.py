import praw.handlers as h
import praw as p
import logging
import praw.errors as errors
import Actions
import socket

import re
from urlparse import urlsplit
def domain_extractor(url):
    """returns the netloc part of a url w/ exception handling

    :param url: the url to check
    :return: the domain of the url (i.e. netloc as determined by urlparse
    """
    if not re.match(r'http(s?)\:', url):
        url = 'http://' + url
    try:
        parsed = urlsplit(url)
        retval = parsed.netloc
        if retval.startswith("www."):
            retval = retval[4:] #ignore any www. for consistency
        return retval
    except Exception, e:
        logging.error("Bad url sent for domain extraction " + str(url))
        return None

def clear_sub(credentials, sub, num=20):
    """Removes all* old posts from a sub (use with care)

    * up to 900
    :param credentials:
    :param sub:
    :return:
    """
    num = min(num, 900)
    mypraw = create_multiprocess_praw(credentials)
    sub = get_subreddit(credentials, mypraw, sub)
    old_stream = p.helpers.submission_stream(mypraw, sub, limit=num)
    results = []
    try:
        #delete all old posts
        for i in range(num):
            try:
                post = old_stream.next()
                Actions.remove_post(post, delete=True)
                print("deleted old post: %s..." % post.title[:20])
            except AttributeError:
                # Post or Comment may have been deleted between retrieving it
                # and accessing its fields
                pass
    except AssertionError, e:
        logging.log(logging.DEBUG, str(e) + "\nNo Posts!")

def create_multiprocess_praw(credentials):
    #create my reddit
    my_handler = h.MultiprocessHandler()
    try:
        r = p.Reddit(user_agent=credentials['USERAGENT'], handler=my_handler)
        r.login(username=credentials['USERNAME'], password=credentials['PASSWORD'])
        logging.info("Multi-process handler sucessfully started")
        return r
    except socket.error, e:
        logging.error(str(e))
        logging.critical("Failed to create Multi-process PRAW object, bad credentials or praw-multiprocess not started")
        return None
    except IOError, e:
        logging.error(str(e))
        logging.critical("Failed to create Multi-process PRAW object, bad credentials or praw-multiprocess not started")
        return None

def create_praw(credentials):
    try:
        r = p.Reddit(user_agent=credentials['USERAGENT'])
        r.login(username=credentials['USERNAME'], password=credentials['PASSWORD'])
        return r
    except socket.error, e:
        logging.error(str(e))
        logging.critical("Failed to create PRAW object: bad credentials")
        return None

def get_subreddit(credentials, praw, subreddit = None):
    try:
        subreddit = subreddit if subreddit else credentials['SUBREDDIT']
        sub = praw.get_subreddit(subreddit)
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
