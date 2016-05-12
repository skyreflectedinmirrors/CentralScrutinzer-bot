#!/usr/bin/env python2.7
import logging
import praw.errors as pr_err
import requests
import praw as praw
import praw.handlers as pr_hand
import urlparse
import time
from enum import Enum
import utilitymethods
import OAuth2Util


class ErrorCodes(Enum):
    success, praw_creation_failure, bad_credentials, oauth_refresh_required, praw_multi_not_started, \
    subreddit_does_not_exist, oauth_scope_required, comment_on_deleted, link_too_old, already_submitted = range(10)


error_strings = {
    ErrorCodes.praw_creation_failure: 'Failed to create PRAW object, bad credentials or praw-multiprocess not started',
    ErrorCodes.bad_credentials: 'Attribute {} missing from credentials file!',
    ErrorCodes.oauth_scope_required: 'Private subreddit or insufficient oauth scope given!',
    ErrorCodes.oauth_refresh_required: 'OAuth refresh required!',
    ErrorCodes.praw_multi_not_started: 'Please start praw-multiprocess',
    ErrorCodes.subreddit_does_not_exist: 'Subreddit does not exist',
    ErrorCodes.comment_on_deleted: 'Attempted to leave comment on deleted link.',
    ErrorCodes.link_too_old: 'Attempted operation on non-modifiable (OLD) link',
    ErrorCodes.already_submitted: 'Link with this url has already been submitted'}

"""
A simple wrapper that can be imported to elsewhere to retry on oauth refresh
"""


def oauth_retry(func, oauth_helper):
    def retried_func(*args, **kwargs):
        value = func(*args, **kwargs)
        if isinstance(value, ErrorCodes) and value == ErrorCodes.oauth_refresh_required:
            oauth_helper.refresh()
            return func(*args, **kwargs)
        return value

    return retried_func()


"""
The generic wrapper for reddit actions
"""


def retry(func, max_tries=5, wait=2):
    def retried_func(*args, **kwargs):
        tries = 0
        while True:
            try:
                return func(*args, **kwargs)
            except pr_err.OAuthInvalidToken:
                logging.warning(error_strings[ErrorCodes.oauth_refresh_required])
                return ErrorCodes.oauth_refresh_required
            except pr_err.LoginOrScopeRequired:
                logging.critical(error_strings[ErrorCodes.oauth_scope_required])
                return ErrorCodes.oauth_scope_required
            except pr_err.Forbidden, e:
                logging.critical(error_strings[ErrorCodes.oauth_scope_required])
                return ErrorCodes.oauth_scope_required
            except pr_err.APIException, e:
                if e.error_type == u'DELETED_LINK':
                    logging.warn(error_strings[ErrorCodes.comment_on_deleted])
                    return ErrorCodes.comment_on_deleted
                elif e.error_type == u'TOO_OLD':
                    logging.warn(error_strings[ErrorCodes.link_too_old])
                    return ErrorCodes.link_too_old
                elif e.error_type == u'ALREADY_SUB':
                    logging.warn(error_strings[ErrorCodes.already_submitted])
                    return ErrorCodes.already_submitted
            except pr_err.InvalidSubreddit:
                logging.critical(error_strings[ErrorCodes.subreddit_does_not_exist])
                return ErrorCodes.subreddit_does_not_exist
            except Exception, e:
                logging.exception(e)


            tries += 1
            if tries == max_tries:
                break
            time.sleep(wait)

    return retried_func


"""
Reddit/subreddit/OAuth creation
"""


def get_oauth_handler(reddit):
    try:
        oauth = OAuth2Util.OAuth2Util(reddit)
        oauth.refresh(force=True)
        return oauth
    except Exception, e:
        if e.errno == 10061:
            logging.critical(error_strings[ErrorCodes.praw_multi_not_started])
            return ErrorCodes.praw_multi_not_started
        raise e


@retry
def create_praw(credentials, multiprocess=True):
    if not u'USERAGENT' in credentials:
        utilitymethods.create_useragent(credentials)
    try:
        if multiprocess:
            my_handler = pr_hand.MultiprocessHandler()
            r = praw.Reddit(user_agent=credentials[u'USERAGENT'], handler=my_handler,
                            site_name=u'reddit')
        else:
            r = praw.Reddit(user_agent=credentials[u'USERAGENT'],
                            site_name=u'reddit')
    except KeyError:
        logging.critical(error_strings[ErrorCodes.bad_credentials].format(str(e)))
        return ErrorCodes.bad_credentials

    logging.info('Praw created successfully')
    return r


@retry
def get_subreddit(reddit, subreddit, test_existance=False):
    sub = reddit.get_subreddit(subreddit)
    logging.info("Retrieved subreddit object")
    if test_existance:
        sub.get_top().next()
    return sub

"""
Various reddit operations
"""


@retry
def get_posts(sub, limit=20, prefetch=True):
    posts = sub.get_new(limit=limit)
    if prefetch:
        return [x for x in posts]
    return posts


@retry
def make_comment(post, text, dist=False):
    comment = post.add_comment(text)
    if dist:
        comment.distinguish()
    return comment

