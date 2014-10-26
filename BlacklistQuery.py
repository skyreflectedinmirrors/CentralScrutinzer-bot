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
        self.update_mods()
        if not len(self.mod_list):
            logging.critical("Could not obtain mod list!")
        #last mod update
        self.last_mod_update = datetime.datetime.now()

        self.url_regex = re.compile(r"(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?")

        self.print_command = re.compile(r"^[pP]rint\b")
        self.add_command = re.compile(r"^[aA]dd\b")
        self.remove_command = re.compile(r"^[rR]emove\b")
        self.update_command = re.compile(r"^[uU]pdate[- ][mM]ods\b")
        self.help_command = re.compile(r"^[hH]elp(\b|$)")
        self.base_commands = [self.print_command, self.add_command, self.remove_command, self.update_command,
                              self.help_command]

        self.domain_match = re.compile(r"(\w+)\b")

        self.blist_command = re.compile(r"\b[Bb]lacklist\b")
        self.wlist_command = re.compile(r"\b[wW]hitelist\b")
        self.filters = [re.compile(r'(?<!\\)\"(.+)(?<!\\)\"'), re.compile(r"\b(\w+)\b")]

        self.short_doc_string = \
            """Available Commands:
                            print/add/remove/update-mods/help"""
        self.print_doc_string = \
            """
                            **Print** command -- returns the black/whitelist for a given domain (optional) id filter.
                            Usage:
                            print
                            whitelist/blacklist (pick one)
                            domain (e.g. youtube, or soundcloud.com)
                            filter (optional)
                            """
        self.add_doc_string = \
            """
                            **Add** command -- adds the channel associated with the url to the black/whitelist
                            Usage:
                            add
                            whitelist/blacklist (pick one)
                            url
                            """
        self.remove_doc_string = \
            """
                            **Remove** command -- removes the channel associated with the domain and id (or optionally url) from the black/whitelist
                            Usage:
                            remove
                            whitelist/blacklist (pick one)
                            id  (channel id)
                            domain  (e.g. youtube, or soundcloud.com)

                            **OR**

                            remove
                            whitelist/blacklist (pick one)
                            url  (url of a video etc. from this channel)
                            """
        self.update_doc_string = \
            """
                            **Update-mods** command -- updates the valid mod list, this is done automatically but can be manually updated
                            Usage:
                            update-mods
                            """

        self.help_doc_string = \
            """
                            **Help** command -- prints the documentation, see github for more examples
                            help
                            domains (optional) prints list of available domains
                            command (optional) print the help specific for a command
                            """

        self.domains = list(set(
            d.replace(".com", "").replace("http://", "").replace("https://", "").replace("www.", "") for b in
            self.blacklists for d in b.domains))
        self.domain_doc_string = "Available Domains:"
        for domain in self.domains:
            self.domain_doc_string += "  \n" + domain

        self.doc_strings = [self.short_doc_string, self.print_doc_string, self.add_doc_string, self.remove_doc_string,
                            self.update_doc_string, self.help_doc_string, self.domain_doc_string]
        self.doc_strings = [s.replace("\n", "  \n") for s in self.doc_strings]
        self.doc_string = "  \n".join(self.doc_strings)
        self.doc_string = textwrap.dedent(self.doc_string)

        self.splitter = re.compile("  |\n")

        self.message_cache = []

    def __shutdown(self):
        pass

    def update_mods(self):
        try:
            mlist = [mod.name for mod in Actions.get_mods(self.praw, self.sub)]
            # only update if it's valid
            self.mod_list = mlist
            return True
        except Exception, e:
            logging.critical("Could not update moderator list!")
            logging.debug(str(e))
            return False

    def __print(self, text, user):
        lines = [l for l in self.splitter.split(text) if len(l)]
        """
        print
        whitelist/blacklist (pick one)
        domain (e.g. youtube, or soundcloud.com)
        filter (optional)
        """

        if len(lines) < 3 or len(lines) > 4:
            return "unrecognized"

        # get black/whitelist
        blacklist = None
        result = self.blist_command.search(lines[1])
        if result:
            blacklist = True
        result = self.wlist_command.search(lines[1])
        if result:
            blacklist = False
        if blacklist is None:
            return "no blist"

        #get domain
        result = self.domain_match.search(lines[2])
        if not result:
            return "no domain"
        result = result.groups()
        if not len(result):
            return "no domain"
        domain = result[0]
        if not any(d == domain or d.startswith(domain) for d in self.domains):
            return "invalid domain"

        myfilter = None
        #get filter
        if len(lines) > 3:
            filters = [f.search(lines[3]) for f in self.filters]
            filters = [f for f in filters if f]
            if len(filters):
                result = filters[0]
                if result:
                    result = result.groups()
                    if len(result):
                        myfilter = result[0]

        the_list = [b for b in self.blacklists if any(domain in d for d in b.domains)]
        if len(the_list):
            if blacklist:
                results = the_list[0].get_blacklisted_channels(myfilter)
            else:
                results = the_list[0].get_whitelisted_channels(myfilter)
            if len(results):
                results = sorted([result[0] for result in results])
            out_str = "\n".join(results)
            subject = "RE:{}list query".format("black" if blacklist else "white")
            subject += " w/ domain " + domain
            if myfilter:
                subject += " and filter " + myfilter
            Actions.send_message(self.praw, user, subject, "Results:\n" + out_str)
            return ""
        else:
            return "error"


    def __add_remove(self, text, add):
        lines = [l for l in self.splitter.split(text) if len(l)]
        # line structure
        """
        add
        whitelist/blacklist (pick one)
        url

        remove
        whitelist/blacklist (pick one)
        id  (channel id)
        domain  (e.g. youtube, or soundcloud.com)

        or

        remove
        whitelist/blacklist (pick one)
        url
        """

        if add:
            if len(lines) != 3:
                return "unknown"
        else:
            if len(lines) < 3 or len(lines) > 4:
                return "unknown"

        #get black/whitelist
        blacklist = None
        result = self.blist_command.search(lines[1])
        if result:
            blacklist = True
        result = self.wlist_command.search(lines[1])
        if result:
            blacklist = False
        if blacklist is None:
            return "no blist"

        url = None
        id = None
        #check for url
        url = self.url_regex.search(lines[2])
        if add and url and len(url.groups()):
            url = lines[2][url.span()[0]:url.span()[1]]
        elif add:
            return "unknown"
        elif len(lines) == 3 and url and len(url.groups()):
            url = lines[2][url.span()[0]:url.span()[1]]
        elif len(lines) == 4:
            id = lines[2].strip()
            domain = lines[3].strip().lower()
        else:
            return "unknown"

        found = False
        valid = False
        for b in self.blacklists:
            check = url if url else domain
            if blacklist:
                found = found or b.check_domain(check)
            else:
                found = found or b.check_domain(check)
            if found:
                if blacklist:
                    if add:
                        invalid = b.add_blacklist(url)
                    else:
                        if url:
                            invalid = b.remove_blacklist_url(url)
                        else:
                            invalid = b.remove_blacklist(id)
                else:
                    if add:
                        invalid = b.add_whitelist(url)
                    else:
                        if url:
                            invalid = b.remove_whitelist_url(self, url)
                        else:
                            invalid = b.remove_whitelist(id)
                break

        if not found:
            return "invalid domain"
        if invalid:
            retstr = "invalid entry: for "
            if url:
                retstr += url
            else:
                retstr += "id = {}, domain = {}".format([id, domain])
            return retstr
        return ""

    def is_cached(self, id):
        return id in self.message_cache

    def process_message(self, message):
        """
        Handles the processing of unread messages, allows for easier testing
        """
        result = None
        # valid author check
        if any(name == message.author.name for name in self.mod_list) and not self.is_cached(message.id):
            text = message.body
            #check that it matches one of the basic commands
            matches = [bc for bc in self.base_commands if bc.search(text)]
            if len(matches) == 1:
                #take care of add /removes
                if matches[0] == self.add_command:
                    result = self.__add_remove(text, True)
                elif matches[0] == self.remove_command:
                    result = self.__add_remove(text, False)
                #update mods
                elif matches[0] == self.update_command:
                    if not self.update_mods():
                        Actions.send_message(self.praw, message.author.name, "RE: Mod Update",
                                             "Sorry, I could not update the mod-list right now, please try again later")
                        result = ""
                    else:
                        Actions.send_message(self.praw, message.author.name, "RE: Mod Update", "Mod update successful!")
                        result = ""
                #print query
                elif matches[0] == self.print_command:
                    result = self.__print(text, message.author.name)
                #help query
                elif matches[0] == self.help_command:
                    Actions.send_message(self.praw, message.author.name, "RE:{}".format(message.subject),
                                         self.doc_string)
                    result = ""
                #check errors
                notFound = None
                if result == "no blist":
                    notFound = "a blacklist or whitelist"
                elif result == "no url":
                    notFound = "a valid url"
                elif result == "no domain":
                    notFound = "a domain field"
                elif result == "invalid domain":
                    notFound = "a valid domain"
                elif result.startswith("invalid entry:"):
                    notFound = "a black or whitelist entry for " + result[result.index("invalid entry:") + len(
                        "invalid entry:"):]
                elif result == "error":
                    Actions.send_message(self.praw, message.author.name, "RE:{}".format(message.subject),
                                         "Sorry, an unspecified error occured.  Please submit this query to /r/centralscrutinizer as a bug")
                if notFound:
                    Actions.send_message(self.praw, message.author.name, "RE:{}".format(message.subject),
                                         "Sorry, I could not find " + notFound + " in your query, ask me for help for a list of valid commands and domains!")
            else:
                result = "unknown"
                Actions.send_message(self.praw, message.author.name, "RE:{}".format(message.subject),
                                     "Sorry, I did not recognize your query.  \n".format(text) + self.short_doc_string)

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
                self.update_mods()

            #get unread
            unread = Actions.get_unread(self.praw, limit=self.policy.Unread_To_Load)
            try:
                messages = [message for message in unread]
                for message in messages:
                    self.process_message(message)
            except Exception, e:
                logging.error("Error on retrieving unread messages")
                logging.debug(str(e))
                self.__log_error()

            self.message_cache = []

            #and wait (min of 30s to prevent return of cached answers on default PRAW install)
            time.sleep(max(self.policy.Blacklist_Query_Period, 30))