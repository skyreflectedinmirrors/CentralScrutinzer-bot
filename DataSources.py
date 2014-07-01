#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# DataSources.py
#defines interfaces for the main data sources for the Central Scruiiiiitinizer bot
#in order to make the bot data source agnostic

from Jobs import Job
from DataBase import DataBase
import praw.helpers
import globaldata as g

#base data source implementation
class DataSource(object):
    def __init__(self):
        self.ready = False
    def get_data(self):
        raise Exception("DataSource::get_data() not implemented!")


class HistoricalDataSource(DataSource):
    def __init__(self, reddit, sub, limit=100):
        super(HistoricalDataSource, self).__init(self)
        self.sub = sub
        self.r = reddit
        self.limit = limit
        self.stream = praw.helpers.submission_stream(self.r, self.sub, limit = self.limit)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.stream.close()
        except Exception, e:
            g.write_error(e)

    def get_data(self):
        ret_arr = []
        for i in range(self.limit):
            ret_arr.append(self.stream.next())
        return ret_arr


#A class designed to process live feed data
class LiveDataSource(DataSource):
    def __init__(self, sub, JobQueue):
        super(LiveDataSource, self).__init(self)
        self.sub = sub
        self.JobQueue = JobQueue
