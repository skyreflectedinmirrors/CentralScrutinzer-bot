import unittest
import CredentialsImport as cr
import Actions as act
import utilitymethods

class TestRedditThread(unittest.TestCase):
    def __init__(self, methodname="runTest"):
        self.creds = cr.CRImport(u'testcredentials.cred')
        utilitymethods.create_useragent(self.creds, True)
        super(TestRedditThread, self).__init__(methodname)

    def __get_oauth(self, multi=True):
        reddit = act.create_praw(self.creds, multiprocess=multi)
        oath = act.get_oauth_handler(reddit)
        return reddit, oath

    def __get_sub(self, multi=True):
        reddit, oath = self.__get_oauth()
        sub = act.get_subreddit(reddit, self.creds[u'SUBREDDIT'], test_existance=True)
        return sub

    def test_create_reddit(self):
        self.assertTrue(act.create_praw(self.creds, multiprocess=True) != act.ErrorCodes.praw_creation_failure)
        self.assertTrue(act.create_praw(self.creds, multiprocess=False) != act.ErrorCodes.praw_creation_failure)

    def test_create_oauth(self):
        r, o = self.__get_oauth()
        y = r.get_me()
        self.assertTrue(y.name == self.creds[u'USERNAME'])

    def test_get_reddit(self):
        r, o = self.__get_oauth()
        s = act.get_subreddit(r, self.creds[u'SUBREDDIT'])
        self.assertTrue(s.display_name == self.creds[u'SUBREDDIT'])

        s = act.get_subreddit(r, u'notarealzuzbdafasd', test_existance=True)
        self.assertTrue(s == act.ErrorCodes.subreddit_does_not_exist)

    def test_get_posts(self):
        s = self.__get_sub()
        self.assertTrue(isinstance(act.get_posts(s, prefetch=True), list))

    def test_make_post(self):
        s = self.__get_sub()
        post = act.make_post(s, 'test', url='www.google.com')
        self.assertTrue(post is not None)
        self.assertTrue(not isinstance(post, act.ErrorCodes) or post == act.ErrorCodes.already_submitted)
        self.assertTrue(post == act.ErrorCodes.already_submitted or post.url == 'www.google.com')
        post = act.make_post(s, 'test', text='test')
        self.assertTrue(post is not None and not isinstance(post, act.ErrorCodes) and post.selftext == 'test')
        post = act.make_post(s, 'test', text='test', distinguish=True)
        self.assertTrue(post is not None and not isinstance(post, act.ErrorCodes) and post.selftext == 'test')

    def test_make_comment(self):
        s = self.__get_sub()
        x = act.get_posts(s, prefetch=True)
        self.assertTrue(x is not None)
        post = x[0]
        comment = act.make_comment(post, "testcomment", dist=True)
        self.assertTrue(comment is not None and not isinstance(comment, act.ErrorCodes))
        self.assertTrue(comment.body == u"testcomment")




