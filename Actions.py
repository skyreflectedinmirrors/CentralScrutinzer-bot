"""Actions.py - contains methods to perform the simple actions of the centralscruitinzer bot
They are placed here so that they can be properly error checked from any calling location
"""

import logging

import praw.errors
import requests


def make_post_text(sub, title, message, distinguish=False):
    try:
        # create a post
        post = sub.submit(title, text=message, raise_captcha_exception=True)
        return post
    except praw.errors.InvalidCaptcha, e:
        logging.error("Invalid captcha detected")
    except Exception, e:
        logging.error("Post with title: " + title + "\tmessage: " + message + " not created.")
        logging.debug(str(e))
    return None

def make_post_url(sub, title, url, distinguish=False):
    try:
        # create a post
        post = sub.submit(title, url=url, raise_captcha_exception=True)
        return post
    except praw.errors.InvalidCaptcha, e:
        logging.error("Invalid captcha detected")
    except Exception, e:
        logging.error("Post with title: " + title + "\turl: " + url + " not created.")
        logging.debug(str(e))
    return None

def approve_post(post):
    try:
        post.approve()
        return True
    except Exception, e:
        logging.error("Post " + str(post.id) + " was not approved")
        logging.debug(str(e))
    return False

def remove_post(post, mark_spam=True, delete=False):
    try:
        if(delete):
            post.delete()
        else:
            post.remove(spam=mark_spam)
        return True
    except Exception, e:
        logging.error("Post " + str(post.id) + " was not removed")
        logging.debug(str(e))
    return False


def ban_user(sub, reason, user):
    try:
        sub.add_ban(user)
        logging.info("User " + str(user) + " was banned for " + str(reason))
        return True
    except Exception, e:
        logging.error("User " + str(user) + " was not successfully banned for " + str(reason))
        logging.debug(str(e))
    return False


def unban_user(sub, user):
    try:
        sub.remove_ban(user)
        logging.info("User " + str(user) + " unbanned successfully.")
        return True
    except Exception, e:
        logging.error("User " + str(user) + " not unbanned successfully.")
        logging.debug(str(e))
    return False


def get_posts(sub, limit=20):
    try:
        posts = sub.get_new(limit=limit)
        return posts
    except Exception, e:
        logging.error("Posts retrieved made correctly")
        logging.debug(str(e))
    return None


def make_comment(post, text):
    try:
        comment = post.add_comment(text)
        return comment
    except Exception, e:
        logging.error("Comment " + text + " was not made successfully!")
        logging.debug(str(e))
    return None

import praw.helpers as helper


def get_comments(post):
    try:
        comments = helper.flatten_tree(post.comments)
        return comments
    except Exception, e:
        logging.error("Comments not retrieved successfully")
        logging.debug(str(e))
    return None

def remove_comment(comment, mark_spam=False):
    try:
        comment.remove(spam=mark_spam)
        return True
    except Exception, e:
        logging.error("Comment not removed successfully")
        logging.debug(str(e))
    return False

def write_wiki_page(wiki, content, reason=''):
    """Writes to a wiki page, returns true if written successfully"""
    try:
        wiki.edit(content=content, reason=reason)
        return True
    except Exception, e:
        logging.error("Error writing wiki page.")
        logging.debug(str(e))
    return False

def get_wiki_content(wiki):
    """Reads from a wiki page, returns content if read successfully"""
    try:
        return wiki.content_md
    except Exception, e:
        logging.error("Could not retrieve wiki page content")
        logging.debug(str(e))
    return None

def get_or_create_wiki(reddit, sub, page):
    """Returns the specified wiki page, it will be created if not already extant"""
    wiki = None
    try:
        wiki = reddit.get_wiki_page(sub, page)
    except requests.exceptions.HTTPError, e:
        logging.warning("Wiki page " + page + " not created for subreddit, creating...")
        try:
            reddit.edit_wiki_page(sub, page, content="", reason="initial commit")
            wiki = reddit.get_wiki_page(sub, page)
        except Exception, e:
            logging.error("Could not create wiki page.")
            logging.debug(str(e))
    except Exception, e:
        logging.error("Could not get wiki page")
        logging.debug(str(e))
    return wiki

def get_unread(reddit, limit=10):
    """Returns a list of messages
    """
    comments = None
    try:
        comments = reddit.get_unread(limit = limit)
    except requests.exceptions.HTTPError, e:
        logging.error("Unread mail for user could not be retrieved")
        logging.debug(str(e))
    except Exception, e:
        logging.error("Unread mail for user could not be retrieved")
        logging.debug(str(e))
    return comments

def send_message(reddit, user, subject, message):
    """sends a message to user 'user' with subject and message
        :type reddit AuthenticatedReddit
        :return True if sent correctly, false otherwise
    """
    try:
        reddit.send_message(user, subject, message)
    except requests.exceptions.HTTPError, e:
        logging.error("Message " + subject + " could not be sent to user " + user)
        logging.debug(str(e))
        return False
    except Exception, e:
        logging.error("Message " + subject + " could not be sent to user " + user)
        logging.debug(str(e))
        return False
    return True

def xpost(post, other_sub, comment):
    try:
        return make_post_url(other_sub, title=post.title + "//"  + comment, url="http://redd.it/{}".format(post.id))
    except Exception, e:
        logging.error("Post " + str(post.id) + " could not be cross posted")
        logging.debug(str(e))
        return False

import urlparse
import httplib
def resolve_url(url):
    """Resolves a url for caching and storing purposes
    :return: the resolved url, or None if an exception occurs
    """

    #determine scheme and netloc
    parsed = urlparse.urlparse(url)
    if parsed.scheme == httplib.HTTP or parsed.scheme == "http":
        h = httplib.HTTPConnection(parsed.netloc)
    elif parsed.scheme == httplib.HTTPS or parsed.scheme == "https":
        h = httplib.HTTPSConnection(parsed.netloc)
    else:
        logging.warning("Could not determine net scheme for url " + url)
        return None

    #add query
    resource = parsed.path
    if parsed.query != "":
        resource += "?" + parsed.query

    #ask server
    try:
        h.request('HEAD', resource)
        response = h.getresponse()
    except httplib.error, e:
        logging.error("Error on resolving url " + url + "\n" + str(e))
        return None

    #check for redirection
    if response.status/100 == 3 and response.getheader('Location'):
        return resolve_url(response.getheader('Location')) # changed to process chains of short urls
    else:
        return url
