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
    def __init__(self, owner, policy):
        """
        :param owner: our owner! should implement a warn function, so we can warn them when too many errors are encountered
        :param policy: the policy to follow
        """
        super(BlacklistQuery, self).__init__(owner, policy)
        self.owner = owner
        self.policy = self.owner.policy

        #get blacklists
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

        self.url_regex = re.compile("(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?")

        self.print_command = re.compile("^[pP]rint\b")
        self.add_command = re.compile("^[aA]dd\b")
        self.remove_command = re.compile("^[rR]emove\b")
        self.update_command = re.compile("^[uU]pdate[- ][mM]ods\b")
        self.help_command = re.compile("^[hHelp]")
        self.base_commands = [self.print_command, self.add_command, self.remove_command, self.update_command]

        self.domain_match = re.compile("\b(\w+)\b")

        self.blist_command = re.compile("\b[Bb]lacklist\b")
        self.wlist_command = re.compile("\b[wW]hitelist\b")
        self.filters = [re.compile('(?<!\\)\"(.+)(?<!\\)\"'), re.compile("\b(\w+)\b")]


        self.doc_string = """Available Commands:
                            print whitelist domain filter? -- prints the whitelist for the given domain and id filter. Note: filter optional
                            print blacklist domain filter? -- prints the blacklist for the given domain and id filter. Note: filter optional
                            add whitelist url               -- adds the channel associated with the url to the whitelist
                            add blacklist url               -- adds the channel associated with the url to the blacklist
                            remove whitelist url            -- removes the channel associated with the url from the whitelist
                            remove blacklist url            -- removes the channel associated with the url from the blacklist
                            update-mods                     -- updates my list of moderators for this subreddit
                            help                            -- prints this message
                            Available Domains:
                          """
        self.doc_string = textwrap.dedent(self.doc_string)
        self.domains = list(set(d.replace(".com", "").replace("http://","").replace("https://", "").replace("www.", "") for b in self.blacklists for d in b.domains))
        for domain in self.domains:
            self.doc_string += "\n" + domain

    def __shutdown(self):
        pass

    def update_mods(self):
        try:
            mlist = [mod.name for mod in Actions.get_mods(self.praw, self.sub)]
            #only update if it's valid
            self.mod_list = mlist
            return True
        except Exception, e:
            logging.critical("Could not update moderator list!")
            logging.debug(str(e))
            return False

    def __print(self, text, user):
        #get black/whitelist
        blacklist = None
        if self.blist_command.search(text):
            blacklist = True
        elif self.wlist_command.search(text):
            blacklist = False
        if blacklist is None:
            return "no blist"

        #get domain
        result = self.domain_match.search(text)
        if not result:
            return "no domain"
        result = result.groups()
        if not len(result):
            return "no domain"
        domain = result[0]
        if len(any(d == domain for d in self.domains)):
            return "invalid domain"
        search_txt = text[text.index(domain) + len(domain):]

        #get filter
        filters = [f.search(text) for f in self.filters.search(search_txt)]
        filters = [f for f in filters if f]
        myfilter = None
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
            results = sorted(results)
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
        #get black/whitelist
        blacklist = None
        if self.blist_command.search(text):
            blacklist = True
        elif self.wlist_command.search(text):
            blacklist = False
        if blacklist is None:
            return "no blist"

        #get url
        url = self.url_regex.search(text)
        if url:
            url = url.groups()
            if len(url) != 1:
                return "no url"
            url = url[0]
        else:
            return "no url"

        found = False
        for b in self.blacklists:
            if blacklist:
                found = found or len(b.check_domain(url))
            else:
                found = found or len(b.check_domain(url))
        if not found:
            return "invalid domain"
        return ""

    def run(self):
        while True:
            if not self.__check_status():
                break

            #see if we need to update mods
            if datetime.datetime.now() - self.last_mod_update > self.policy.Mod_Update_Period:
                self.update_mods()

            #get unread
            unread = Actions.get_unread(self.praw, limit=self.policy.Unread_To_Load)
            try:
                for message in unread:
                    #valid author check
                    if any(name == message.author.name for name in self.mod_list):
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
                                    Actions.send_message(self.praw, message.author.name, "RE: Mod Update", "Sorry, I could not update the mod-list right now, please try again later")
                                else:
                                    Actions.send_message(self.praw, message.author.name, "RE: Mod Update", "Mod update successful!")
                            #print query
                            elif matches[0] == self.print_command:
                                result = self.__print(text, message.author.name)
                            #help query
                            elif matches[0] == self.help_command:
                                Actions.send_message(self.praw, message.author.name, self.doc_string)
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
                            elif result == "error":
                                Actions.send_message(self.praw, message.author.name, "RE:{}".format(message.subject), "Sorry, an unspecified error occured.  Please submit this query to /r/centralscrutinizer as a bug")
                            if notFound:
                                Actions.send_message(self.praw, message.author.name, "RE:{}".format(message.subject), "Sorry, I could not find " + notFound + " in the text {}, ask me for help for a list of valid commands and domains!".format(text))
                        else:
                            Actions.send_message(self.praw, message.author.name, "RE:{}".format(message.subject), "Sorry, I did not recognize the text {}, ask me for help for a list of valid commands and domains!".format(text))
                    #don't need to see this again
                    message.mark_read()
            except Exception, e:
                logging.error("Error on retrieving unread messages")
                logging.debug(str(e))
                self.__log_error()

        #and wait
        threading.current_thread.wait(self.policy.Blacklist_Quary_Period)