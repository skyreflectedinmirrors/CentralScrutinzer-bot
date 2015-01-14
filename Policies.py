"""
Policies controlling the various actions and responses of the Central Scruitinzer
"""

import Actions
import datetime
import logging

class DefaultPolicy(object):
    """
    Historical_Scan_On_New_Database -- if true the bot will populate the database based on the last 900 (available) posts
    Scan_Sub_Period -- the wait period (in seconds) between subreddit scans
    Pause_Period -- the wait period (in seconds) when the bot is paused
    Posts_To_Load -- how many posts to load on a normal scan
    Unread_To_Load -- how many unread messages to load on a normal scan
    Threads -- how many multiprocessing threads may be used
    Max_Retries -- how many retries to use
    Retry_Multiplier -- the post multiplier for each retry
    Mod_Update_Period -- the frequency of moderator list updates
    Errors_Before_Halt -- number of errors before requesting a pause
    on_blacklist -- the action to take for a blacklisted post
    on_whitelist -- the action to take for a blacklisted post
    Blacklist_Query_Period -- the time to wait between BlacklistQuery scans
    debug_info -- a method that writes debug messages to a desired place
    """
    def __init__(self, homesub):
        self.homesub = homesub

    def remove_and_post(self, post):
        Actions.remove_post(post)
        Actions.make_comment(post,
             'This channel has been blacklisted on /r/{}.  For more details '
             'please [contact the moderators](http://www.reddit.com/message/compose?to=/r/{}&subject='
             'Why is this channel blacklisted?)  \n'
             '[^(Don\'t blame me, I\'m just a bot)](/r/centralscrutinizer)'.format(self.homesub, self.homesub))

    Historical_Scan_On_New_Database = True
    Historical_Scan_On_Startup = False #now handled by it's own object
    Scan_Sub_Period = 5 * 60 #seconds
    Pause_Period = 5 * 60 #seconds
    Scan_Error_Pause = 5 * 60 #second
    Posts_To_Load = 25
    Unread_To_Load = 10
    Mod_Update_Period = datetime.timedelta(days=1)
    Threads = 4
    Max_Retries = 3
    Retry_Multiplier = 2
    Errors_Before_Halt = 3
    Blacklist_Query_Period = 60 #seconds
    Strike_Counter_Scan_History = datetime.timedelta(days=180) #go back 180 days
    Strike_Counter_Frequency = 12 * 60 * 60 #every 12 hrs
    on_blacklist = Actions.remove_post
    on_whitelist = Actions.approve_post
    Strike_Count_Max = 3 #three strikes, and you're out
    Use_Reddit_Analytics_For_Historical_Scan = True #much more detailed history (normally)
    Historial_Scan_Period = 24 * 60 * 60 # 1 day

    def debug(self, message, text=u""):
        logging.debug(message + u"\t" + text)

    def debug_url(self, message, url=u""):
        logging.debug(message + u"\t" + url)

    def info(self, message, text=u""):
        logging.info(message + u"\t" + text)

    def info_url(self, message, url=u""):
        logging.debug(message + u"\t" + url)

class DebugPolicy(DefaultPolicy):
    def __init__(self, homesub, altsub):
        super(DebugPolicy, self).__init__(homesub)
        self.on_blacklist = lambda post: Actions.xpost(post, altsub, "blacklist")
        self.on_whitelist = lambda post: Actions.xpost(post, altsub, "whitelist")
        self.altsub = altsub

    def debug(self, message, text=u""):
        logging.debug(message + u"\t" + text )
        if __debug__:
            if text == u'':
                text = u'This has been a test of the Central Scruuuuutinizer'
            Actions.make_post_text(self.altsub, message, text)

    def debug_url(self, message, url=u''):
        logging.debug(message + u"\t" + url)
        if __debug__:
            if url.startswith(u"t3_"):
                url = u"http://redd.it/{}".format(url[3:])
            Actions.make_post_url(self.altsub, message, url)

    def info(self, message, text=u''):
        logging.info(message)
        if __debug__:
            if text == u'':
                text = u'This has been a test of the Central Scruuuuutinizer'
            Actions.make_post_text(self.altsub, message, text)

    def info_url(self, message, url=u""):
        logging.info(message)
        if __debug__:
            if url.startswith(u"t3_"):
                url = u"http://redd.it/{}".format(url[3:])
            Actions.make_post_url(self.altsub, message, url)