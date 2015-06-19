import RedditThread
import DataBase
import datetime
import time
import utilitymethods
import Actions
import logging
import Blacklist
import traceback
import re

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
        self.sub = utilitymethods.get_subreddit(self.owner.credentials, self.praw)
        self.blacklists = self.owner.blacklists

        self.regex_list = [ re.compile(r'^(?:\*\*)?/u/([\w\d_\-\*]+)[,\s]'), #Automod / removal reason
            re.compile(r'^All apologies /u/([\w\d_\-\*]+)[,\s]'), #raddit
            re.compile(r'/u/([\w\d\*-_]+), your submission') #generic
        ]

    def check_for_submitter(self, post):
        #check comments for submitter id
        for comment in post.comments:
            if comment.author and comment.distinguished == 'moderator': #not deleted, and from mod
                for regex in self.regex_list:
                    search = regex.search(comment.body)
                    if search:
                        return search.group(1)

    def check_exception(self, post):
        try:
            #check for link flair
            if post.link_flair_css_class is None:
                return True
        except:
            pass
        try:
            #check for removal reason
            if post.removal_reason is not None:
                return True
        except:
            pass
        #check top level comments for specific keyword matches
        try:
            success = True
            #check comments
            for comment in post.comments:
                #test comment
                if not Actions.is_deleted(comment) and comment.distinguished == 'moderator':
                    #test keyword
                    for exception in self.policy.exception_list:
                        if re.search(exception, comment.body):
                            return True
            return False
        except Exception, e:
            success = False
            time.sleep(1)

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
            now = datetime.datetime.now()
            global_strike_date = now - self.policy.Strike_Counter_Global_Strike_History
            history_date = now - self.policy.Strike_Counter_Scan_History
            entries = db.get_reddit(date_added=history_date, processed=0, return_dateadded=True)
            if entries is None:
                logging.warning("No reddit entries found in database...")
                return

            new_strike_channels = []
            #loop over entries
            stride = 100
            while len(entries):
                num_loaded = min(stride, len(entries))
                (ids, channels, domains, add_dates) = zip(*entries[:num_loaded])
                ids = list(ids)
                #see if we have submitters
                have_submitters = db.have_submitter(ids)
                #any new detected usernames go here
                new_submitters_list = []
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


                #check for deleted / exceptions
                increment_posts = {}
                processed_posts = []
                excepted_posts = []
                for i, post in enumerate(posts):
                    if Actions.is_deleted(post):
                        if not have_submitters[i]:
                            val = self.check_for_submitter(post)
                            if val is not None:
                                new_submitters_list.append((val, ids[i]))
                        if not self.check_exception(post):
                            #self.policy.info(u"Deleted post found {}".format(post.name), u"channel = {}, domain = {}".format(channels[i], domains[i]))
                            if add_dates[i] > global_strike_date:
                                if not (channels[i], domains[i]) in increment_posts:
                                    increment_posts[(channels[i], domains[i])] = 1
                                else:
                                    increment_posts[(channels[i], domains[i])] += 1
                            if not (channels[i], domains[i]) in new_strike_channels:
                                new_strike_channels.append((channels[i], domains[i]))
                        else:
                            excepted_posts.append(post.name)
                        processed_posts.append(post.name)

                if len(increment_posts):
                    #add strikes
                    db.add_strike([(increment_posts[key],) + key  for key in increment_posts])
                    if __debug__:
                        logging.info("Strike Counter found {} new deleted posts...".format(len(increment_posts)))

                if len(increment_posts) or len(excepted_posts):
                    #remove from consideration (so we don't count them over and over)
                    db.set_processed(processed_posts)
                    db.set_exception(excepted_posts)


                #update submitters
                if len(new_submitters_list):
                    db.update_submitter(new_submitters_list)

                #forget old entries
                entries = entries[num_loaded:]

            #check for rule breaking channels
            channels = db.get_channels(strike_count=self.policy.Strike_Count_Max, blacklist=Blacklist.BlacklistEnums.NotFound)
            #check for user strike counts
            user_strikes = db.max_processed_from_user(new_strike_channels)
            if user_strikes:
                user_strikes = [user[1] for user in user_strikes if user[0] > self.policy.User_Strike_Count_Max]

            if channels and len(channels):
                if __debug__:
                    logging.info("{} new channels added to the blacklist".format(len(channels)))
                db.set_blacklist(channels, Blacklist.BlacklistEnums.Blacklisted, self.owner.credentials['USERNAME'],
                                 "Global strike count exceeded")

            if user_strikes and len(user_strikes):
                reason_list = ["User strike count exceeded by {}".format(user) for user in user_strikes]
                db.set_blacklist(channels, Blacklist.BlacklistEnums.Blacklisted, self.owner.credentials['USERNAME'],
                                 reason_list)

            #find posts older than scan period marked as processed
            old_strikes = db.processed_older_than(global_strike_date)
            if old_strikes is not None and len(old_strikes):
                decrement_count = {}
                for pair in old_strikes:
                    if not pair in decrement_count:
                        decrement_count[pair] = 0
                    decrement_count[pair] += 1

                #and remove them from the count
                db.subtract_strikes([(decrement_count[pair],) + pair for pair in decrement_count])

            #remove older than scan period
            db.remove_reddit_older_than(history_date)

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