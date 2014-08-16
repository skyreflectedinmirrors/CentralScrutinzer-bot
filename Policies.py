"""
Policies controlling the various actions and responses of the Central Scruitinzer
"""

import Actions
import datetime

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
    """
    Historical_Scan_On_New_Database = True
    Scan_Sub_Period = 5 * 60 #seconds
    Pause_Period = 2 * 60 #seconds
    Posts_To_Load = 10
    Unread_To_Load = 10
    Mod_Update_Period = datetime.timedelta(days=1)
    Threads = 4
    Max_Retries = 3
    Retry_Multiplier = 2
    Errors_Before_Halt = 3
    Blacklist_Query_Period = 3 * 60 #seconds
    on_blacklist = Actions.remove_post
    on_whitelist = Actions.approve_post

class DebugPolicy(DefaultPolicy):
    def __init__(self, altsub):
        self.on_blacklist = lambda post: Actions.xpost(post, altsub, "blacklist")
        self.on_whitelist = lambda post: Actions.xpost(post, altsub, "whitelist")
        self.Historical_Scan_On_New_Database = False
