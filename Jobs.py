#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Jobs.py - contains classes designed to perform the various jobs of the Central Scruitnizer Bot
#			A Job is different from an Action in that a job requires data to be loaded from reddit, and therefore
#			must go through the JobQueue
#Jobs include:
#	Loading live reddit data
#	Loading historical reddit data
#	Adding/removing channels from the white/blacklists
#	Generating reports
#	Writing/Reading from the database

from Priorities import *

#Base Job implementation
class Job(object):
    #contains the priority of the job, as well as the callback method
    def __init__(self, Priority):
        self.Priority = Priority

    #a method stub to be overridden in base classes
    def ProcessData(self):
        raise Exception("Job::ProcessData() not implemented!")

    #a method stub to be overridden in base classes
    def run(self):
        raise Exception("Job::run() not implemented!")

#Data Loaders

import thread
#Live Data Job
#	Will be spawned often, so this job should be reusable to reduce overhead
#	Needs a callback after submission to the job queue
class LiveDataJob(object):
    #contains the priority of the job, as well as the callback method
    def __init__(self, Priority):
        self.Priority = Priority
        self.Submissions = []
        self.IsUsable = True
        self.Lock = thread.allocate_lock()

    def ProcessData(self):
        #processes loaded data

        #do whatever

        #finally turn IsUsable back on
        self.Lock.acquire()
        self.IsUsable = True
        self.Lock.release()
        raise Exception("Not Implemented!")

    #a method stub to be overridden in base classes
    def run(self):
        #tell other threads we're not usuable right now
        self.Lock.acquire()
        self.IsUsable = False
        self.Lock.release()
        raise Exception("Not implemented!")