@retry
def make_post(sub, title, text=None, url=None, distinguish=False):
    theargs = {u'title':title}
    if text is not None:
        theargs[u'text'] = text
    elif url is not None:
        theargs[u'url'] = url
    else:
        logging.warn('Cannot make post without text or url!')
        return None
    post = sub.submit(**theargs)
    if distinguish:
        post.distinguish()
    return post

@retry
def get_comments(post):
    try:
        comments = helper.flatten_tree(post.comments)
        return comments
    except Exception, e:
        logging.error("Comments not retrieved successfully")
        if __debug__:
            logging.exception(e)
    return None


def remove_comment(comment, mark_spam=False):
    try:
        comment.remove(spam=mark_spam)
        return True
    except Exception, e:
        logging.error("Comment not removed successfully")
        if __debug__:
            logging.exception(e)
    return False


def write_wiki_page(wiki, content, reason=''):
    """Writes to a wiki page, returns true if written successfully"""
    try:
        wiki.edit(content=content, reason=reason)
        return True
    except Exception, e:
        logging.error("Error writing wiki page.")
        if __debug__:
            logging.exception(e)
    return False


def get_wiki_content(wiki):
    """Reads from a wiki page, returns content if read successfully"""
    try:
        return wiki.content_md
    except Exception, e:
        logging.error("Could not retrieve wiki page content")
        if __debug__:
            logging.exception(e)
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
            if __debug__:
                logging.exception(e)
    except Exception, e:
        logging.error("Could not get wiki page")
        if __debug__:
            logging.exception(e)
    return wiki


def get_unread(reddit, limit=10):
    """Returns a list of messages
    """
    comments = None
    try:
        comments = reddit.get_unread(limit=limit)
    except requests.exceptions.HTTPError, e:
        logging.error("Unread mail for user could not be retrieved")
        if __debug__:
            logging.exception(e)
    except Exception, e:
        logging.error("Unread mail for user could not be retrieved")
        if __debug__:
            logging.exception(e)
    return comments


def get_mods(reddit, sub):
    try:
        return reddit.get_moderators(sub)
    except Exception, e:
        logging.error("Could not retrieve moderators for sub: " + str(sub))
        if __debug__:
            logging.exception(e)
        return None


def send_message(reddit, user, subject, message):
    """sends a message to user 'user' with subject and message
        :type reddit AuthenticatedReddit
        :return True if sent correctly, false otherwise
    """
    try:
        if len(message) >= 10000:
            temp = "  \nMessage too long, truncated to 10000 characters..."
            message = message[:10000 - len(temp)] + temp
        reddit.send_message(user, subject, message)
    except requests.exceptions.HTTPError, e:
        logging.error("Message " + subject + " could not be sent to user " + user)
        if __debug__:
            logging.exception(e)
        return False
    except Exception, e:
        logging.error("Message " + subject + " could not be sent to user " + user)
        if __debug__:
            logging.exception(e)
        return False
    return True


def xpost(post, other_sub, comment):
    try:
        return make_post_url(other_sub, title=post.title + "//" + comment, url=u"http://redd.it/{}".format(post.id))
    except Exception, e:
        logging.error("Post " + str(post.id) + " could not be cross posted")
        if __debug__:
            logging.exception(e)
        return False


def get_username(post):
    try:
        return post.author.name
    except:
        return None


def is_deleted(post):
    try:
        return post.author is None or (post.author is not None and post.author.name == "[deleted]")
    except:
        return False


def is_deleted(post):
    try:
        return post.author is None or (post.author is not None and post.author.name == "[deleted]")
    except:
        return False


def get_by_ids(reddit, id_list):
    """ Gets a list of posts by submission id

    :param reddit: the praw object
    :param id_list: the list of post id's (should be the submission's name property)
    :return: a list of loaded posts
    """
    if not id_list:
        return None
    try:
        return reddit.get_submissions(id_list)
    except TypeError, e:
        logging.error("At least one non-string in id_list passed to get_by_ids")
    except Exception, e:
        logging.error("Posts with id's: " + ", ".join(id_list)[:30] + " were not loaded")
        if __debug__:
            logging.exception(e)
        return None


def resolve_url(url):
    """Resolves a url for caching and storing purposes
    :return: the resolved url, or None if an exception occurs
    """

    # determine scheme and netloc
    parsed = urlparse.urlparse(url)
    if parsed.scheme == httplib.HTTP or parsed.scheme == "http":
        h = httplib.HTTPConnection(parsed.netloc)
    elif parsed.scheme == httplib.HTTPS or parsed.scheme == "https":
        h = httplib.HTTPSConnection(parsed.netloc)
    else:
        logging.warning("Could not determine net scheme for url " + url)
        return None

    # add query
    resource = parsed.path
    if parsed.query != "":
        resource += "?" + parsed.query

    # ask server
    try:
        h.request('HEAD', resource,
                  headers={"USER-AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:13.0) Gecko/13.0 Firefox/13.0"})
        response = h.getresponse()
    except httplib.error, e:
        logging.error("Error on resolving url " + url + "\n" + str(e))
        if __debug__:
            logging.exception(e)
        return None

    # check for redirection
    if response.status / 100 == 3 and response.getheader('Location'):
        return resolve_url(response.getheader('Location'))  # changed to process chains of short urls
    else:
        return url
