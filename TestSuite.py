#Test-Suite.py

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
			print 'please enter captcha resposne for\n' + "www.reddit.com/captcha/" +  captcha['iden'] + ".png"
			captcha['captcha'] = raw_input()

def testMakePost(sub):
	#spawn a  action
	action = Actions.MakePost(sub, "testpost", "please ignore", captcha)
	action.execute()
	action.callback()
	return action.Post
			
def testRemovePost(sub, post = None):
	if (not post):
		#create a post
		post = sub.submit("testpost", text="please ignore", raise_captcha_exception=True, captcha=captcha)
	#spawn a Removal action
	action = Actions.RemovePost(post)
	action.execute()
	action.callback()

def main():
	g.init()
	#import credentials
	credentials = CRImport("TestCredentials.cred")
	#create my reddit
	r = praw.Reddit(user_agent = credentials['USERAGENT'])
	r.login(credentials['USERNAME'], credentials['PASSWORD'])
	sub = r.get_subreddit(credentials['SUBREDDIT'])
	
	#get Capthca
	getCaptcha(sub)
	
	#run MakePost test
	p = testMakePost(sub)
	
	#run RemovePost test
	testRemovePost(sub, p)
	
if (__name__ == "__main__"):
	main()