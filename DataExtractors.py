#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#DataExtractors.py -- classes designed to retrieve information from various websites (e.g. youtube, soundcloud, etc.)

import soundcloud #soundcloud api
from apiclient.discovery import build #constructs youtube API urls
import apiclient.errors
import re
import logging

class YoutubeExtractor(object):
    def __init__(self, key):
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        self.videos_url = '/videos/'
        self.key = key
        self.regex = regex = re.compile(
            r'''(?<=(?:v|i)=)[a-zA-Z0-9-]+(?=&)|(?<=(?:v|i)\/)[^&\n]+|(?<=embed\/)[^"&\n]+|'''
            r'''(?<=(?:v|i)=)[^&\n]+|(?<=youtu.be\/)[^&\n]+''', re.I)
        self.youtube = build('youtube', 'v3', developerKey=self.key)

    #returns the channel name from a channel id
    def channel_name(self, id):
        #avoid asking if the ID is marked PRIVATE
        if id == "PRIVATE":
            return id

        # ask for channel w/ id
        try:
            response = self.youtube.channels().list(part='snippet', id=id).execute()
        except apiclient.errors.HttpError:
            logging.error("Bad request for youtube video id " + str(id))
            return None

        try:
            #should be the first id in the list
            response = response.get("items")[0].get("snippet").get("title")
        except IndexError:
            logging.info("Deleted or private youtube channel requested: {}".format(id))
            return "PRIVATE"
        except Exception, e:
            logging.error()
        return response

    #returns the channel name from a url
    def channel_name_url(self, url):
        return self.channel_name(self.channel_id(url))

    #returns the channel id from a url
    def channel_id(self, url):
        #first get video id
        id = self._get_id(url)
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
        return response

    def _get_id(self, url):
        # regex via: http://stackoverflow.com/questions/3392993/php-regex-to-get-youtube-video-id

        yt_id = self.regex.findall(
            url.replace('%3D', '=').replace('%26', '&').replace('%2F', '?').replace('&amp;', '&'))

        if yt_id:
            # temp fix:
            yt_id = yt_id[0].split('#')[0]
            yt_id = yt_id.split('?')[0]
            return yt_id