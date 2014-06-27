#Actions.py - contains classes to perform the simple actions of the centralscruitinzer bot
#				An action is different from a job in that an action DOES NOT require loading of data from Reddit

from Callback import Callback
import globaldata as g

class ActionType:
	RemovePost, MakePost = range(2)
	
def writelog(exception):
	g.Log.info(str(exception))

#base Action definition
#has method stubs for execute
class Action(Callback):
	def __init__(self, Type):
		self.Type = Type
		self.Success = None
	
	def execute(self):
		raise Exception("Cannot instantiate base Action class!")

#makes the specified post
class MakePost(Action):
	def __init__(self, sub, title, message, captcha, distinguish = False):
		super(MakePost, self).__init__(ActionType.MakePost)
		self.sub = sub
		self.title = title
		self.message = message
		self.distinguish = False
		self.Post = None
		self.captcha = captcha
	def execute(self):
		try:
			#create a post
			self.Post = self.sub.submit("testpost", "please ignore", raise_captcha_exception=True, captcha=self.captcha)
		except Exception, e:
			writelog(e)
	def callback(self):
		if (not self.Post):
			writelog ("Post was not successfully posted")
		else:
			writelog ("Posted " + self.Post.title)

#makes the removes the specified post		
class RemovePost(Action):
	def __init__(self, Post, markspam = False):
		super(RemovePost, self).__init__(ActionType.RemovePost)
		self.Post = Post
		self.markspam = markspam
	
	def execute(self):
		try:
			self.Post.remove(spam = self.markspam)
			self.Success = True
		except Exception, e:
			writelog(e)
			self.Success = False
			
	def callback(self):
		writelog("Post " + self.Post.title + (" was " if self.Success else "was not ") + "removed successfully!")