# Actions.py - contains classes to perform the simple actions of the centralscruitinzer bot
# An action is different from a job in that an action DOES NOT require loading of data from Reddit

import globaldata as g
import logging

import praw.errors


def make_post(sub, title, message, callback=None, distinguish=False):
    try:
        # create a post
        post = sub.submit("testpost", "please ignore", raise_captcha_exception=True)
        if callback:
            callback(post)
        logging.info("Post " + post.title + " created.")
    except praw.errors.InvalidCaptcha, e:
        logging.warning("Warning: invalid captcha detected")
    except Exception, e:
        logging.error(str(e))
        logging.warning("Post " + title + " not created.")


def remove_post(post, callback=None, mark_spam=True):
    try:
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