import RedditThread
import DataBase
import datetime
import time
import utilitymethods
import Actions
import logging
import Blacklist
import traceback

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
        tally = []
        for i,item in enumerate(seq):
            tup = (seq[i], seq2[i])
            if not any(val == tup for val in tally):
                tally.append(tup)
        return [val for val in tally]

    def scan(self):
        """
        Scans the previously collected reddit posts for deleted posts
        """
        #scan old messages, see if deleted
        with DataBase.DataBaseWrapper(self.database_file, False) as db:
            entries = db.get_reddit(date_added=datetime.datetime.now() - self.policy.Strike_Counter_Scan_History, processed=0)
            if entries is None:
                logging.warning("No reddit entries found in database...")
                return

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

                #make sure channels exist
                add_channels = []
                exists = db.channel_exists([(channel, domains[i]) for i, channel in enumerate(channels)])
                for i, e in enumerate(exists):
                    if not e:
                        #pull up the url
                        add_channels.append((channels[i], domains[i]))

                #resolve all the added ids
                if add_channels:
                    if not db.add_channels(add_channels):
                        logging.info("Error adding channels to channel_record, skipping processing of posts")
                        continue #if there was an error adding the channels, don't mark as processed


                #check for deleted / (not by automod)
                increment_posts = {}
                processed_posts = []
                for i, post in enumerate(posts):
                    if (post.author is None or (post.author is not None and post.author.name == "[deleted]")) and post.link_flair_text is not None:
                        #self.policy.info(u"Deleted post found {}".format(post.name), u"channel = {}, domain = {}".format(channels[i], domains[i]))
                        if not (channels[i], domains[i]) in increment_posts:
                            increment_posts[(channels[i], domains[i])] = 1
                        else:
                            increment_posts[(channels[i], domains[i])] += 1
                        processed_posts.append(post.name)

                if len(increment_posts):
                    #add strikes
                    db.add_strike([(increment_posts[key],) + key for key in increment_posts])
                    #remove from consideration (so we don't count them over and over)
                    db.set_processed(processed_posts)
                    if __debug__:
                        logging.info("Strike Counter found {} new deleted posts...".format(len(processed_posts)))


                #forget old entries
                entries = entries[num_loaded:]

            #check for rule breaking channels
            channels = db.get_channels(strike_count=self.policy.Strike_Count_Max, blacklist=Blacklist.BlacklistEnums.NotFound)

            if channels and len(channels):
                if __debug__:
                    logging.info("{} new channels added to the blacklist".format(len(channels)))
                db.set_blacklist(channels, Blacklist.BlacklistEnums.Blacklisted)

            #remove older than scan period
            db.remove_reddit_older_than(self.policy.Strike_Counter_Scan_History.days)

            if __debug__:
                logging.info("Strike count completed successfully at {}".format(datetime.datetime.now()))
    def run(self):
        while True:
            #check for pause
            if not self.check_status():
                break

            try:
                self.scan()
            except Exception, e:
                logging.error("Exception occured while scanning old reddit posts")
                if __debug__:
                    logging.exception(e)
                self.log_error()

            time.sleep(self.policy.Strike_Counter_Frequency)

    def shutdown(self):
        pass