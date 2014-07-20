"""Blacklist.py - a implementation of black/whitelists"""


import logging

from threading import Lock
from urlparse import urlsplit
import re
import utilitymethods
from praw.objects import WikiPage
import logging
import Actions

from DataExtractors import IdentificationExtractor

class Blacklist(object):
    """ Also a whitelist, but who's counting
    @type data IdentificationExtractor
    @type wiki WikiPage
    """
    def __init__(self, credentials, data_extractor):
        assert(isinstance(data_extractor, IdentificationExtractor))
        #set data
        self.name = data_extractor.name
        self.data = data_extractor
        self.domains = self.data.domains
        self.list = {}
        self.locker = Lock()
        self.BLACKLIST = "B"
        self.WHITELIST = "W"
        #load praw
        self.reddit = utilitymethods.create_multiprocess_praw(credentials)
        sub = utilitymethods.get_subreddit(credentials, self.reddit)
        self.wiki = Actions.get_or_create_wiki(self.reddit, sub, self.name + "_blacklist")
        #load list
        self.__unserialze_list()

    def __serialize_list(self):
        self.locker.acquire()
        retstring = '  \n'.join("%s=%r" % (key,val) for (key,val) in self.list.iteritems())
        self.locker.release()
        return retstring

    def __unserialze_list(self):
        self.locker.acquire()
        content = self.wiki.content_md
        if content:
            for entry in content.split('  \n'):
                (key, value) = entry.split('=')
                self.list[key] = value
        self.locker.release()

    def check_blacklist(self, url):
        """ This method tells you whether a submission is on a blacklisted channel.
        :param url: the url to check
        :return: True if the url's channel is in this blacklist, false if not this domain, or not blacklisted
        """
        retval = False
        if self.__check_domain(url):
            channel = self.data.channel_id(url)
            self.locker.acquire()
            if len([c for c in self.list if channel == c]):
                retval = True
            self.locker.release()
        return retval

    def __check_domain(self, url):
        """
        Checks whether a domain is valid for this extractor
        """
        domain = utilitymethods.domain_extractor(url)
        if domain:
            return any(domain.endswith(d) for d in self.domains)
        return False

    def add_blacklist(self, urls):
        """ adds a channel to the blacklist
        :param url: a url of link corresponding to the channel
        :return: True if successfully added, false otherwise
        """
        if not isinstance(urls, list):
            urls = [urls]
        for url in urls:
            logging.info("Adding channel from url " + url + " to blacklist:" + self.name)
        return self.__add_channels(urls, self.BLACKLIST)

    def add_whitelist(self, urls):
        """ adds a channel to the whitelist
        :param url: a url of link corresponding to the channel
        :return: True if successfully added, false otherwise
        """
        if not isinstance(urls, list):
            urls = [urls]
        for url in urls:
            logging.info("Adding channel from url " + url + " to whitelist: " + self.name)
        return self.__add_channels(urls, self.WHITELIST)

    def __add_channels(self, urls, value):
        """Adds a channel to the list

        :param urls:  a list of urls corresponding to channels ot add
        :param value: BLACKLIST or WHITELIST
        :return: True if successfully added, false otherwise
        """
        #check that the domain is being added
        my_urls = [url for url in urls if self.__check_domain(url)]
        #get ids
        my_ids = [self.data.channel_id(url) for url in my_urls]
        self.locker.acquire()
        #add to list
        for id in my_ids:
            self.list[id] = value
        self.locker.release()
        #write to wikipage
        rstring = self.__serialize_list()
        Actions.write_wiki_page(self.wiki, rstring, reason="Adding channels " + ', '.join(my_ids) + " to the " + ("Blacklist" if value == self.BLACKLIST else "Whitelist"))

    def remove_blacklist_url(self, urls):
        """Removes channels from blacklist by URL"""
        self.__remove_channels_url(urls)

    def remove_blacklist(self, ids):
        """Removes channels from blacklist by ID"""
        self.__remove_channels(ids)

    def remove_whitelist_url(self, urls):
        """Removes channels from whitelist by URL"""
        self.__remove_channels_url(urls)

    def remove_whitelist_url(self, ids):
        """Removes channels from whitelist by ID"""
        self.__remove_channels(ids)

    def __remove_channels_url(self, urls):
        if not isinstance(urls, list):
            urls = [urls]
        #check that the domain is being added
        my_urls = [url for url in urls if self.__check_domain(url)]
        #get ids
        my_ids = [self.data.channel_id(url) for url in my_urls]
        #remove
        self.__remove_channels(my_ids)

    def __remove_channels(self, ids):
        if not isinstance(ids, list):
            ids = [ids]
        self.locker.acquire()
        #add to list
        for id in ids:
            if id in self.list:
                del self.list[id]
        self.locker.release()
        #write to wikipage
        string = self.__serialize_list()
        Actions.write_wiki_page(self.wiki, string, "Removing ids: " + ', '.join(ids) + " from the list")

    def get_blacklisted_channels(self, filter):
        """returns the blacklisted channel's whos id matches this filter"""
        return self.__get_channels(filter, self.BLACKLIST)

    def get_whitelisted_channels(self, filter):
        """returns the whitelisted channel's whos id matches this filter"""
        return self.__get_channels(filter, self.WHITELIST)

    def __get_channels(self, filter, value):
        regex = re.compile(filter)
        self.locker.acquire()
        copy = [k for k, v in self.list.iteritems() if regex.search(k) and v == value]
        self.locker.release()
        return copy