#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#DataExtractors.py -- classes designed to retrieve information from various websites (e.g. youtube, soundcloud, etc.)

import soundcloud #soundcloud api
from apiclient.discovery import build #constructs youtube API urls
import apiclient.errors
import re
import logging
import utilitymethods

#base class for extractors
class IdentificationExtractor(object):
    def __init__(self, name, domains, viewcount_limit=None):
        self.name = name
        self.domains = [d.lower() for d in domains]
        self.viewcount_limit = viewcount_limit

    def channel_id(self, url):
        """returns the channel id from the url

        :param url: the url to check
        :return: the (channel_id, channel_url) else None if an error occurs
        """
        raise NotImplementedError

    def get_views(self, url):
        """Returns the number of views for a video

        :param url: The video url
        :return: the number of views for the video
        """
        raise NotImplementedError




class SoundCloudExtractor(IdentificationExtractor):
    def __init__(self, key, policy):
        super(SoundCloudExtractor, self).__init__("soundcloud", ["soundcloud.com", "snd.sc"], policy.soundcloud_viewcount_limit)
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
            logging.error(u"Bad resolve for soundcloud " + str(url))
            return None

        try:
            return response.username, response.permalink_url
        except AttributeError:
            try:
                return (response.user['username'], response.user['permalink_url'])
            except AttributeError:
                logging.info(u"Deleted or private soundcloud user requested: {}".format(url))
                return None
        except Exception, e:
            logging.error(u"Could not find soundcloud username or permalink for url: {}".format(url))
            logging.debug(str(e))

    def get_views(self, url):
        #query server
        response = None
        try:
            #resolve the url
            response = self.soundcloud.get('/resolve', url=url)
        except Exception, e:
            logging.error(u"Bad resolve for soundcloud " + str(url))
            return None

        try:
            return response.playback_count
        except AttributeError:
            try:
                return response.user['playback_count']
            except AttributeError:
                logging.info(u"Deleted or private soundcloud user requested: {}".format(url))
                return None
        except Exception, e:
            logging.error(u"Could not find soundcloud username or permalink for url: {}".format(url))
            logging.debug(str(e))
        return None


class YoutubeExtractor(IdentificationExtractor):
    def __init__(self, key, policy):
        super(YoutubeExtractor, self).__init__("youtube", ['youtube.com', 'youtu.be', 'm.youtube.com'], policy.youtube_viewcount_limit)
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        self.videos_url = '/videos/'
        self.key = key
        self.regex = re.compile(
            r'''(?<=(?:v|i)=)[a-zA-Z0-9-]+(?=&)|(?<=(?:v|i)\/)[^&\n]+|(?<=embed\/)[^"&\n]+|'''
            r'''(?<=(?:v|i)=)[^&\n]+|(?<=youtu.be\/)[^&\n]+''', re.I)
        self.channel_regex = re.compile(r"(?:(?:http|https):\/\/|)(?:www\.)?youtube\.com\/(?:channel\/|user\/)([a-zA-Z0-9_-]{1,})")
        self.youtube = build('youtube', 'v3', developerKey=self.key)

    #returns the channel id from a url
    def channel_id(self, url, retry_id=None):
        """returns the (channel_id, channel_url) from a youtube url

        :param url: the url in question
        :return: (channel_id, channel_url) or None if an error occured
        """
        if retry_id is not None:
            id = retry_id
        else:
            id = self.__get_video_id(url)
        if not id:
            return None

        #query server
        response = None
        channel_id = None
        try:
            response = self.youtube.videos().list(part='snippet', id=id).execute()
        except apiclient.errors.HttpError:
            #maybe it's a channel:
            pass
            #logging.error("Bad request for youtube id " + str(id))
            #return None

        try:
            channel_id = response.get("items")[0].get("snippet").get("channelId")
        except IndexError:
            #try it as a channel
            channel_id = id
        except Exception, e:
            logging.error(u"Unknown error detecting channelId for youtube url " + str(url))


         #avoid asking if the ID is marked PRIVATE
        if channel_id == "PRIVATE" or channel_id is None:
            return None

        # ask for channel w/ id
        try:
            response = self.youtube.channels().list(part='snippet', id=channel_id).execute()
        except apiclient.errors.HttpError:
            logging.error(u"Bad request for youtube channel id {} and url {} ".format(str(channel_id), str(url)))
            return None

        try:
            #should be the first id in the list
            channel_title = response.get("items")[0].get("snippet").get("title")
        except IndexError:
            #retry with 11 character limit
            if retry_id is None and len(id) > 11:
                logging.warning(u'Retrying channel_id for id {} w/ 11 character id {}'.format(id, id[:11]))
                return self.channel_id(url, retry_id=id[:11])
            logging.info(u"Deleted or private youtube channel requested: {}, for url {}".format(id, str(url)))
            return None
        except Exception, e:
            logging.exception(e)
        return channel_title, u"http://www.youtube.com/channel/{}".format(channel_id)


    def __get_video_id(self, url):
        """Given a url, this returns the video id for a youtube video"""
        # regex via: http://stackoverflow.com/questions/3392993/php-regex-to-get-youtube-video-id

        yt_id = self.regex.findall(
            url.replace('%3D', '=').replace('%26', '&').replace('%2F', '?').replace('&amp;', '&'))

        if not yt_id:
            #try parsing it as a channel
            #regex via: http://stackoverflow.com/questions/25413707/regex-for-youtube-channel-url
            yt_id = self.channel_regex.findall(
            url.replace('%3D', '=').replace('%26', '&').replace('%2F', '?').replace('&amp;', '&'))

        if yt_id and len(yt_id) > 1 and "channel" in url:
            logging.info(u"More than one YT id detected in url {}".format(url))
            return None

        if yt_id:
            yt_id = yt_id[0].split('#')[0]
            yt_id = yt_id.split('?')[0]
            if yt_id.endswith('/'):
                yt_id = yt_id[:-1]
            return yt_id
        return None

    def get_views(self, url, retry_id=None):
        if retry_id is not None:
            id = retry_id
        else:
            id = self.__get_video_id(url)
        if not id:
            return None

        #query server
        response = None
        try:
            response = self.youtube.videos().list(part='statistics', id=id).execute()
        except apiclient.errors.HttpError:
            logging.info(u"Could not determine views for video: {}".format(id))
            return None

        try:
            viewcount = response.get("items")[0].get("statistics").get("viewCount")
            return int(viewcount)
        except IndexError:
            logging.error(u"No items found for youtube id {} for url {}".format(id, str(url)))
            #retry with 11 character limit
            if retry_id is None and len(id) > 11:
                logging.warning(u'Retrying viewcount for id {} w/ 11 character id {}'.format(id, id[:11]))
                return self.get_views(url, retry_id=id[:11])
            return None
        except Exception, e:
            logging.error(u"Unknown error detecting viewCount for youtube url " + str(url))
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
        domain = utilitymethods.domain_extractor(url)
        if not domain:
            return None
        try:
            return domain, url[:url.index(domain)] + domain
        except:
            logging.error(u"Bad domain extracted from {}".format(url))
            return None

    def get_views(self, url):
        return None