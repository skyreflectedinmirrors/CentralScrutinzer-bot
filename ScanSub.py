"""
Scans the given sub for any new posts, processing them and checking for blacklist / delete-reposts / etc.
"""

import logging
import datetime
from Blacklist import BlacklistEnums
import DataBase
import Actions
import utilitymethods
import socket
import CentralScrutinizer
import RedditThread
import time
import requests
import json


class scan_result:
    FoundOld, DidNotFind, Error = range(3)

    @staticmethod
    def to_string(variable):
        if variable == scan_result.FoundOld:
            return "Found Old"
        if variable == scan_result.DidNotFind:
            return "Not Found"
        if variable == scan_result.Error:
            return "Error"
        return "Unknown"


class SubScanner(RedditThread.RedditThread):
    def __init__(self, owner, skip_scan = False):
        """Creates a new subscanner
        :type owner: CentralScrutinizer

        :param owner: our owner! should implement a warn function, so we can warn them when too many errors are encountered
        :param credentials: a dictionary containing the credentials to be used
        :param policy: the policy on blacklist/whitelist etc.  derived from the policy class
        :param database_file: the database file to use
        """
        super(SubScanner, self).__init__(owner, owner.policy)

        self.descriptor = "Subscan"
        self.owner = owner

        # next create a blacklist object for each
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
            self.RA_headers = {'User-Agent': self.owner.credentials['USERAGENT']}
            self.RA_params = {"limit": 500, "subreddit": self.owner.credentials["SUBREDDIT"], "fields": "name"}

        #check for empty database
        self.file = self.owner.database_file
        scan = self.policy.Historical_Scan_On_Startup
        goto = None
        if scan:
            with DataBase.DataBaseWrapper(self.file, False) as db:
                goto = db.newest_reddit_entries()
                if goto is not None and len(goto):
                    goto = goto[0]
                    goto -= datetime.timedelta(days=1)
        if self.policy.Historical_Scan_On_New_Database:
            with DataBase.DataBaseWrapper(self.file, False) as db:
                if db.check_reddit_empty() and db.check_channel_empty():
                    scan = True
                    goto = datetime.datetime.now() - self.policy.Strike_Counter_Scan_History

        if scan and not skip_scan:
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
                self.last_seen = datetime.datetime.now()
            else:
                self.last_seen = db.newest_reddit_entries()[0]


        #old posts stored here
        self.cached_posts = []

        #create praw
        self.praw = utilitymethods.create_multiprocess_praw(self.owner.credentials)
        self.sub = utilitymethods.get_subreddit(self.owner.credentials, self.praw)

        self.scan_period = self.policy.Scan_Sub_Period


    def __check_cached(self, id):
        return any(i == id for i in self.cached_posts)

    def __get_blacklist(self, url):
        for b in self.blacklists:
            if b.check_domain(url):
                return b

    def __process_post_list(self, post_list):
        """processes a list of posts

        :param post_list: a list of post data of the form: [(post.created_utc, post.name, post.url, post) for post in posts if not post.is_self]
        :returns: A boolean for each post, each entry is True if processed, false if the post domain was not matched
        """

        found_domain = [False for post in post_list]
        added_posts = []
        #sort by creation date so that the last post
        post_list.sort(key=lambda x: x[0])
        for blacklist in self.blacklists:
            temp = [(i, post[2]) for i, post in enumerate(post_list) if blacklist.check_domain(post[2])]
            if not len(temp):
                continue
            indexes, my_urls = zip(*temp)
            channel_data = [blacklist.data.channel_id(url) for url in my_urls]
            temp = [(indexes[i], channel[0]) for i, channel in enumerate(channel_data) if channel is not None]
            if not len(temp):
                # avoid zipping an empty list
                continue
            indexes, channel_ids = zip(*temp)
            #mark the posts as found/processed
            for index in indexes:
                found_domain[index] = True
            check = blacklist.check_blacklist(ids=channel_ids)
            for i, enum in enumerate(check):
                index = indexes[i]
                if enum == BlacklistEnums.Blacklisted:
                    # self.policy.info_url(u"Blacklist action taken on post", post_list[index][1])
                    self.policy.on_blacklist(post_list[index][3])
                if enum == BlacklistEnums.Whitelisted:
                    # self.policy.info_url(u"Whitelist action taken on post", post_list[index][1])
                    self.policy.on_whitelist(post_list[index][3])
                # add post to record
                added_posts.append((post_list[index][1], channel_ids[i], blacklist.domains[0],
                                    datetime.datetime.fromtimestamp(post_list[index][0])))

        # finally add our new posts to the reddit_record
        with DataBase.DataBaseWrapper(self.file, False) as db:
            db.add_reddit(added_posts)

        return found_domain

    def get_historial_posts(self, goto):
        """Scans the sub with more intensive detection of previously found reddit posts
        Allows for mass processing of past posts
        """
        last_id = None
        last_seen = datetime.datetime.now()
        posts = []
        if self.policy.Use_Reddit_Analytics_For_Historical_Scan:
            while last_seen > goto:
                if last_id:
                    self.RA_params["after"] = last_id
                try:
                    data = requests.get("http://api.redditanalytics.com/getPosts", params=self.RA_params,
                                        headers=self.RA_headers)
                    json_data = json.loads(data.content)
                    ids = [post["name"] for post in json_data["data"]]
                    with DataBase.DataBaseWrapper(self.file) as db:
                        exists = db.reddit_exists(ids)
                    if exists is not None:
                        ids = [ids[i] for i in range(len(ids)) if not exists[i]]
                    else:
                        return None
                    if not len(ids):
                        continue
                    temp_posts = Actions.get_by_ids(self.praw, ids)
                    if temp_posts is not None:
                        posts.extend(temp_posts)
                    else:
                        return None
                    last_id = json_data["metadata"]["oldest_id"]
                    last_seen = datetime.datetime.fromtimestamp(json_data["metadata"]["oldest_date"])
                except ValueError, e:
                    if str(e).startswith("No JSON object"):
                        logging.error("Reddit-Analytics is down, retrying historical scan after pause...")
                    else:
                        logging.error(str(e))
                        if __debug__:
                            logging.exception(e)
                    return None
                except Exception, e:
                    logging.error(str(e))
                    if __debug__:
                        logging.exception(e)
                    return None
        else:
            posts = Actions.get_posts(self.sub, 900)
            if posts is None:
                return scan_result.Error

        return posts

    def historical_scan(self, goto):
        posts = self.get_historial_posts(goto)
        if posts is not None and len(posts):
            post_data = [(post.created_utc, post.name, post.url, post) for post in posts if not post.is_self]
            self.__process_post_list(post_data)
            return scan_result.FoundOld
        return scan_result.Error

    def get_posts(self, lim):
        return Actions.get_posts(self.sub, lim)

    def scan(self, limit=None):
        """Scans the sub.

        :param limit: If None, the limit in the policy will be used
        :return: True if self.last_seen was reached, False otherwise
        """

        lim = limit if limit else self.policy.Posts_To_Load
        # first ask for posts
        posts = self.get_posts(lim)
        found_old = False

        try:
            #Actions.resolve_url(post.url)
            post_data = [(post.created_utc, post.name, post.url, post) for post in posts if
                         not post.is_self]
        except socket.error, e:
            if e.errno == 10061:
                logging.critical("praw-multiprocess not started!")
            else:
                logging.error(str(e))
            return scan_result.Error
        except Exception, e:
            logging.critical("Unknown exception occured while obtaining post data for {}".format(self.descriptor))
            logging.exception(e)
            return scan_result.Error

        with DataBase.DataBaseWrapper(self.file, False) as db:
            exists = db.reddit_exists([post[1] for post in post_data])

        if exists is None:
            logging.error("Could not find reddit_exists for {}".format(self.descriptor))
            return scan_result.Error

        try:
            #get list we need to process
            look_at = []
            for i, post in enumerate(post_data):
                #ignore improperly resolved urls
                if post[2] is None:
                    continue

                #if we've seen this before, skip
                if exists[i]:
                    continue

                if datetime.datetime.fromtimestamp(post[0]) < self.last_seen - \
                        datetime.timedelta(seconds=2 * self.scan_period):
                    found_old = True

                #don't look at old ones again
                if self.__check_cached(post[1]):
                    continue
                self.cached_posts.append(post[1])

                look_at.append(post)
        except Exception, e:
            logging.critical("Unknown error encountered during {}'s scan".format(self.descriptor))
            logging.exception(e)
            return scan_result.Error


        found_domain = self.__process_post_list(look_at)
        found_old &= found_domain.count(True) == 0 or len(look_at) == 0

        if found_old:
            return scan_result.FoundOld
        else:
            return scan_result.DidNotFind

    def shutdown(self):
        pass

    def run(self):
        while True:
            # check for pause
            try:
                if not self.check_status():
                    break
            except Exception, e:
                logging.critical("Unknown exception occured during {}'s status check".format(self.descriptor))
                logging.exception(e)

            #scan, until old id found
            try:
                result = self.scan(self.policy.Posts_To_Load)
            except Exception, e:
                logging.debug("Error on sub scan:\t" + str(e))
                result = scan_result.Error

            try:
                retry_count = 0
                if result == scan_result.DidNotFind:
                    reached_old = result
                    while reached_old == scan_result.DidNotFind and retry_count < self.policy.Max_Retries:
                        reached_old = \
                            self.scan(self.policy.Posts_To_Load * (retry_count + 1) * self.policy.Retry_Multiplier)
                        retry_count += 1
                        if reached_old == scan_result.Error:
                            result = scan_result.Error

                    result = reached_old
                    if retry_count == 5:
                        logging.warning(
                            "Old post made at: " + self.last_seen + " not found!  Historical data scan recommended.")

                if result == scan_result.Error:
                    self.log_error()
                elif result == scan_result.FoundOld:
                    #don't need old cached posts anymore, remove ones more than two periods back
                    self.cached_posts = self.cached_posts[:2 * self.policy.Posts_To_Load * (retry_count + 1)]

                if __debug__:
                    logging.info("{} completed at {} with result {}".format(self.descriptor, datetime.datetime.now(),
                                                                                 scan_result.to_string(result)))

                #update old id
                with DataBase.DataBaseWrapper(self.file, False) as db:
                    if db.check_reddit_empty():
                        self.last_seen = datetime.datetime.now()
                    else:
                        latest_entry = db.newest_reddit_entries()
                        if latest_entry is not None:
                            self.last_seen = latest_entry[0]
                        else:
                            logging.critical("Error loading newest database entry")

                #and wait
                time.sleep(self.scan_period)
            except Exception, e:
                logging.critical("Unknown exception occured during {}".format(self.descriptor))
                logging.exception(e)


class ModLogScanner(SubScanner):
    def __init__(self, owner):
        super(ModLogScanner, self).__init__(owner, True)
        self.descriptor = "Modlog Scanner"

    def get_posts(self, lim):
        # first ask for posts
        try:
            posts = self.sub.get_mod_log(action="removelink", limit=lim)
            posts = [posts.next().target_fullname for i in range(lim)]
            return Actions.get_by_ids(self.praw, posts)
        except Exception, e:
            logging.error(str(e))
            if __debug__:
                logging.exception(e)

class HistoricalScanner(SubScanner):
    def __init__(self, owner):
        super(HistoricalScanner, self).__init__(owner, True)
        self.descriptor = "Historical Scanner"
        self.scan_period = owner.policy.Historial_Scan_Period

    def get_posts(self, lim):
        try:
            return self.get_historial_posts(self.last_seen - datetime.timedelta(seconds=2 * self.scan_period))
        except Exception, e:
            logging.error("Error loading historical posts")
            logging.exception(e)
