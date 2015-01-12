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
* Anything after a -- is simply a comment
* Line breaks are important.  The text you send on reddit should have line breaks where outlined here (use the preview feature of RES to be sure if needed)

##Available comands

###Help
Pretty self explanitory...  Will send the querying mod a help message outlining available commands, call syntax and other options/info (such as available domains)

Syntax:  
S: help  
B: [domains]/[command]/[anything] -- With domains specified, the bot will return the list of valid domains.  If a command is specified, the bot will tell you more about it.  For any other text, the generic help message is returned

###Print
Return a list of black/whitelisted channels for a given domain and (optional) id filter

Syntax:  
S: print [whitelist]/[blacklist]  
B: domain -- the domain to use   
filter -- optional, regex is also accepted

Example:  
S: print whitelist  
B: soundcloud.com  
A

Will print any whitelisted soundcloud channel with an A in it

Example:  
S: print blacklist  
B: youtube.com  
j.*b

Result:
This will result a list of all blacklisted youtube channels that have a j followed by a b in them (with anything in between)

###Add
Add a channel or list of channels by ID or url to the appropriate black or whitelists
######Add by ID
The add by ID feature adds a list of quoted, comma separated channel id's to the appropriate black/white list

Syntax:  
S: +[blacklist]/[whitelist]  
B: domain  
"Id1", "Id2", "Id3".... "IdN" --the first id list  
"OtherID1", "OtherID2" ... "OtherID2" --another id list

Note that each line (after the first domain line) should contain a comma separated list of quoted channel titles.  

**A Note on channel titles with quotes/commas in them**  
In order to prevent mistakes on the part of moderators, any id list containing an channel id with a quote or comma inside is not acted upon. Instead the offending ids are identified, and the CS bot will respond to you asking if you really meant to black/whitelist these id's.  
This is to prevent a situation like the following:

S: +blacklist  
B: youtube.com  
"Id1", "Id2" "Id3".... "IdN"

From being parsed as: Id1, Id2" "Id3

Example:  
S: +whitelist  
B: youtube.com  
"arghdos"

Result: Add the channel arghdos to the youtube whitelist


Example:  
S: +blacklist  
B: youtube.com  
"arghdos", "arghdos1"  
"arghydos", "arghydos1"

Result: Add arghdos, arghdos1, arghydos, arghydos1 to the youtube blacklist


######Add by URL
Optionally, instead of an ID list, you may simply send a URL for each channel you want to black/whitelist (one per line)

Syntax:  
S: +[blacklist]/[whitelist]  
B: URL1 (may be a single video or the channel url)    
URL2  
...

Example:  
S: +whitelist  
B: https://www.youtube.com/watch?v=fVIFmej6VZg  
https://www.youtube.com/watch?v=AYQjxZURQwE

Result:  Add parkerh1288 and SanturronIdiota channels to the youtube whitelist

###Remove
Remove the specified channels from the black/whitelist.  Works very similarly to the add command.

######By Id

Syntax:  
S: -[blacklist]/[whitelist]  
B: domain  
"Id1", "Id2", "Id3".... "IdN" --the first id list  
"OtherID1", "OtherID2" ... "OtherID2" --another id list

Example:  
S: -whitelist  
B: youtube.com  
"arghdos"

Result: remove arghdos from the youtube whitelist

######By URL
Example:  
S: +whitelist  
B: https://www.youtube.com/watch?v=fVIFmej6VZg  
https://www.youtube.com/watch?v=AYQjxZURQwE

Result:  Remove parkerh1288 and SanturronIdiota channels to the youtube whitelist


###Update Mods
Updates the valid mod list (from whom the CS will accept commands).  This is done automatically every day (by default), but you can trigger it manually after adding new mods

Syntax:  
S: update-mods  
B: doesn't matter (but reddit requires you to put something)

Result: updates the valid mod list