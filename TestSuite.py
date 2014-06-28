# Test-Suite.py

#I'm a man who (now) believes in unit test driven developement, so this is where the unit tests live!

import praw
import praw.errors as perr
from CredentialsImport import CRImport
import DataBase
import Actions
import globaldata as g

captcha = {}
#captcha['iden'] = 'YkKvOED85SiFLiJrGJn6LXhZ7RgJqe5a'
#captcha['captcha'] = 'qlupyz'

def getCaptcha(sub):
    global captcha
    if (not captcha):
        try:
            post = sub.submit("testpost", text="please ignore", raise_captcha_exception=True)
        except perr.InvalidCaptcha, err:
            captcha['iden'] = err.response['captcha']
            print 'please enter captcha resposne for\n' + "www.reddit.com/captcha/" + captcha['iden'] + ".png"
            captcha['captcha'] = raw_input()

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

def testRemoveComment(Comment):
    #spawn an action
    action = Actions.RemoveComment(Comment)
    action.execute()
    action.callback()

def testGetComments(Post):
    action = Actions.GetComments(Post, print_comments)
    action.execute()
    action.callback()

def testMakeComment(Post):
    #spawn an action
    action = Actions.MakeComment(Post, "test comment")
    action.execute()
    action.callback()
    return action.Comment

def testGetPosts(sub):
    #spawn an action
    action = Actions.GetPosts(sub, print_posts)
    action.execute()
    action.callback()


def testMakePost(sub):
    #spawn a  action
    action = Actions.MakePost(sub, "testpost", "please ignore", captcha)
    action.execute()
    action.callback()
    return action.Post


def testRemovePost(sub, post=None):
    if (not post):
        #create a post
        post = sub.submit("testpost", text="please ignore", raise_captcha_exception=True, captcha=captcha)
    #spawn a Removal action
    action = Actions.RemovePost(post)
    action.execute()
    action.callback()


def testBanUser(sub, user):
    #spawn a Removal action
    action = Actions.BanUser(sub, "test", user)
    action.execute()
    action.callback()


def testUnBanUser(sub, user):
    #spawn a Removal action
    action = Actions.UnBanUser(sub, user)
    action.execute()
    action.callback()


def main():
    g.init()
    #import credentials
    credentials = CRImport("TestCredentials.cred")
    #create my reddit
    r = praw.Reddit(user_agent=credentials['USERAGENT'])
    r.login(credentials['USERNAME'], credentials['PASSWORD'])
    sub = r.get_subreddit(credentials['SUBREDDIT'])

    #get Capthca
    getCaptcha(sub)

    #run MakePost test
    p = testMakePost(sub)

    #run RemovePost test
    testBanUser(sub, "StudabakerHoch")

    #run RemovePost test
    testUnBanUser(sub, "StudabakerHoch")

    #run get post test
    testGetPosts(sub)

    #run make comment test
    c = testMakeComment(p)

    #run get comments post
    testGetComments(p)

    #run make comment test
    testRemoveComment(c)

    #run RemovePost test
    testRemovePost(sub, p)

if (__name__ == "__main__"):
    main()