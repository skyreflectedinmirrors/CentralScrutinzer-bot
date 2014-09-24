"""Blacklist.py - a implementation of black/whitelists"""


import logging

from threading import Lock
import re
import utilitymethods
from praw.objects import WikiPage
import Actions
import DataBase

from DataExtractors import IdentificationExtractor

class BlacklistEnums:
    NotFound, Blacklisted, Whitelisted = range(3)

class Blacklist(object):
    """ Also a whitelist, but who's counting
    @type data IdentificationExtractor
    @type wiki WikiPage
    """
    def __init__(self, data_extractor, database_file):
        assert(isinstance(data_extractor, IdentificationExtractor))
        #set data
        self.name = data_extractor.name
        self.data = data_extractor
        self.domains = self.data.domains
        self.locker = Lock()
        self.blacklist = set()
        self.whitelist = set()
        self.file = database_file

        #load black and whitelist
        with DataBase.DataBaseWrapper(self.file) as db:
            blist = db.get_channels(blacklist=BlacklistEnums.Blacklisted, domain=self.domains[0])
            if blist:
                for item in blist:
                    self.blacklist.add(item[0])
            wlist = db.get_channels(blacklist=BlacklistEnums.Whitelisted, domain=self.domains[0])
            if wlist:
                for item in wlist:
                    self.whitelist.add(item[0])


    def check_blacklist(self, url=None, id=None):
        """ This method tells you whether a submission is on a blacklisted channel. Either id or url must be specified
        :param url: the url to check
        :param id: the id to check
        :return: the appropriate blacklist enum
        """
        if not url and not id:
            logging.warning("No url or id specified")
            return BlacklistEnums.NotFound

        retval = BlacklistEnums.NotFound
        if url and self.check_domain(url):
            id = self.data.channel_id(url)
            if id and not id == "PRIVATE":
                id = id[0]

        if id and not id == "PRIVATE":
            self.locker.acquire()
            if id in self.blacklist:
                retval = BlacklistEnums.Blacklisted
            elif id in self.whitelist:
                retval = BlacklistEnums.Whitelisted
            self.locker.release()
        return retval

    def check_domain(self, url):
        """
        Checks whether a domain is valid for this extractor
        """
        domain = utilitymethods.domain_extractor(url)
        if domain:
            return any(d.startswith(domain) or d.endswith(domain) for d in self.domains)
        return False

    def add_blacklist(self, urls):
        """ adds a channel to the blacklist
        :param url: a url of link corresponding to the channel
        """
        if not isinstance(urls, list):
            urls = [urls]
        return self.__add_channels(urls, BlacklistEnums.Blacklisted)

    def add_whitelist(self, urls):
        """ adds a channel to the whitelist
        :param url: a url of link corresponding to the channel
        """
        if not isinstance(urls, list):
            urls = [urls]
        return self.__add_channels(urls, BlacklistEnums.Whitelisted)

    def __split_on_condition(self, seq, condition):
        a, b = [], []
        for item in seq:
            (a if condition(item) else b).append(item)
        return a,b

    def __add_channels(self, urls, value):
        """Adds a channel to the list

        :param urls:  a list of urls corresponding to channels ot add
        :param value: BLACKLIST or WHITELIST
        :return: True if successfully added, false otherwise
        """
        #check that the domain is being added
        my_urls,invalid_urls = self.__split_on_condition(urls, self.check_domain)
        #get ids
        ids = [self.data.channel_id(url) for url in my_urls]
        valid_ids, invalid_ids = self.__split_on_condition(ids, lambda x: x and x != "PRIVATE")
        #transform
        entries = [(id[0], self.domains[0]) for id in valid_ids]
        with DataBase.DataBaseWrapper(self.file, False) as db:
            #first find list of channels that exist already
            existant_channels = db.channel_exists(entries)
            if not existant_channels:
                return invalid_urls + invalid_ids + valid_ids
            #split and populate our tuple lists based on this
            update_list = []
            add_list = []
            for i, channel_exists in enumerate(existant_channels):
                if channel_exists:
                    update_list.append((entries[i]) + (value,))
                else:
                    add_list.append(entries[i] + (valid_ids[i][1], value, 0))

            #add and update channels
            if len(update_list):
                db.set_blacklist(update_list)
            if len(add_list):
                db.add_channels(add_list)
        #finally add to the appropriate shortlist
        the_list = None
        if value == BlacklistEnums.Blacklisted:
            the_list = self.blacklist
        elif value == BlacklistEnums.Whitelisted:
            the_list = self.whitelist
        if the_list != None and len(valid_ids):
            self.locker.acquire()
            for id in valid_ids:
                the_list.add(id[0])
            self.locker.release()
        return invalid_urls + invalid_ids


    def remove_blacklist_url(self, urls):
        """Removes channels from blacklist by URL
            :return: a list of urls not valid or not found
        """
        return self.__remove_channels_url(urls, BlacklistEnums.Blacklisted)

    def remove_blacklist(self, ids):
        """Removes channels from blacklist by ID
         :return: a list of ids not valid or not found"""
        return self.__remove_channels(ids, BlacklistEnums.Blacklisted)

    def remove_whitelist_url(self, urls):
        """Removes channels from whitelist by URL
         :return: a list of urls not valid or not found"""
        return self.__remove_channels_url(urls, BlacklistEnums.Whitelisted)

    def remove_whitelist(self, ids):
        """Removes channels from whitelist by ID
         :return: a list of ids not valid or not found"""
        return self.__remove_channels(ids, BlacklistEnums.Whitelisted)

    def __remove_channels_url(self, urls, value):
        if not isinstance(urls, list):
            urls = [urls]
                #check that the domain is being added
        my_urls,invalid_urls = self.__split_on_condition(urls, self.check_domain)
        #get ids
        ids = [self.data.channel_id(url) for url in my_urls]
        valid_ids, invalid_ids = self.__split_on_condition(ids, lambda x: x and x != "PRIVATE")
        return invalid_urls + invalid_ids + self.__remove_channels([v[0] for v in valid_ids], value)

    def __remove_channels(self, ids, value):
        if not isinstance(ids, list):
            ids = [ids]
        invalid_ids = []
        valid_ids = []
        #transform
        entries = [(id, self.domains[0]) for id in ids]
        #update database
        with DataBase.DataBaseWrapper(self.file, False) as db:
            existant_channels = db.channel_exists(entries)
            update_list = []
            for i, channel_exists in enumerate(existant_channels):
                if channel_exists:
                    update_list.append(entries[i] + (BlacklistEnums.NotFound,))
                    valid_ids.append(ids[i])
                else:
                    invalid_ids.append(ids[i])
            if len(update_list):
                db.set_blacklist(update_list)

        #update the appropriate shortlist

        the_list = None
        if value == BlacklistEnums.Blacklisted:
            the_list = self.blacklist
        elif value == BlacklistEnums.Whitelisted:
            the_list = self.whitelist
        if the_list != None and len(valid_ids):
            self.locker.acquire()
            for id in valid_ids:
                the_list.remove(id)
            self.locker.release()
        return invalid_ids

    def get_blacklisted_channels(self, filter):
        """returns the blacklisted channel's whos id matches this filter"""
        return self.__get_channels(filter, BlacklistEnums.Blacklisted)

    def get_whitelisted_channels(self, filter):
        """returns the whitelisted channel's whos id matches this filter"""
        return self.__get_channels(filter, BlacklistEnums.Whitelisted)

    def __get_channels(self, filter, value):
        if value == BlacklistEnums.Whitelisted:
            list = self.whitelist
        elif value == BlacklistEnums.Blacklisted:
            list = self.blacklist
        else:
            list = None
        copy = []
        if list:
            if filter:
                regex = re.compile(filter)
            self.locker.acquire()
            if filter:
                copy = [k for k in list if regex.search(k)]
            else:
                copy = [k for k in list]
            self.locker.release()
        return copy