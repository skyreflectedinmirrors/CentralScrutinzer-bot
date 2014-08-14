"""
Policies controlling the various actions and responses of the Central Scruitinzer
"""

import Actions

class DefaultPolicy(object):
    """
    Historical_Scan_On_New_Database -- if true the bot will populate the database based on the last 900 (available) posts
    Scan_Sub_Period -- the wait period (in seconds) between subreddit scans
    Pause_Period -- the wait period (in seconds) when the bot is paused
    Posts_To_Load -- how many posts to load on a normal scan
    Threads -- how many multiprocessing threads may be used
    Max_Retries -- how many retries to use
    Retry_Multiplier -- the post multiplier for each retry
    on_blacklist -- the action to take for a blacklisted post
    on_whitelist -- the action to take for a blacklisted post
    """
    Historical_Scan_On_New_Database = True
    Scan_Sub_Period = 5 * 60 #seconds
    Pause_Period = 2 * 60 #seconds
    Posts_To_Load = 10
    Threads = 4
    Max_Retries = 3
    Retry_Multiplier = 2
    on_blacklist = Actions.remove_post
    on_whitelist = Actions.approve_post

class DebugPolicy(DefaultPolicy):
    def __init__(self, altsub):
        self.on_blacklist = lambda post: Actions.xpost(post, altsub, "blacklist")
        self.on_whitelist = lambda post: Actions.xpost(post, altsub, "whitelist")
        self.Historical_Scan_On_New_Database = False
