"""
Scans the given sub for any new posts, processing them and checking for blacklist / delete-reposts / etc.
"""

import logging
import datetime
import Blacklist
from Blacklist import BlacklistEnums
import DataExtractors
import DataBase
import Actions
import utilitymethods
import multiprocessing
import socket
import CentralScrutinizer
import RedditThread
import time
import requests
import json
import traceback

class scan_result:
    FoundOld, DidNotFind, Error = range(3)

class SubScanner(RedditThread.RedditThread):
    def __init__(self, owner):
        """Creates a new subscanner
        :type owner: CentralScrutinizer

        :param owner: our owner! should implement a warn function, so we can warn them when too many errors are encountered
        :param credentials: a dictionary containing the credentials to be used
        :param policy: the policy on blacklist/whitelist etc.  derived from the policy class
        :param database_file: the database file to use
        """
        super(SubScanner, self).__init__(owner, owner.policy)

        self.owner = owner

        #next create a blacklist object for each
        self.extractors = self.owner.extractors
        self.blacklists = self.owner.blacklists

        #store policy
        self.policy = self.owner.policy

        #old posts stored here
        self.cached_posts = []

        #create praw
        self.praw = utilitymethods.create_multiprocess_praw(self.owner.credentials)
        self.sub = utilitymethods.get_subreddit(self.owner.credentials, self.praw)

        #self.pool = multiprocessing.Pool(processes=self.owner.policy.Threads)

        #create reddit analyics stuff if needed
        if self.policy.Use_Reddit_Analytics_For_Historical_Scan:
            self.RA_headers = {'User-Agent' : self.owner.credentials['USERAGENT']}
            self.RA_params = {"limit":500, "subreddit":self.owner.credentials["SUBREDDIT"], "fields":"name"}

        #check for empty database
        self.file = self.owner.database_file
        scan = self.policy.Historical_Scan_On_Startup
        goto = None
        if scan:
            with DataBase.DataBaseWrapper(self.file, False) as db:
                goto = db.newest_reddit_entries()
                if goto:
                    goto = list(goto[0])
                goto = Actions.get_by_ids(self.praw, goto)
                if goto:
                    goto = goto.next()
                if goto:
                    goto = datetime.datetime.fromtimestamp(goto.created_utc)
        if self.policy.Historical_Scan_On_New_Database:
            with DataBase.DataBaseWrapper(self.file, False) as db:
                if db.check_reddit_empty() and db.check_channel_empty():
                    scan = True
                    goto = datetime.datetime.now() - self.policy.Strike_Counter_Scan_History

        if scan:
            result = scan_result.Error
            count = 0
            while result == scan_result.Error and count < 5:
                result = self.historical_scan(goto)
                if result == scan_result.Error:
                    count += 1
                    time.sleep(5 * 60)
            if result == scan_result.Error:
                logging.warning("Error on historical scan, proceeding without pre-populated database")

        with DataBase.DataBaseWrapper(self.file, False) as db:
            #get previous ids
            if db.check_reddit_empty():
                self.last_seen = 0
            else:
                self.last_seen = list(db.newest_reddit_entries()[0])
                self.last_seen = Actions.get_by_ids(self.praw, self.last_seen)
                if self.last_seen is not None:
                    self.last_seen = self.last_seen.next().created_utc
                else:
                    self.last_seen = 0

        #old posts stored here
        self.cached_posts = []

        #create praw
        self.praw = utilitymethods.create_multiprocess_praw(self.owner.credentials)
        self.sub = utilitymethods.get_subreddit(self.owner.credentials, self.praw)


    def __check_cached(self, id):
        return any(i == id for i in self.cached_posts)

    def __get_blacklist(self, url):
        for b in self.blacklists:
            if b.check_domain(url):
                return b

    def __process_post_list(self, post_list):
        """processes a list of posts

        :param post_list: a list of post data of the form: [(post.created_utc, post.name, post.url, post) for post in posts if not post.is_self]
        """

        added_posts = []
        for blacklist in self.blacklists:
            temp = [(i, post[2]) for i, post in enumerate(post_list) if blacklist.check_domain(post[2])]
            if not len(temp):
                continue
            indexes, my_urls = zip(*temp)
            channel_data = [blacklist.data.channel_id(url) for url in my_urls]
            temp = [(indexes[i], channel[0]) for i, channel in enumerate(channel_data) if channel is not None]
            if not len(temp):
                #avoid zipping an empty list
                continue
            indexes, channel_ids = zip(*temp)
            check = blacklist.check_blacklist(ids=channel_ids)
            for i, enum in enumerate(check):
                index = indexes[i]
                if enum == BlacklistEnums.Blacklisted:
                    self.policy.info_url(u"Blacklist action taken on post", post_list[index][1])
                    self.policy.on_blacklist(post_list[index][3])
                    continue
                if enum == BlacklistEnums.Whitelisted:
                    self.policy.info_url(u"Whitelist action taken on post", post_list[index][1])
                    self.policy.on_whitelist(post_list[index][3])
                #if whitelisted or not found, store reddit_record
                added_posts.append((post_list[index][1], channel_ids[i], blacklist.domains[0], datetime.datetime.fromtimestamp(post_list[index][0])))

        #finally add our new posts to the reddit_record
        with DataBase.DataBaseWrapper(self.file, False) as db:
            if __debug__:
                for post in added_posts:
                    pass
                    #self.policy.info_url(u"Adding post {} to reddit_record".format(post[0]), post[0])
            db.add_reddit(added_posts)

    def historical_scan(self, goto=None):
        """Scans the sub with more intensive detection of previously found reddit posts
        Allows for mass processing of past posts
        """

        last_id = None
        if not goto:
            goto = datetime.datetime.now() - self.policy.Strike_Counter_Scan_History
        last_seen = datetime.datetime.now()
        if self.policy.Use_Reddit_Analytics_For_Historical_Scan:
            while last_seen > goto:
                if last_id:
                    self.RA_params["after"] = last_id
                try:
                    data = requests.get("http://api.redditanalytics.com/getPosts", params=self.RA_params, headers=self.RA_headers)
                    json_data = json.loads(data.content)
                    ids = [post["name"] for post in json_data["data"]]
                    with DataBase.DataBaseWrapper(self.file) as db:
                        exists = db.reddit_exists(ids)
                    ids = [ids[i] for i in range(len(ids)) if not exists[i]]
                    if not len(ids):
                        continue
                    posts = Actions.get_by_ids(self.praw, ids)
                    post_data = [(post.created_utc, post.name, post.url, post) for post in posts if not post.is_self]
                    self.__process_post_list(post_data)
                    last_id = json_data["metadata"]["oldest_id"]
                    last_seen = datetime.datetime.fromtimestamp(json_data["metadata"]["oldest_date"])
                except Exception, e:
                    logging.error(str(e))
                    if __debug__:
                        logging.error(traceback.format_exc())
                    return scan_result.Error
        else:
            posts = Actions.get_posts(self.sub, 900)
            try:
                post_data = [(post.created_utc, post.name, Actions.resolve_url(post.url), post) for post in posts if not post.is_self]
            except socket.error, e:
                if e.errno == 10061:
                    logging.critical("praw-multiprocess not started!")
                else:
                    logging.error(str(e))
                return scan_result.Error

            self.__process_post_list(post_data)

        return scan_result.FoundOld

    def scan(self, limit=10):
        """Scans the sub.

        :param limit: If None, the limit in the policy will be used
        :return: True if self.last_seen was reached, False otherwise
        """

        lim = limit if limit else self.policy.Posts_To_Load
        #first ask for posts
        posts = Actions.get_posts(self.sub, lim)
        found_old = False
        added_posts = []

        try:
            post_data = [(post.created_utc, post.name, Actions.resolve_url(post.url), post) for post in posts if not post.is_self]
        except socket.error, e:
            if e.errno == 10061:
                logging.critical("praw-multiprocess not started!")
            else:
                logging.error(str(e))
            return scan_result.Error
        #get list we need to process
        look_at = []
        for post in post_data:
            #ignore improperly resolved urls
            if post[2] is None:
                continue

            #if we've reached the last one, break
            if post[0] <= self.last_seen:
                found_old = True
                continue

            #don't look at old ones again
            if self.__check_cached(post[1]):
                continue
            self.cached_posts.append(post[1])

            look_at.append(post)

        self.__process_post_list(look_at)

        if found_old:
            return scan_result.FoundOld
        else:
            return scan_result.DidNotFind

    def __shutdown(self):
        pass

    def run(self):
        while True:
            #check for pause
            if not self.check_status():
                break

            #scan, until old id found
            try:
                result = self.scan()
            except Exception, e:
                logging.debug("Error on sub scan:\t" + str(e))
                result = scan_result.Error

            if result == scan_result.DidNotFind:
                retry_count = 0
                reached_old = False
                while reached_old == scan_result.DidNotFind and retry_count < self.policy.Max_Retries:
                    reached_old = self.scan(self.policy.Posts_To_Load * (retry_count + 1) * self.policy.Retry_Multiplier)
                    retry_count += 1
                    if reached_old == scan_result.Error:
                        result = scan_result.Error

                if retry_count == 5:
                    logging.warning("Old post made at: " + self.last_seen + " not found!  Historical data scan recommended.")

            if result == scan_result.Error:
                self.log_error()
            elif result == scan_result.FoundOld:
                #don't need old cached posts anymore
                self.cached_posts = []

            #update old id
            with DataBase.DataBaseWrapper(self.file) as db:
                if db.check_reddit_empty():
                    self.last_seen = 0
                else:
                    save = self.last_seen
                    self.last_seen = list(db.newest_reddit_entries()[0])
                    self.last_seen = Actions.get_by_ids(self.praw, self.last_seen)
                    if self.last_seen is not None:
                        self.last_seen = self.last_seen.next().created_utc
                    else:
                        self.last_seen = 0
                    #if self.last_seen != save:
                    #    self.policy.info(u"Sub Scan last_seen updated to {}".format(self.last_seen))

            #and wait
            time.sleep(self.policy.Scan_Sub_Period)
