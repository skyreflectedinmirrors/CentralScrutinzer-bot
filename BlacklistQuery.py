#!/usr/bin/env python2.7

import CentralScrutinizer
import utilitymethods
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

    The blacklist query object allows mods to ask for add/remove from black/whitelists through reddit
    """

    def __init__(self, owner):
        """
        :param owner: our owner! should implement a warn function, so we can warn them when too many errors are encountered
        :param policy: the policy to follow
        """
        super(BlacklistQuery, self).__init__(owner, owner.policy)

        # get blacklists
        self.blacklists = self.owner.blacklists
        # create praw
        self.praw = utilitymethods.create_multiprocess_praw(self.owner.credentials)
        self.sub = utilitymethods.get_subreddit(self.owner.credentials, self.praw)

        # get mods
        self.mod_list = []
        self.update_mods(None)
        if not len(self.mod_list):
            logging.critical("Could not obtain mod list!")
        # last mod update
        self.last_mod_update = datetime.datetime.now()

        # stolen/modified from Django
        self.url_regex = re.compile(r'^https?://(?!.+https?://)'  # http:// or https:// (and only one on a line)
                                    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))'  # domain...
                                    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        self.info_command = re.compile(r"^[iI]nfo\b")
        self.add_command = re.compile(r"^(\+)|([aA]dd)\b")
        self.remove_command = re.compile(r"^(\-)|([rR]emove)\b")
        self.update_command = re.compile(r"^[uU]pdate[- ]*[mM]ods\b")
        self.help_command = re.compile(r"^[hH]elp(\b|$)")
        self.base_commands = [self.info_command, self.add_command, self.remove_command, self.update_command,
                              self.help_command]

        self.blist_command = re.compile(r"\b[Bb]lacklist\b")
        self.wlist_command = re.compile(r"\b[wW]hitelist\b")

        self.short_doc_string = \
            u"""Available Commands:
                            print/add/remove/update-mods/help"""
        self.info_doc_string = \
            u"""
                            **Info** command -- returns various info about the given channel / user / blacklist
                            Usage 1:
                            subject: info list
                            body: domain: youtube.com (e.g., is optional)
                            filter: KEXP (optional, regex supported)

                            Returns a table of:
                                channel, domain, black/whitelist status, lister, list date, reason for listing

                            Where each channel return matches the optional filter and domain


                            Usage 2:
                            subject: info user
                            body: /u/username1
                            /u/username2...

                            Returns a table of:
                                submission, user, channel, domain, strike

                            The list of submissions for a given user(s) along with corresponding channel / domain,
                            and whether the submission was deleted without a proper exception\\*

                            Usage 3:
                            subject: info channel
                            body: url list (url of a video from the desired channels from any domain, one per line)

                            Returns a table of:
                                submission, user, channel, domain, strike

                            The list of submissions for a channel / domain with corresponding user, and whether the
                            submission was deleted without a proper exception\\*

                            \\*  Note: exceptions are updated daily by default

                            """
        self.add_doc_string = \
            u"""
                            **Add** command -- adds the channel associated with the url to the black/whitelist
                            Usage:
                            subject: +whitelist/blacklist (pick one)
                            body: url list  (url of a video from this channel, one per line)
                            """
        self.remove_doc_string = \
            u"""
                            **Remove** command -- removes the channel associated with the domain and id (or optionally url) from the black/whitelist
                            Usage:
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

        self.line_splitter = re.compile("(  \n)|\n")
        self.quote_match = re.compile("^(\".+\",\\s*)*\".+\"$")
        self.whitespace = re.compile("\\s")
        self.comma_match = re.compile("^\\s*,")
        self.force = re.compile(u"--[fF]orce\\b")
        self.line_end = re.compile("\\s*$")
        self.escape_chars = re.compile("(\\\\)|(\\\\\")")
        self.message_cache = []


    def __is_escaped(self, i, line):
        return i > 1 and line[i - 1] == '\\'

    def __end_of_line(self, i, line):
        return self.line_end.match(line[i:]) is not None

    def __unescape(self, entry):
        match = self.escape_chars.search(entry)
        while match is not None:
            group_num = 0 if match.group(0) is None else 1
            entry = entry[:match.start(group_num)] + ("\\" if group_num == 0 else "\"") + \
                    entry[match.end(group_num) + 1:]
            match = self.escape_chars.search(entry)
        return entry

    def quote_splitter(self, line, force=False, warn_width=20):
        entries = []
        error_entries = []
        start_index = None
        for i, char in enumerate(line):
            escaped = self.__is_escaped(i, line)
            if escaped:
                # check character
                if char != "\\" and char != "\"":
                    error_entries.append(i)
            elif char == "\"":
                if start_index is not None:
                    # final quote?
                    if self.__end_of_line(i + 1, line):
                        entries.append((start_index + 1, i))
                    # followed by comma?
                    elif self.comma_match.match(line[i + 1:]):
                        entries.append((start_index + 1, i))
                        start_index = None
                    # otherwise it's an error
                    else:
                        error_entries.append(i)
                else:
                    # start of a new id
                    start_index = i

        stringified = [line[tup[0]:tup[1]] for tup in entries if tup[0] + 1 < tup[1]]
        if len(error_entries):
            # go through and identify which entry each belongs to
            for index, error_loc in enumerate(error_entries):
                for i, entry in enumerate(entries):
                    if entry[0] <= error_loc < entry[1]:
                        error_entries[index] = stringified[i]
            return stringified, error_entries
        return stringified

    def shutdown(self):
        pass

    def update_mods(self, author=None):
        """
        Update the internal mod-list (who can execute queries)
        :param author: if specified, the bot will respond to this user to let them know success/failure
        :return: None
        """
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
            if author is not None:
                Actions.send_message(self.praw, author, u"RE: Modlist update",
                                    u"Error encountered, please try again later.")
            logging.error(u"Could not update moderator list!")
            self.log_error()
            if __debug__:
                logging.exception(e)
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
            Actions.send_message(self.praw, author, u"RE: {}list print".format(u"Black" if blacklist else u"White"), \
                                u"Could not determine blacklist/whitelist from subject line  \n\
                                 Subject: {}".format(subject))
            return False

        # check that we have text
        lines = [l.strip() for l in self.line_splitter.split(text) if l is not None and len(l.strip())]
        if not len(lines):
            Actions.send_message(self.praw, author, u"RE: {}list print".format(u"Black" if blacklist else u"White"), \
                                 u"No domain specified in text:  \n{}".format(text))
            return False

        blist = None
        # get domain
        for b in self.blacklists:
            if b.check_domain(lines[0]):
                blist = b
                break
        if not blist:
            Actions.send_message(self.praw, author, u"RE: {}list print".format(u"Black" if blacklist else u"White"), \
                                 u"Could not find valid domain specified in text:  \n{}".format(lines[0]))
            return False

        myfilter = None
        # get filter
        if len(lines) > 1:
            myfilter = lines[1]

        if blacklist:
            results = blist.get_blacklisted_channels(myfilter)
        else:
            results = blist.get_whitelisted_channels(myfilter)
        if results is None:
            Actions.send_message(self.praw, author, subject, u"Error querying blacklist, please submit bug report to \
                                 /r/centralscrutinizer")
            return False
        elif len(results):
            results = [result[0] for result in results]
            out_str = u"  \n".join(results)
        else:
            out_str = u"No matches found!"
        subject = u"RE:{}list print".format(u"black" if blacklist else u"white")
        subject += u" w/ domain " + blist.domains[0]
        if myfilter:
            subject += u" and filter " + myfilter
        Actions.send_message(self.praw, author, subject, u"Results:  \n" + out_str)
        return True


    def __add_remove(self, author, subject, text, add):
        """
        add/remove a list of entries from the black/whitelist

        :param author: the mod who initiated this query
        :param subject: the subject line of the message
        :param text: the text of the message
        :param add: a boolean indicating whether this is an addition or removal
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
            Actions.send_message(self.praw, author, u"RE: Black/whitelist add/removal", \
                                 u"Could not determine blacklist/whitelist from subject line  \n" \
                                 u"Subject: {}".format(subject))
            return False

        force_flag = self.force.search(subject) is not None

        lines = [l.strip() for l in self.line_splitter.split(text) if l and len(l.strip())]
        matches = [self.quote_match.match(l) for l in lines]
        matches = [m for m in matches if m]
        if len(matches) and len(matches) == len(lines) - 1:
            url_list = False
        elif not len(matches) and any(self.url_regex.match(l) for l in lines):
            url_list = True
        else:
            Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white", \
                                                                            u"addition" if add else u"removal"), \
                                 u"Could not determine format of request.  For an id list, the first line must " \
                                 u"be a domain and all subsequent lines must be followed by comma separated ids in" \
                                 u" quotes.  For a url list, there must be no comma separated ids.")
            return False

        if add and not url_list:
            Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white", \
                                                                            u"addition" if add else u"removal"), \
                                 u"Addition of {}list entries by id is no longer supported.  Please add by URL instead"
                                .format(u"black" if blacklist else u"white"))
            return False

        blist = None
        if not url_list:
            # test the first line to get appropriate blacklist
            for b in self.blacklists:
                if b.check_domain(lines[0]):
                    # store b
                    blist = b
                    break

        # now check that we have a blacklist and url_list defined
        if blist is None and not url_list:
            Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white", \
                                                                            u"addition" if add else u"removal"),
                                 u"Could not determine valid domain from:  \n{}".format(lines[0]))
            return False

        # check that if we do not have a url list, we indeed have a domain and other entries to add
        if not url_list and len(lines) == 1:
            Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white", \
                                                                            u"addition" if add else u"removal"), u"Invalid format detected, must have at least one channel id to {}\
                from {}list for domain {}".format(u"add" if add else u"remove", u"black" if blacklist else u"white", \
                                                  self.lines[0]))
            return False

        entries = lines if url_list else lines[1:]
        invalid_ids = []
        invalid_urls = []
        valid_ids = []
        if not url_list:
            real_entries = []
            # if we have an id list, we have to see if they're comma separated
            for entry in entries:
                val = self.quote_splitter(entry, force=force_flag)
                if isinstance(val, tuple):
                    if force_flag:
                        val = val[0]
                    else:
                        body = u"Warning: potential error(s) in ID list detected, **No action has been taken**.  \n" \
                               u"Unescaped quotes or slashes (or simply malformed input) " \
                               u"has been found in the following entries:    \n\n"
                        body += u"  \n".join(val[1])
                        body += u"  \n  \nIf these entries have been correctly parsed " \
                                u"(note: any escaped characters have not been processed), " \
                                u"please resubmit your last query with the --force flag in the subject line."
                        body += u"  \n  \n**Parsed entries**:  \n"
                        body += u"  \n".join(val[0])
                        Actions.send_message(self.praw, author, u"RE: {}list {}".format(
                            u"black" if blacklist else u"white", u"addition" if add else u"removal"), body)
                        return False
                if val:
                    real_entries.extend([self.__unescape(v) for v in val])
                else:
                    Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white" \
                        ), u"Cannot parse quoted identifiers:  \n{}".format(entry))
            # copy back
            entries = real_entries[:]
        else:
            real_entries = []
            for entry in entries:
                if self.url_regex.match(entry):# and Actions.resolve_url(entry):
                    real_entries.append(entry)
                else:
                    invalid_urls.append(entry)
            entries = real_entries[:]

        if url_list:
            found = [False for u in entries]
            for blist in self.blacklists:
                this_list = []
                for i, url in enumerate(entries):
                    if blist.check_domain(url):
                        found[i] = True
                        this_list.append(url)

                if not len(this_list):
                    continue
                if blacklist:
                    if add:
                        bad_urls, bad_ids, good_ids = blist.add_blacklist_urls(this_list, author)
                    else:
                        bad_urls, bad_ids, good_ids = blist.remove_blacklist_urls(this_list, author)
                else:
                    if add:
                        bad_urls, bad_ids, good_ids = blist.add_whitelist_urls(this_list, author)
                    else:
                        bad_urls, bad_ids, good_ids = blist.remove_whitelist_urls(this_list, author)
                invalid_urls += bad_urls
                invalid_ids += [(b, blist.domains[0]) for b in bad_ids]
                valid_ids += [(g, blist.domains[0]) for g in good_ids]
            invalid_urls += [url for i, url in enumerate(entries) if not found[i]]
        else:
            if blacklist:
                if add:
                    #no longer accepted
                    invalid_ids += entries
                    #invalid += blist.add_blacklist(entries)
                else:
                    invalid_ids += blist.add_blacklist(entries)
            else:
                if add:
                    invalid_ids += blist.add_whitelist(entries)
                else:
                    invalid_ids += blist.add_whitelist(entries)
            valid_ids = [(v, lines[0]) for v in entries if not v in invalid_ids]

        invalid_str = u""
        if invalid_ids is not None and len(invalid_ids):
            if url_list:
                invalid_str += u"Failed to add the following ids:  \n"
                invalid_str += u"  \n".join([u"id = {},domain={}".format(inv[0],  inv[1]) for inv in invalid_ids])
            else:
                invalid_str += u"Failed to add the following ids:  \n"
                invalid_str += u"  \n".join([u"id = {}, domain={}".format(inv[0],  lines[0]) for inv in invalid_ids])

        if invalid_urls is not None and len(invalid_urls):
            invalid_str += u"Invalid urls detected:  \n"
            invalid_str += u"  \n".join(invalid_urls)

        retstr = u""
        if valid_ids is not None and len(valid_ids):
            retstr = u"The following channels were successfully {} the {}list  \n" \
                        u"{}".format(u"added to" if add else u"removed from the", u"black" \
                        if blacklist else u"white", u"  \n".join([u"id = {}, domain={}".format(v[0], v[1])
                                                                  for v in valid_ids]))
        if len(invalid_str):
            if len(retstr):
                retstr += u"  \n"
            retstr += invalid_str
        return Actions.send_message(self.praw, author, u"RE: {}list {}".format(u"black" if blacklist else u"white", \
                                                                               u"addition" if add else u"removal"),
                                    retstr)

    def is_cached(self, id):
        """
        Simple method to avoid re-processing messages
        """
        return id in self.message_cache

    def process_message(self, message):
        """
        Handles the processing of unread messages
        :param message: the message to process
        """
        result = None
        # valid author check
        if any(name == message.author.name for name in self.mod_list) and not self.is_cached(message.id):
            subject = message.subject
            text = message.body
            # check that it matches one of the basic commands
            matches = [bc for bc in self.base_commands if bc.search(subject)]
            if len(matches) == 1:
                # take care of add /removes
                if matches[0] == self.add_command:
                    self.__add_remove(message.author.name, subject, text, True)
                elif matches[0] == self.remove_command:
                    self.__add_remove(message.author.name, subject, text, False)
                # update mods
                elif matches[0] == self.update_command:
                    self.update_mods(message.author.name)
                # print query
                elif matches[0] == self.info_command:
                    result = self.__print(message.author.name, subject, text)
                # help query
                elif matches[0] == self.help_command:
                    Actions.send_message(self.praw, message.author.name, u"RE:{}".format(message.subject),
                                         self.doc_string)

            if len(matches) != 1:
                Actions.send_message(self.praw, message.author.name, u"RE:{}".format(message.subject),
                                     u"Sorry, I did not recognize your query.  \n".format(text) + self.short_doc_string)

        self.message_cache.append(message.id)
        # don't need to see this again
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

            # get unread
            unread = Actions.get_unread(self.praw, limit=self.policy.Unread_To_Load)
            try:
                messages = [message for message in unread]
                if __debug__:
                    logging.info(u"Blacklist query processing {} messages...".format(len(messages)))
                for message in messages:
                    self.process_message(message)
                    if __debug__:
                        logging.info(u"Blacklist query processing message from user {}.\nSubject:{}\nBody:{}".
                                     format(message.author.name if message.author.name is not None else u"DELETED",
                                            message.subject, message.body))
            except Exception, e:
                logging.error(u"Error on retrieving unread messages")
                if __debug__:
                    logging.exception(e)
                self.log_error()

            self.message_cache = []

            # and wait (min of 30s to prevent return of cached answers on default PRAW install)
            time.sleep(max(self.policy.Blacklist_Query_Period, 30))
