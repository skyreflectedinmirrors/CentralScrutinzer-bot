#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#DataExtractors.py -- classes designed to retrieve information from various websites (e.g. youtube, soundcloud, etc.)

import soundcloud #soundcloud api
from apiclient.discovery import build #constructs youtube API urls
import apiclient.errors
import re
import logging

#base class for extractors
class IdentificationExtractor(object):
    def __init__(self, name, domains):
        self.name = name
        self.domains = [d.lower() for d in domains]

    def channel_id(self, url):
        """returns the channel id from the url

        :param url: the url to check
        :return: the (channel_id, channel_url) else None if an error occurs
        """
        raise NotImplementedError




class SoundCloudExtractor(IdentificationExtractor):
    def __init__(self, key):
        super(SoundCloudExtractor, self).__init__("soundcloud", ["soundcloud.com"])
        self.soundcloud = soundcloud.Client(client_id=key)

    def channel_id(self, url):
        """the soundcloud username

        :param url: the url to check
        :return: the soundcloud user name if found, private if a deleted or private link is used, None if an error occurs
        """

        #query server
        response = None
        try:
            #resolve the url
            response = self.soundcloud.get('/resolve', url=url)
        except Exception, e:
            logging.error("Bad resolve for soundcloud " + str(url))
            return None

        try:
            return response.username, response.permalink_url
        except AttributeError:
            try:
                return (response.user['username'], response.user['permalink_url'])
            except AttributeError:
                logging.info("Deleted or private soundcloud user requested: {}".format(url))
                return "PRIVATE"
        except Exception, e:
            logging.error("Could not find soundcloud username or permalink for url: {}".format(url))
            logging.debug(str(e))


class YoutubeExtractor(IdentificationExtractor):
    def __init__(self, key):
        super(YoutubeExtractor, self).__init__("youtube", ['youtube.com', 'youtu.be', 'm.youtube.com'])
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        self.videos_url = '/videos/'
        self.key = key
        self.regex = regex = re.compile(
            r'''(?<=(?:v|i)=)[a-zA-Z0-9-]+(?=&)|(?<=(?:v|i)\/)[^&\n]+|(?<=embed\/)[^"&\n]+|'''
            r'''(?<=(?:v|i)=)[^&\n]+|(?<=youtu.be\/)[^&\n]+''', re.I)
        self.youtube = build('youtube', 'v3', developerKey=self.key)

    #returns the channel id from a url
    def channel_id(self, url):
        """returns the (channel_id, channel_url) from a youtube url

        :param url: the url in question
        :return: (channel_id, channel_url) or None if an error occured
        """
        id = self.__get_video_id(url)
        if not id:
            return None

        #query server
        response = None
        try:
            response = self.youtube.videos().list(part='snippet', id=id).execute()
        except apiclient.errors.HttpError:
            logging.error("Bad request for youtube video id " + str(id))
            return None

        try:
            #should be the first id in the list
            response = response.get("items")[0].get("snippet").get("channelId")
        except IndexError:
            logging.info("Deleted or private youtube video url requested: {}".format(url))
            return "PRIVATE"
        except Exception, e:
            logging.error()


         #avoid asking if the ID is marked PRIVATE
        if response == "PRIVATE" or response == None:
            return response

        # ask for channel w/ id
        try:
            response = self.youtube.channels().list(part='snippet', id=response).execute()
        except apiclient.errors.HttpError:
            logging.error("Bad request for youtube video id " + str(response))
            return None

        try:
            #should be the first id in the list
            response = response.get("items")[0].get("snippet").get("title")
        except IndexError:
            logging.info("Deleted or private youtube channel requested: {}".format(id))
            return "PRIVATE"
        except Exception, e:
            logging.error()
        return response, u"http://www.youtube.com/user/{}".format(response)


    def __get_video_id(self, url):
        """Given a url, this returns the video id for a youtube video"""
        # regex via: http://stackoverflow.com/questions/3392993/php-regex-to-get-youtube-video-id

        yt_id = self.regex.findall(
            url.replace('%3D', '=').replace('%26', '&').replace('%2F', '?').replace('&amp;', '&'))

        if yt_id:
            # temp fix:
            yt_id = yt_id[0].split('#')[0]
            yt_id = yt_id.split('?')[0]
            return yt_id
        return None

from utilitymethods import domain_extractor
class BandCampExtractor(IdentificationExtractor):
    def __init__(self):
        super(BandCampExtractor, self).__init__("bandcamp", ["bandcamp.com"])

    def channel_id(self, url):
        """returns the channel id from a url
        By default only the domain is returned, e.g.:
        "http://www.sleepwalkersbandcamp.bandcamp.com/" -> "sleepwalkersbandcamp.bandcamp.com"
        :returns: the id, or None if an error is encountered
        """
        domain = domain_extractor(url)
        if not domain:
            return domain
        try:
            return domain, url[:url.index(domain)] + domain
        except:
            logging.error("Bad domain extracted from {}".format(url))
            return None