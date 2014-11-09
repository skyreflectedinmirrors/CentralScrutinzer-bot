import RedditThread
import DataBase
import datetime
import time
import utilitymethods
import Actions
import logging
import Blacklist
import multiprocessing
from collections import defaultdict

class StrikeCounter(RedditThread.RedditThread):
    """
    :type policy: DefaultPolicy
    :type owner: CentralScrutinizer.CentralScrutinizer
    """

    def __init__(self, owner):
        super(StrikeCounter, self).__init__(owner, owner.policy)
        self.owner = owner
        self.policy = owner.policy
        self.database_file = self.owner.database_file
        self.praw = utilitymethods.create_multiprocess_praw(self.owner.credentials)
        self.blacklists = self.owner.blacklists

    def __get_unique(self, seq, seq2):
        tally = defaultdict(list)
        for i,item in enumerate(seq):
            tally[(item, seq2[i])].append(i)
        return [(key, locs[0]) for key, locs in tally.items()
                                if len(locs) == 1]

    def scan(self):
        """

        :type post: praw.R
        :param db:
        :return:
        """
        #scan old messages, see if deleted
        with DataBase.DataBaseWrapper(self.database_file, False) as db:
            entries = db.get_reddit(date_added=datetime.datetime.now() - self.policy.Strike_Counter_Scan_History, return_channel_url=True, processed=0)
            if entries is None:
                logging.warning("No reddit entries found in database...")
                return

            #loop over entries
            stride = 100
            while len(entries):
                num_loaded = min(stride, len(entries))
                (ids, channels, domains, urls) = zip(*entries[:num_loaded])
                ids = list(ids)
                channels = list(channels)
                domains = list(domains)
                urls = list(urls)
                loaded = Actions.get_by_ids(self.praw, ids)
                if not loaded:
                    logging.info("Historical posts not loaded...")
                    return

                #make sure posts retrieved
                posts = [post for post in loaded]
                if not posts:
                    logging.info("Bad post retrieve")
                    return

                #make sure channels exist
                add_channels = []
                indexes = []
                unique_channels = self.__get_unique(channels, domains)
                exists = db.channel_exists([channel[0] for channel in unique_channels])
                for i, e in enumerate(exists):
                    if not e:
                        #pull up the url
                        indexes.append(unique_channels[i][1])

                #resolve all the added ids
                if indexes:
                    for blacklist in self.blacklists:
                        my_indexes = [i for i in indexes if blacklist.check_domain(urls[i])]
                        if not len(my_indexes):
                            continue
                        for index in my_indexes:
                            add_channels.append((channels[index], urls[index], domains[index]))
                    if __debug__:
                        pass
                        #for i, index in enumerate(indexes):
                            #self.policy.info(u"Adding {} to channel_record".format(channels[index]), u"channel={}, domain = {}".format(channels[index], domains[index]))
                    db.add_channels(add_channels)


                #check for deleted / (not by automod)
                increment_posts = []
                processed_posts = []
                for i, post in enumerate(posts):
                    if (post.author is None or (post.author is not None and post.author.name == "[deleted]")) and post.link_flair_text is not None:
                        self.policy.info(u"Deleted post found {}".format(post.name), u"channel = {}, domain = {}".format(channels[i], domains[i]))
                        increment_posts.append((channels[i], domains[i]))
                        processed_posts.append(post.name)

                if len(increment_posts):
                    #add strikes
                    db.add_strike(increment_posts)
                    #remove from consideration (so we don't count them over and over)
                    db.set_processed(processed_posts)

                #forget old entries
                entries = entries[num_loaded:]

            #check for rule breaking channels
            channels = db.get_channels(strike_count=self.policy.Strike_Count_Max, blacklist_not_equal=Blacklist.BlacklistEnums.Blacklisted)

            if channels and len(channels):
                if __debug__:
                    for i, channel in enumerate(channels):
                        self.policy.info(u"Adding channel to blacklist", u"channel={}, domain = {}".format(channel, domains[i]))
                #add channels to blacklist
                db.set_blacklist(channels, Blacklist.BlacklistEnums.Blacklisted)

            #remove older than scan period
            db.remove_reddit_older_than(self.policy.Strike_Counter_Scan_History.days)

    def run(self):
        while True:
            #check for pause
            if not self.check_status():
                break

            try:
                self.scan()
            except Exception, e:
                logging.error("Exception occured while scanning old reddit posts")
                logging.debug(str(e))
                self.log_error()

            time.sleep(self.policy.Strike_Counter_Frequency)