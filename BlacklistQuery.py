import CentralScrutinizer
import utilitymethods
import threading
import Actions
from Policies import DefaultPolicy
import logging
import datetime
import re
import textwrap
import RedditThread
import time


class BlacklistQuery(RedditThread.RedditThread):
    """
    :type policy: DefaultPolicy
    :type owner: CentralScrutinizer.CentralScrutinizer

    The blacklist query object allows mods to ask for black/whitelists through reddit
    The query syntax is as follows:

    print (black)|(white)list domain (filter)? -- print the black/whitelist for the domain for all channels matching the (optional) filter
    update-mods -- updates the modlist
    add (black)|(white)list url -- add the url of the given channel to the black/whitelist
    """

    def __init__(self, owner):
        """
        :param owner: our owner! should implement a warn function, so we can warn them when too many errors are encountered
        :param policy: the policy to follow
        """
        super(BlacklistQuery, self).__init__(owner, owner.policy)

        # get blacklists
        self.blacklists = self.owner.blacklists
        #create praw
        self.praw = utilitymethods.create_multiprocess_praw(self.owner.credentials)
        self.sub = utilitymethods.get_subreddit(self.owner.credentials, self.praw)

        #get mods
        self.mod_list = []
        self.update_mods(None)
        if not len(self.mod_list):
            logging.critical("Could not obtain mod list!")
        #last mod update
        self.last_mod_update = datetime.datetime.now()

        self.url_regex = re.compile(r"(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?")

        self.print_command = re.compile(r"^[pP]rint\b")
        self.add_command = re.compile(r"^(\+)|([aA]dd)\b")
        self.remove_command = re.compile(r"^(\-)|([rR]emove)\b")
        self.update_command = re.compile(r"^[uU]pdate[- ]*[mM]ods\b")
        self.help_command = re.compile(r"^[hH]elp(\b|$)")
        self.base_commands = [self.print_command, self.add_command, self.remove_command, self.update_command,
                              self.help_command]

        self.blist_command = re.compile(r"\b[Bb]lacklist\b")
        self.wlist_command = re.compile(r"\b[wW]hitelist\b")
        self.filters = [re.compile(r'(?<!\\)\"(.+)(?<!\\)\"'), re.compile(r"\b(\w+)\b")]

        self.short_doc_string = \
            u"""Available Commands:
                            print/add/remove/update-mods/help"""
        self.print_doc_string = \
            u"""
                            **Print** command -- returns the black/whitelist for a given domain (optional) id filter.
                            Usage:
                            subject: print whitelist/blacklist (pick one)
                            body: domain (e.g. youtube, or soundcloud.com)
                            filter (optional)
                            """
        self.add_doc_string = \
            u"""
                            **Add** command -- adds the channel associated with the url to the black/whitelist
                            Usage:
                            subject: +whitelist/blacklist (pick one)
                            body: domain  (e.g. youtube, or soundcloud.com)
                            id list  (channel ids, one per line or comma separated, each id is expected to be in quotes)

                            **OR**

                            subject: +whitelist/blacklist (pick one)
                            body: url list  (url of a video from this channel, one per line)
                            """
        self.remove_doc_string = \
            u"""
                            **Remove** command -- removes the channel associated with the domain and id (or optionally url) from the black/whitelist
                            Usage:
                            subject: -whitelist/blacklist
                            body: domain  (e.g. youtube, or soundcloud.com)
                            id list  (channel ids, one per line or comma separated, each id is expected to be in quotes)

                            **OR**

                            subject: -whitelist/blacklist (pick one)
                            body: url list  (url of a video from this channel, one per line)
                            """
        self.update_doc_string = \
            u"""
                            **Update-mods** command -- updates the valid mod list, this is done automatically but can be manually updated
                            Usage:
                            subject: update-mods
                            """

        self.help_doc_string = \
            u"""
                            **Help** command -- prints the documentation, see github for more examples
                            subject: help
                            body: domains (optional) prints list of available domains
                            command (optional) print the help specific for a command
                            """

        self.domains = list(set(
            d.replace(u".com", u"").replace(u"http://", u"").replace(u"https://", u"").replace(u"www.", u"") for b in
            self.blacklists for d in b.domains))
        self.domain_doc_string = u"Available Domains:"
        for domain in self.domains:
            self.domain_doc_string += u"  \n" + domain

        self.doc_strings = [self.short_doc_string, self.print_doc_string, self.add_doc_string, self.remove_doc_string,
                            self.update_doc_string, self.help_doc_string, self.domain_doc_string]
        self.doc_strings = [textwrap.dedent(s) for s in self.doc_strings]
        self.doc_strings = [s.replace(u"\n", u"  \n") for s in self.doc_strings]
        self.doc_string = u"  \n".join(self.doc_strings)
        self.doc_string = textwrap.dedent(self.doc_string)

        self.line_splitter = re.compile("  |\n")
        self.quote_splitter = re.compile("\"([^\"]+)\",")
        self.quote_extractor = re.compile("^\"([^\"]+)\"$")

        self.message_cache = []

    def __shutdown(self):
        pass

    def update_mods(self, author):
        try:
            mlist = [mod.name for mod in Actions.get_mods(self.praw, self.sub)]
            if mlist is None or not len(mlist):
                return False
            # only update if it's valid
            self.mod_list = mlist
            self.last_mod_update = datetime.datetime.now()
            if author is not None:
                Actions.send_message(self.praw, author, u"RE: Modlist update", u"Success!")
            return True
        except Exception, e:
            self.policy.debug(u"Error updating mod_list")
            if author is not None:
                Actions.send_message(self.praw, author, u"RE: Modlist update", u"Error encountered, please try again later.")
            logging.critical(u"Could not update moderator list!")
            logging.debug(str(e))
            return False

    def __print(self, author, subject, text):
        """
        subject: print whitelist/blacklist (pick one)
        body: domain (e.g. youtube, or soundcloud.com)
        filter (optional)
        """

        # get black/whitelist
        blacklist = None
        result = self.blist_command.search(subject)
        if result:
            blacklist = True
        result = self.wlist_command.search(subject)
        if result:
            blacklist = False
        if blacklist is None:
            Actions.send_message(self.praw, author, u"RE: {}list print".format(u"Black" if blacklist else u"White"),\
                                 u"Could not determine blacklist/whitelist from subject line  \n\
                                 Subject: {}".format(subject))
            return False

        #check that we have text
        lines = [l for l in self.line_splitter.split(text) if len(l)]
        if not len(lines):
            Actions.send_message(self.praw, author, u"RE: {}list print".format(u"Black" if blacklist else u"White"),\
                                 u"No domain specified in text:  \n{}".format(text))
            return False

        blist = None
        #get domain
        for b in self.blacklists:
            if b.check_domain(lines[0]):
                blist = b
                break
        if not blist:
            Actions.send_message(self.praw, author, u"RE: {}list print".format(u"Black" if blacklist else u"White"),\
                                 u"Could not find valid domain specified in text:  \n{}".format(lines[0]))
            return False

        myfilter = None
        #get filter
        if len(lines) > 1:
            filters = [f.search(lines[1]) for f in self.filters]
            filters = [f for f in filters if f]
            if len(filters):
                result = filters[0]
                if result:
                    result = result.groups()
                    if len(result):
                        myfilter = result[0]

        if blacklist:
            results = blist.get_blacklisted_channels(myfilter)
        else:
            results = blist.get_whitelisted_channels(myfilter)
        if len(results):
            results = sorted([result[0] for result in results])
        else:
            Actions.send_message(self.praw, author, subject, u"Error querying blacklist, please submit bug report to \
                                 /r/centralscrutinizer")
            return False
        out_str = u"\n".join(results)
        subject = u"RE:{}list print".format(u"black" if blacklist else u"white")
        subject += u" w/ domain " + blist.domains[0]
        if myfilter:
            subject += u" and filter " + myfilter
        Actions.send_message(self.praw, author, subject, u"Results:  \n" + out_str)
        return True


    def __add_remove(self, author, subject, text, add):
        #get black/whitelist
        blacklist = None
        result = self.blist_command.search(subject)
        if result:
            blacklist = True
        result = self.wlist_command.search(subject)
        if result:
            blacklist = False
        if blacklist is None:
            Actions.send_message(self.praw, author, u"RE: Black/whitelist add/removal",\
                                 u"Could not determine blacklist/whitelist from subject line",\
                                 u"Subject: {}".format(subject))
            return False

        lines = [l for l in self.line_splitter.split(text) if len(l)]
        check = lines[0]
        blist = None
        url_list = None
        #test the first line to see if it's a url, or just a domain
        for b in self.blacklists:
            if b.check_domain(check):
                #store b
                blist = b
                #found correct blacklist, but could still be just the domain, try to resolve
                result = b.data.channel_id(check)
                if result is not None:
                    url_list = True
                else:
                    url_list = False
                break

        #now check that we have a blacklist and url_list defined
        if blist is None:
            Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white",\
                u"addition" if add else u"removal"), u"Could not determine valid domain from:  \n{}".format(lines[0]))
            return False

        #check that if we do not have a url list, we indeed have a domain and other entries to add
        if url_list and len(lines) == 1:
            Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white",\
                u"addition" if add else u"removal"), u"Invalid format detected, must have at least one channel id to {}\
                from {}list for domain {}".format(u"add" if add else u"remove", u"black" if blacklist else u"white",\
                check))
            return False

        entries = lines if url_list else lines[1:]
        invalid = []
        if not url_list:
            real_entries = []
            #if we have an id list, we have to see if they're comma separated
            for entry in entries:
                val = self.quote_splitter.split(entry)
                if val:
                    real_entries.extend([v.strip() for v in val if v and len(v.strip())])
                else:
                    val = self.quote_extractor.match(entry)
                    if not val:
                        invalid.append(entry)
                    else:
                        real_entries.extend(val.group(1))
                if self.quote_extractor.match(real_entries[-1]):
                    real_entries[-1] = self.quote_extractor.match(real_entries[-1]).group(1)
            #copy back
            entries = real_entries[:]

        if blacklist:
            if add:
                if url_list:
                    invalid += b.add_blacklist_urls(entries)
                else:
                    invalid += b.add_blacklist(entries)
            else:
                if url_list:
                    invalid += b.remove_blacklist_urls(entries)
                else:
                    invalid += b.add_blacklist(entries)
        else:
            if add:
                if url_list:
                    invalid += b.add_whitelist_urls(entries)
                else:
                    invalid += b.add_whitelist(entries)
            else:
                if url_list:
                    invalid += b.remove_whitelist_urls(entries)
                else:
                    invalid += b.add_whitelist(entries)

        if invalid is not None and len(invalid):
            retstr = u"Invalid entries detected:  \n"
            if url_list:
                retstr += u"  \n".join(invalid)
            else:
                retstr += u"  \n".join([u"id = {}, domain = {}  \n".format(id, check) for id in invalid])
            self.policy.debug(u"Invalid entry detected for message", retstr)
            Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white",\
                u"addition" if add else u"removal"), retstr)
            return False

        Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white",\
                u"addition" if add else u"removal"), u"Success!")
        return True

    def is_cached(self, id):
        return id in self.message_cache

    def process_message(self, message):
        """
        Handles the processing of unread messages, allows for easier testing
        """
        result = None
        # valid author check
        if any(name == message.author.name for name in self.mod_list) and not self.is_cached(message.id):
            subject = message.subject
            text = message.body
            #check that it matches one of the basic commands
            matches = [bc for bc in self.base_commands if bc.search(subject)]
            if len(matches) == 1:
                #take care of add /removes
                if matches[0] == self.add_command:
                    self.__add_remove(message.author.name, subject, text, True)
                elif matches[0] == self.remove_command:
                    self.__add_remove(message.author.name, subject, text, False)
                #update mods
                elif matches[0] == self.update_command:
                    self.update_mods(message.author.name)
                #print query
                elif matches[0] == self.print_command:
                    result = self.__print(text, message.author.name)
                #help query
                elif matches[0] == self.help_command:
                    Actions.send_message(self.praw, message.author.name, u"RE:{}".format(message.subject),
                                         self.doc_string)

            if len(matches) != 1:
                Actions.send_message(self.praw, message.author.name, u"RE:{}".format(message.subject),
                                     u"Sorry, I did not recognize your query.  \n".format(text) + self.short_doc_string)

        self.message_cache.append(message.id)
        #don't need to see this again
        message.mark_as_read()
        return result


    def run(self):
        while True:
            if not self.check_status():
                break

            # see if we need to update mods
            if datetime.datetime.now() - self.last_mod_update > self.policy.Mod_Update_Period:
                if __debug__:
                    logging.info(u"Blacklist Query updating mod list...")
                self.update_mods()
                if __debug__:
                    logging.info(u"Modlist updated to: {}".format(u", ".join(self.mod_list)))

            #get unread
            unread = Actions.get_unread(self.praw, limit=self.policy.Unread_To_Load)
            try:
                messages = [message for message in unread]
                if __debug__:
                    logging.info(u"Blacklist query processing {} messages...".format(len(messages)))
                for message in messages:
                    self.process_message(message)
                    if __debug__:
                        logging.info(u"Blacklist query processing message:\n{}".format(message.body))
            except Exception, e:
                logging.error(u"Error on retrieving unread messages")
                logging.debug(str(e))
                self.log_error()

            self.message_cache = []

            #and wait (min of 30s to prevent return of cached answers on default PRAW install)
            time.sleep(max(self.policy.Blacklist_Query_Period, 30))
