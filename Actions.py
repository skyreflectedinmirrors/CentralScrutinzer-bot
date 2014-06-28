# Actions.py - contains classes to perform the simple actions of the centralscruitinzer bot
# An action is different from a job in that an action DOES NOT require loading of data from Reddit

import globaldata as g


class ActionType:
    RemovePost, MakePost, BanUser, UnBanUser, GetPosts, MakeComment, RemoveComment, GetComments = range(8)

#utility methods

#write error to log
def write_error(exception):
    g.Log.error(str(exception))

#write info to log
def write_info(Success, message):
    if g.Verbose:
        g.Log.info(message)
    elif not Success:
        g.Log.info(message)

#make callback
def make_callback(callback, data):
    Success = True
    try:
        if callback:
            callback(data)
    except Exception, e:
        Success = False
        write_error(e)
    return Success


# base Action definition
#has method stubs for execute
class Action(object):
    def __init__(self, a_type):
        self.a_type = a_type
        self.Success = None

    def execute(self):
        raise Exception("Cannot instantiate base Action class!")

    def callback(self):
        #do nothing
        pass


#makes the specified post
class MakePost(Action):
    def __init__(self, sub, title, message, captcha, distinguish=False):
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
            self.Success = True
        except Exception, e:
            self.Success = False
            write_error(e)

    def callback(self):
        if (self.Success):
            write_info(True, "Posted " + self.Post.title)
        else:
            write_info(False, "Post was not made successfully")


#makes the removes the specified post
class RemovePost(Action):
    def __init__(self, Post, mark_spam=False):
        super(RemovePost, self).__init__(ActionType.RemovePost)
        self.Post = Post
        self.mark_spam = mark_spam

    def execute(self):
        try:
            self.Post.remove(spam=self.mark_spam)
            self.Success = True
        except Exception, e:
            write_error(e)(e)
            self.Success = False

    def callback(self):
        write_info(self.Success, "Post " + self.Post.title + (" was " if self.Success else "was not ") + "removed successfully!")


#bans user from subreddit
class BanUser(Action):
    def __init__(self, sub, reason, user):
        super(BanUser, self).__init__(ActionType.BanUser)
        self.sub = sub
        self.reason = reason
        self.user = user

    def execute(self):
        try:
            self.sub.add_ban(self.user)
            self.Success = True
        except Exception, e:
            write_error(e)
            self.Success = False

    def callback(self):
        write_info(self.Success, "User " + self.user + (" was " if self.Success else "was not ") + "banned for " + self.reason)


#unbans user from subreddit
class UnBanUser(Action):
    def __init__(self, sub, user):
        super(UnBanUser, self).__init__(ActionType.UnBanUser)
        self.sub = sub
        self.user = user

    def execute(self):
        try:
            self.sub.remove_ban(self.user)
            self.Success = True
        except Exception, e:
            write_error(e)
            self.Success = False

    def callback(self):
        write_info(self.Success, "User " + self.user + (" was " if self.Success else "was not ") + "unbanned successfully!")


class GetPosts(Action):
    def __init__(self, sub, my_callback, limit=20):
        super(GetPosts, self).__init__(ActionType.GetPosts)
        self.sub = sub
        self.limit = limit
        self.Posts = None
        self.my_callback = my_callback

    def execute(self):
        try:
            self.Posts = self.sub.get_new(limit=self.limit)
            self.Success = True
        except Exception, e:
            write_error(e)
            self.Success = False

    def callback(self):
        self.Success &= make_callback(self.my_callback, self.Posts)
        write_info(self.Success, "Posts " + (" were " if self.Success else "were not ") + "retrieved successfully!")


class MakeComment(Action):
    def __init__(self, post, text):
        super(MakeComment, self).__init__(ActionType.MakeComment)
        self.post = post
        self.text = text
        self.Comment = None

    def execute(self):
        try:
            self.Comment = self.post.add_comment(self.text)
            print self.Comment
            self.Success = True
        except Exception, e:
            write_error(e)
            self.Success = False

    def callback(self):
        write_info(self.Success, "Comment " + (" was " if self.Success else "was not ") + "made successfully!")

import praw.helpers as help
class GetComments(Action):
    def __init__(self, post, my_callback = None):
        super(GetComments, self).__init__(ActionType.GetComments)
        self.Comments = None
        self.post = post
        self.my_callback = my_callback

    def execute(self):
        try:
            self.Comments = help.flatten_tree(self.post.comments)
            self.Success = True
        except Exception, e:
            write_error(e)
            self.Success = False

    def callback(self):
        self.Success &= make_callback(self.my_callback, self.Comments)
        write_info(self.Success, "Comments " + (" were " if self.Success else "were not ") + "retrieved successfully!")


class RemoveComment(Action):
    def __init__(self, comment, mark_spam = False):
        super(RemoveComment, self).__init__(ActionType.RemoveComment)
        self.comment = comment
        self.mark_spam = mark_spam

    def execute(self):
        try:
            self.comment.remove(spam = self.mark_spam)
            self.Success = True
        except Exception, e:
            write_error(e)
            self.Success = False

    def callback(self):
        write_info(self.Success, "Comment " + (" was " if self.Success else "was not ") + "removed successfully!")