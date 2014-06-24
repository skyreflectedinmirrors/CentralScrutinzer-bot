#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#DataSources.py
#defines interfaces for the main data sources for the Central Scruiiiiitinizer bot
#in order to make the bot data source agnostic

from Jobs import Job
from DataBase import DataBase

#base data source implementation
class DataSource(object):
	def __init__(self, JobQueue, ErrorLog):
		self.ready = False
		self.JobQueue = JobQueue
		self.Log = ErrorLog
		
	def addJob(Job):
		try:
			self.JobQueue.put((Job.Priority, Job))
		except TypeError, e:
			Log.log("Submitted job was not of right type: " + str(e)
			
#A class designed to scan historical data
class HistoricalDataSource(DataSource):
	def __init__(self, Reddit, JobQueue, ErrorLog):
		super(HistoricalDataSource, self).__init(self, JobQueue, ErrorLog)
		self.Reddit = Reddit
		
#A class designed to process live feed data
class LiveDataSource(DataSource):
	def __init__(self, Reddit, JobQueue, ErrorLog):
		super(LiveDataSource, self).__init(self, Reddit, JobQueue, ErrorLog)
		self.Reddit = Reddit
		
class DataBaseSource(DataSource):
	def __init__(self, DataBase, JobQueue, ErrorLog):
		super(LiveDataSource, self).__init(self, Reddit, JobQueue, ErrorLog)
		self.DataBase = DataBase
		