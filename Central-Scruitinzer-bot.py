#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Central-Scruitinzer-bot.py
#main program for /r/listentothis's centralscrutinizer

import CentralScrutinizer
import CredentialsImport
import Policies
import utilitymethods as u

def main():
    #keep myself from doing something stupid before I'm ready
    #if not __debug__:
    #    raise Exception
    cred = CredentialsImport.CRImport("credentials.cred")
    cred['USERAGENT'] += ' ({})'.format(cred['SUBREDDIT'])
    mypraw = u.create_multiprocess_praw(cred)
    pol = Policies.DefaultPolicy(cred['SUBREDDIT'])
    if __debug__:
        cs = CentralScrutinizer.CentralScrutinizer(cred, pol, "database.db", True)
    else:
        cs = CentralScrutinizer.CentralScrutinizer(cred, pol, "database.db", True)
    cs.run()

if __name__ == "__main__":
    main()