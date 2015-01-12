CentralScrutinzer-bot
=====================

A spam fighting reddit bot


#What is the Central Scruuuuuutinizer?
The [Central Scrutinizer](https://www.youtube.com/watch?v=ljnT49jU9vM) monitors individual subreddits in an attempt to combat spam.
Certain heuristics are utilized to determine whether a channel appears to be spamming your subreddit, if so, the channel is automatically added to the blacklist and future posts from that channel will be removed.


##What kind of heuristics do we use?
I'm not gonna tell you.  Of course, the code is publically available, so you know...

##Can I use the CentralScrutinizer on my subreddit?
Yes!  You will need to run your own instance however.  The Central Scruitinzer depends on the following non-standard packages, which should be installed via pip:
praw -- version >= 2.1.19
requests -- version >= 2.4.3
google-api-python-client -- version >= 1.3.1 (if not installed, youtube channels will not be monitered)
soundcloud -- version >= 0.4.1 (if not installed, soundcloud channels will not be monitered)
httplib2 -- version >= 0.9

#Setup
##Credentials file
The first task you will need to do is to create a credentials file.  I have provided a sample in SampleCredentials.cred.  Note anything after a # is ignored

1.  Change the subreddit field to whichever subreddit you want to monitor, e.g.:
	SUBREDDIT = listentothis #the subreddit to watch
	
2.  Obtain a [Soundcloud API key](https://developers.soundcloud.com/).  Replace the None part of the Soundcloud API line with this key

3.  Obtain a [Google API key](https://developers.google.com/youtube/v3/getting-started).  Replace the None part of the GOOGLEID line with this key

##Policy file
This file allows you to change the various delays/settings/preferences of the CS bot to your liking.  You are warned that poor decisions here can negatively affect the performance (or even break) the bot!
The various switches should be decently well documented, but if you have a question, just ask.  Further, some (really bad) choices will simply be ignored by the program.

#Mod Interaction
The nicest feature (in my biased opinion) is the ability of the any mod of your sub to add/remove/query the blacklist simply by sending a message to the CS Bot instance in question!
This section will detail the various mod commands, and give examples!

**Note**: 
* In this section S: is short for the subject line and B: for the message body.  
* [option1]/[option2]... indicates that one of the two (or more) options should be selected
* Anything in parentheses (or after parenthetic text) is simply a comment
* Line breaks are important.  The text you send on reddit should have line breaks where outlined here (use the preview feature of RES to be sure if needed)

##Available comands

###Help
Pretty self explanitory...  Will send the querying mod a help message outlining available commands, call syntax and other options/info (such as available domains)

###Print
Return a list of black/whitelisted channels for a given domain and (optional) id filter

Syntax:
S: print [whitelist]/[blacklist]
B: domain (the domain to use)
filter (optional, regex is also accepted)

Examples:
S: print blacklist
B: youtube.com  
j.*b

Result:
This will result a list of all blacklisted youtube channels that 