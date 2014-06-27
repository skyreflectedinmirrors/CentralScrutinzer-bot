#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Priorities.py - contains a list of job priorities that can be modified according to your tastes
#The lower the priority, the quicker the job will be excecuted

#the basic scheme here is that live data / black/whitelisting is the most important
#followed by moderater requested actions
#followed by historical data work

#high priority
LiveDataPriority = 0
BlacklistPriority = 0
WhitelistPriority = 0
BanUserPriority = 0

#medium priority
RequestedReportPriority = 1
HistoricalDataPriority = 2
HistoricalDataPruning = 2

#low priority
WeeklyReportPriority = 3