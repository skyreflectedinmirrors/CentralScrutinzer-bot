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
        self.file = database_file

        #make sure database is created
        with DataBase.DataBaseWrapper(self.file) as db:
            pass

    def check_blacklist(self, urls=None, ids=None):
        """ This method tells you whether each in a list of submission is on a blacklisted channel. Either ids or urls must be specified
        :param url: the urls to check
        :param id: the ids to check
        :return: the appropriate blacklist enums
        """
        if not urls and not ids:
            logging.warning("No url or id specified")
            return BlacklistEnums.NotFound

        if urls:
            if not isinstance(urls, list):
                urls = list(urls)
            results = [BlacklistEnums.NotFound for url in urls]
            ids = [(i, self.data.channel_id(url)[0]) for i, url in enumerate(urls) if self.check_domain(url)]
            ids = [id for id in ids if id and not id[1] == "PRIVATE"]
        elif ids:
            if not isinstance(ids, list):
                ids = list(ids)
            results = [BlacklistEnums.NotFound for id in ids]
            ids = [(i, id) for i, id in enumerate(ids) if id != "PRIVATE"]

        with DataBase.DataBaseWrapper(self.file, False) as db:
            temp_ret = db.get_blacklist([(id[1], self.domains[0]) for id in ids])
            for i in range(len(ids)):
                results[ids[i][0]] = temp_ret[i]

        return results

    def check_domain(self, url):
        """
        Checks whether a domain is valid for this extractor
        """
        domain = utilitymethods.domain_extractor(url)
        if domain:
            return any(domain.startswith(d) or domain.endswith(d) for d in self.domains)
        return False

    def add_blacklist_urls(self, urls):
        """ adds a channel to the blacklist
        :param url: a url of link corresponding to the channel
        """
        return self.__add_channels_url(urls, BlacklistEnums.Blacklisted)

    def add_whitelist_urls(self, urls):
        """ adds a channel to the whitelist
        :param url: a url of link corresponding to the channel
        """
        return self.__add_channels_url(urls, BlacklistEnums.Whitelisted)

    def add_blacklist(self, ids):
        """ adds a channel to the blacklist
        :param ids: ids of channels
        """
        if not isinstance(ids, list):
            ids = [ids]
        return self.__add_channels(ids, BlacklistEnums.Blacklisted)

    def add_whitelist(self, ids):
        """ adds a channel to the whitelist
        :param url: a url of link corresponding to the channel
        """
        if not isinstance(ids, list):
            ids = [ids]
        return self.__add_channels(ids, BlacklistEnums.Whitelisted)

    def __split_on_condition(self, seq, condition):
        a, b = [], []
        for item in seq:
            (a if condition(item) else b).append(item)
        return a,b

    def __split_on_condition_altlist(self, seq, condition, altlist):
        a, b = [], []
        for i, item in enumerate(seq):
            if condition(item):
                a.append(item)
            else:
                b.append(altlist[i])
        return a,b

    def __add_channels(self, ids, value):
        """Adds a channel to the list

        :param ids:  a list of ids corresponding to channels to add
        :param value: BLACKLIST or WHITELIST
        :return: True if successfully added, false otherwise
        """

        #transform
        entries = [(id, self.domains[0]) for id in ids]
        with DataBase.DataBaseWrapper(self.file, False) as db:
            #first find list of channels that exist already
            existant_channels = db.channel_exists(entries)
            if existant_channels is None or not len(existant_channels):
                return ids
            #split and populate our tuple lists based on this
            update_list = []
            add_list = []
            for i, channel_exists in enumerate(existant_channels):
                update_list.append(entries[i])
                #add if not existant, and no duplicates
                if not channel_exists:
                    add_list.append(entries[i])

            if len(add_list):
                db.add_channels(add_list)
            #add and update channels
            if len(update_list):
                db.set_blacklist(update_list, value)
            #finally check for invalid entries
            set_correct = db.check_blacklist(update_list, value)
            return [ids[i] for i, val in enumerate(set_correct) if not val]


    def remove_blacklist_urls(self, urls):
        """Removes channels from blacklist by URL
            :return: a list of urls not valid or not found
        """
        return self.__remove_channels_url(urls, BlacklistEnums.Blacklisted)

    def remove_blacklist(self, ids):
        """Removes channels from blacklist by ID
         :return: a list of ids not valid or not found"""
        return self.__remove_channels(ids, BlacklistEnums.Blacklisted)

    def remove_whitelist_urls(self, urls):
        """Removes channels from whitelist by URL
         :return: a list of urls not valid or not found"""
        return self.__remove_channels_url(urls, BlacklistEnums.Whitelisted)

    def remove_whitelist(self, ids):
        """Removes channels from whitelist by ID
         :return: a list of ids not valid or not found"""
        return self.__remove_channels(ids, BlacklistEnums.Whitelisted)

    def __add_channels_url(self, urls, value):
        if not isinstance(urls, list):
            urls = [urls]
        #check that the domain is being added
        my_urls, invalid_urls = self.__split_on_condition(urls, self.check_domain)
        #get ids
        ids = [self.data.channel_id(url) for url in my_urls]
        valid_ids, invalid_ids = self.__split_on_condition_altlist(ids, lambda x: x and x[0] != "PRIVATE", my_urls)
        failed_ids = self.__add_channels([v[0] for v in valid_ids], value)
        return (invalid_urls, invalid_ids + failed_ids, [v[0] for v in valid_ids if not v[0] in failed_ids])

    def __remove_channels_url(self, urls, value):
        if not isinstance(urls, list):
            urls = [urls]
                #check that the domain is being added
        my_urls,invalid_urls = self.__split_on_condition(urls, self.check_domain)
        #get ids
        ids = [self.data.channel_id(url) for url in my_urls]
        valid_ids, invalid_ids = self.__split_on_condition_altlist(ids, lambda x: x and x[0] != "PRIVATE", my_urls)
        failed_ids = self.__remove_channels([v[0] for v in valid_ids], value)
        return (invalid_urls, invalid_ids + failed_ids, [v[0] for v in valid_ids if v[0] not in failed_ids])

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
                #update if channel exists and not a duplicate
                if entries[i] in update_list:
                    continue
                if channel_exists:
                    update_list.append(entries[i])
                    valid_ids.append(ids[i])
                else:
                    invalid_ids.append(ids[i])
            if len(update_list):
                db.set_blacklist(update_list, BlacklistEnums.NotFound)
            #check that they were removed correctly
            set_correct = db.check_blacklist(update_list, BlacklistEnums.NotFound)
            invalid_ids += [ids[i] for i, val in enumerate(set_correct) if not val]

        return invalid_ids

    def get_blacklisted_channels(self, filter):
        """returns the blacklisted channel's whos id matches this filter"""
        return self.__get_channels(filter, BlacklistEnums.Blacklisted)

    def get_whitelisted_channels(self, filter):
        """returns the whitelisted channel's whos id matches this filter"""
        return self.__get_channels(filter, BlacklistEnums.Whitelisted)

    def __get_channels(self, filter, value):
        with DataBase.DataBaseWrapper(self.file, False) as db:
            return db.get_channels(blacklist=value, domain=self.domains[0], id_filter=filter)