import RedditThread
import DataBase
import datetime
import time
import utilitymethods
import Actions
import logging
import Blacklist

class StrikeCounter(RedditThread.RedditThread):
    """
    :type policy: DefaultPolicy
    :type owner: CentralScrutinizer.CentralScrutinizer
    """

    def __init__(self, owner):
<<<<<<< HEAD
        super(StrikeCounter, self).__init__(owner, owner.policy)
=======
>>>>>>> origin/master
        self.owner = owner
        self.policy = owner.policy
        self.database_file = self.owner.database_file
        self.praw = utilitymethods.create_multiprocess_praw(self.owner.credentials)

    def scan(self):
        """

        :type post: praw.R
        :param db:
        :return:
        """
        #scan old messages, see if deleted
        with DataBase.DataBaseWrapper("test_database.db", False) as db:
            entries = db.get_reddit(date_added=datetime.datetime.now() - self.policy.Strike_Counter_Scan_History)

            #loop over entries
            stride = 100
            while len(entries):
                num_loaded = min(stride, len(entries))
                (ids, channels, domains) = zip(*entries[:num_loaded])
                ids = list(ids)
                channels = list(channels)
                domains = list(domains)
                loaded = Actions.get_by_ids(self.praw, ids)
                if not loaded:
                    logging.info("Historical posts not loaded...")
                    return

                #make sure posts retrieved
                posts = [post for post in loaded]
                if not posts:
                    logging.info("Bad post retrieve")
                    return

                #check for deleted / (not by automod)
                increment_posts = []
                delete_posts = []
                for i, post in enumerate(posts):
                    if (post.author is None or (post.author is not None and post.author.name == "[deleted]")) and post.link_flair_text is not None:
                        increment_posts.append((channels[i], domains[i]))
                        delete_posts.append(post.name)

                if len(increment_posts):
                    #add strikes
                    db.add_strike(increment_posts)
                    #remove from consideration (so we don't count them over and over)
                    db.remove_reddit(delete_posts)

                #forget old entries
                entries = entries[num_loaded:]

            #check for rule breaking channels
            channels = db.get_channels(strike_count=self.policy.Strike_Count_Max, blacklist_not_equal=Blacklist.BlacklistEnums.Blacklisted)

            #add channels to blacklist
            db.set_blacklist(channels, Blacklist.BlacklistEnums.Blacklisted)

            #remove older than scan period
            db.remove_reddit_older_than(self.policy.Strike_Counter_Scan_History.days)

    def run(self):
        while True:
            #check for pause
<<<<<<< HEAD
            if not self.check_status():
=======
            if not self.__check_status():
>>>>>>> origin/master
                break

            try:
                self.scan()
            except Exception, e:
                logging.error("Exception occured while scanning old reddit posts")
                logging.debug(str(e))
                self.__log_error()

            time.sleep(self.policy.Strike_Counter_Frequency)