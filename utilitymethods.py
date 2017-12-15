import praw as p
import logging
import praw.exceptions as errors
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
    if num < 0:
        num = int(1e6)
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
                print("# {} deleted...".format(i))
            except AttributeError:
                # Post or Comment may have been deleted between retrieving it
                # and accessing its fields
                pass
    except AssertionError, e:
        logging.log(logging.DEBUG, str(e) + "\nNo Posts!")

def create_multiprocess_praw(credentials):
    #create my reddit
    try:
        r = p.Reddit(user_agent=credentials['USERAGENT'],
                     client_id=credentials['CLIENT_ID'],
                     client_secret=credentials['CLIENT_SECRET'],
                     username=credentials['USERNAME'],
                     password=credentials['PASSWORD'],
                     refresh_token=credentials['REFRESH_TOKEN'])
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
        r = p.Reddit(user_agent=credentials['USERAGENT'],
                     client_id=credentials['CLIENT_ID'],
                     client_secret=credentials['CLIENT_SECRET'],
                     username=credentials['USERNAME'],
                     password=credentials['PASSWORD'],
                     refresh_token=credentials['REFRESH_TOKEN'])
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
