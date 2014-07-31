"""Actions.py - contains methods to perform the simple actions of the centralscruitinzer bot
They are placed here so that they can be properly error checked from any calling location
"""

import logging

import praw.errors
import requests


def make_post_text(sub, title, message, callback=None, distinguish=False):
    try:
        # create a post
        post = sub.submit(title, text=message, raise_captcha_exception=True)
        if callback:
            callback(post)
        logging.info("Post " + post.title + " created.")
    except praw.errors.InvalidCaptcha, e:
        logging.warning("Warning: invalid captcha detected")
    except Exception, e:
        logging.error(str(e))
        logging.warning("Post " + title + " not created.")

def make_post_url(sub, title, url, callback=None, distinguish=False):
    post = None
    try:
        # create a post
        post = sub.submit(title, url=url, raise_captcha_exception=True)
        if callback:
            callback(post)
        logging.info("Post " + post.title + " created.")
    except praw.errors.InvalidCaptcha, e:
        logging.warning("Warning: invalid captcha detected")
    except Exception, e:
        logging.error(str(e))
        logging.warning("Post " + title + " not created.")
    return post


def remove_post(post, callback=None, mark_spam=False, delete=False):
    try:
        if(delete):
            post.delete()
        else:
            post.remove(spam=mark_spam)
        if callback:
            callback(True)
        logging.info("Post " + post.title + " was removed")
    except Exception, e:
        logging.error(str(e))
        logging.warning("Post " + str(post) + " was removed")


def ban_user(sub, reason, user, callback=None):
    try:
        sub.add_ban(user)
        if (callback):
            callback(True)
        logging.info("User " + str(user) + " was banned for " + str(reason))
    except Exception, e:
        logging.error(str(e))
        logging.warning("User " + str(user) + " was not successfully banned for " + str(reason))


def unban_user(sub, user, callback=None):
    try:
        sub.remove_ban(user)
        if callback:
            callback(True)
        logging.info("User " + str(user) + " unbanned successfully.")
    except Exception, e:
        logging.error(str(e))
        logging.warning("User " + str(user) + " not unbanned successfully.")


def get_posts(sub, callback=None, limit=20):
    try:
        posts = sub.get_new(limit=limit)
        if callback:
            callback(posts)
        if logging.getLogger().getEffectiveLevel() >= logging.INFO:
            logging.info("Posts " + ', '.join([str(post.id) for post in posts]) + " were made successfully.")
    except Exception, e:
        logging.info("Posts not made correctly")
        logging.warning(str(e))


def make_comment(post, text, callback=None):
    try:
        comment = post.add_comment(text)
        if callback:
            callback(comment)
        logging.info("Comment " + str(comment) + " was made successfully!")
    except Exception, e:
        logging.error(str(e))
        logging.warning("Comment " + (comment) + " was made successfully!")


import praw.helpers as helper


def get_comments(post, callback):
    try:
        comments = helper.flatten_tree(post.comments)
        if callback:
            callback(comments)
        # only write if needed
        if logging.getLogger().getEffectiveLevel() >= logging.INFO:
            logging.info("Comments " + ', '.join([str(comment.id) for comment in comments]) + " retrieved successfully")
    except Exception, e:
        logging.error(str(e))
        logging.warning("Comments not retrieved successfully")

def remove_comment(comment, callback=None, mark_spam=False):
    try:
        comment.remove(spam=mark_spam)
        if callback:
            callback(comment)
        logging.info("Comment" + str(comment) + " removed successfully")
    except Exception, e:
        logging.error(str(e))
        logging.warning("Comment" + str(comment) + " not removed successfully")

def write_wiki_page(wiki, content, reason=''):
    """Writes to a wiki page, returns true if written successfully"""
    try:
        wiki.edit(content=content, reason=reason)
        return True
    except Exception, e:
        logging.critical("Error writing wiki page.")
    return False

def get_wiki_content(wiki):
    """Reads from a wiki page, returns content if read successfully"""
    try:
        return wiki.content_md
    except Exception, e:
        logging.warning("Could not retrieve wiki page content")
        return None

def get_or_create_wiki(reddit, sub, page):
    """Returns the specified wiki page, it will be created if not already extant"""
    try:
        wiki = reddit.get_wiki_page(sub, page)
    except requests.exceptions.HTTPError, e:
        logging.warning("Wiki page " + page + " not created for subreddit, creating...")
        reddit.edit_wiki_page(sub, page, content="", reason="initial commit")
        wiki = reddit.get_wiki_page(sub, page)
    return wiki

from praw import AuthenticatedReddit
def get_unread(reddit, limit=10):
    """Returns a list of messages
        :type reddit AuthenticatedReddit
    """
    comments = None
    try:
        comments = reddit.get_unread(limit = limit)
    except requests.exceptions.HTTPError, e:
        logging.error("Unread mail for user could not be retrieved")
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
        return False
    return True

import urlparse
import httplib
def resolve_url(url):
    """Resolves a url for caching and storing purposes
    :return: the resolved url, or None if an exception occurs
    """

    #determine scheme and netloc
    parsed = urlparse.urlparse(url)
    if parsed.scheme == httplib.HTTP:
        h = httplib.HTTPConnection(parsed.netloc)
    elif parsed.scheme == httplib.HTTPS:
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
