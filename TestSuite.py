# Test-Suite.py

#I'm a man who (now) believes in unit test driven development, so this is where the unit tests live!

import praw
import praw.errors as perr
import praw.handlers as phand
from CredentialsImport import CRImport
import DataBase
import Actions as a
import globaldata as g
import utilitymethods as u

def store_post(post):
    global my_post
    my_post = post
    print "my_post = "  + my_post.title

def store_comment(comment):
    global my_comment
    my_comment = comment
    print "my_comment = "  + my_comment.id

def print_posts(posts):
    try:
        for posts in posts:
            print posts.title
    except:
        pass

def print_comments(comments):
    try:
        for comment in comments:
            print comment.text
    except:
        pass

def testMultiprocess(credentials):
    #create my reddit
    return u.create_multiprocess_praw(credentials)

def testRemoveComment(comment):
    #spawn an action
    a.remove_comment(comment)

def testGetComments(post):
    a.get_comments(post, print_comments)

def testMakeComment(post):
    #spawn an action
    a.make_comment(post, "test comment", store_comment)

def testGetPosts(sub):
    #spawn an action
    a.get_posts(sub, print_posts)


def testMakePostText(sub):
    #spawn a  action
    a.make_post_text(sub, "testpost", "please ignore", store_post)


def testRemovePost(sub, post=None):
    #spawn a Removal action
    a.remove_post(post)


def testBanUser(sub, user):
    #spawn a Removal action
    a.ban_user(sub, "test", user)


def testUnBanUser(sub, user):
    #spawn a Removal action
    a.unban_user(sub, user)


def main():
    g.init()
    g.close()
    #import credentials
    credentials = CRImport("TestCredentials.cred")

    #create my reddit
    r = u.create_praw(credentials)

    sub = r.get_subreddit(credentials['SUBREDDIT'])

    #run MakePost test
    testMakePostText(sub)

    #run RemovePost test
    testBanUser(sub, "StudabakerHoch")

    #run RemovePost test
    testUnBanUser(sub, "StudabakerHoch")

    #run get post test
    testGetPosts(sub)

    #run make comment test
    testMakeComment(my_post)

    #run get comments post
    testGetComments(my_post)

    #run make comment test
    testRemoveComment(my_comment)

    #run RemovePost test
    testRemovePost(sub, my_post)

    #run multiproc handler test
    r = testMultiprocess(credentials)

    import logging
    logging.info("Tests complete")

if (__name__ == "__main__"):
    main()