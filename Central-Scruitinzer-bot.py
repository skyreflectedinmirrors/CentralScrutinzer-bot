#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Central-Scruitinzer-bot.py
#main program for /r/listentothis's centralscrutinizer

import CentralScrutinizer
import CredentialsImport
import Policies
import utilitymethods as u

def main():
    cred = CredentialsImport.CRImport("testcredentials.cred")
    mypraw = u.create_multiprocess_praw(cred)
    cred['SUBREDDIT'] = 'listentothis'
    wz = u.get_subreddit(cred, mypraw, "thewhitezone")
    pol = Policies.DebugPolicy(wz)
    cs = CentralScrutinizer.CentralScrutinizer(cred, pol, "database.db")
    #cs.run()
    cs.ss.run()

if __name__ == "__main__":
    main()