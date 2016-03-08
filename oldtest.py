# Test-Suite.py

# I'm a man who (now) believes in unit test driven development, so this is where the unit tests live!

import praw
from CredentialsImport import CRImport
import Actions as a
import utilitymethods as u
import DataExtractors
import Blacklist
import DataBase
import datetime


def testMultiprocess(credentials):
    # create my reddit
    return u.create_multiprocess_praw(credentials)


def testRemoveComment(comment):
    # spawn an action
    print "Remove Comment:"
    val = a.remove_comment(comment)
    print "Passed" if val else "Failed"
    return val


def testGetComments(sub):
    print "Get Comments:"
    post = a.get_posts(sub, 1)
    comments = a.get_comments(post.next())
    print "Passed" if comments != None and len(comments) and comments[0].body == "test comment" else "Failed"
    return comments != None


def testMakeComment(post):
    # spawn an action
    print "Make Comment:"
    comment = a.make_comment(post, "test comment")
    print "Passed" if comment else "Failed"
    return comment


def testGetPosts(sub):
    # spawn an action
    print "Get Posts:"
    posts = a.get_posts(sub)
    print "Passed" if posts else "Failed"
    return posts != None


def testMakePostText(sub):
    # spawn a  action
    print "Make Post:"
    post = a.make_post_text(sub, "testpost", "please ignore")
    print "Passed" if post else "Failed"
    return post


def testRemovePost(sub, post):
    # spawn a Removal action
    print "Remove Post:"
    val = a.remove_post(post)
    print "Passed" if val else "Failed"
    return val


def testBanUser(sub, user):
    # spawn a Removal action
    print "Ban user:"
    val = a.ban_user(sub, "test", user)
    print "Passed" if val else "Failed"
    return val


def testUnBanUser(sub, user):
    # spawn a Removal action
    print "Unban user: "
    val = a.unban_user(sub, user)
    print "Passed" if val else "Failed"
    return val


def testYoutubeExtractor(credentials):
    y = DataExtractors.YoutubeExtractor(credentials['GOOGLEID'])
    id_to_response = {
        "https://www.youtube.com/watch?v=-vihDAj5VkY": ("arghdos", "http://www.youtube.com/user/arghdos"),
        "https://m.youtube.com/watch?v=G4ApQrbhQp8": ("IGN", "http://www.youtube.com/user/IGN"),
        "http://youtu.be/Cg9PWSHL4Vg": ("Karen Jones", "http://www.youtube.com/user/Karen Jones"),
        "https://www.youtube.com/watch?v=iMoNJ_UiRQY": "PRIVATE",
        "https://www.youtube.com/watch?v=WkqziN8F8oM": ("BBrucker2", "http://www.youtube.com/user/BBrucker2")
    }

    print "Youtube Extractor:"
    for id, response in id_to_response.iteritems():
        if y.channel_id(id) != response:
            print "Failed on ", id, response
            return False

    print "Passed"
    return True


def testSoundcloudExtractor(credentials):
    y = DataExtractors.SoundCloudExtractor(credentials['SOUNDCLOUDID'])

    id_to_response = {
        "http://soundcloud.com/matt-spencer-37": ("Morty Spin", "http://soundcloud.com/matt-spencer-37"),
        "http://soundcloud.com/maggiesmithmusic/100-needles-for-zil": (
            "MaggieSmithMusic", "http://soundcloud.com/maggiesmithmusic"),
        "http://soundcloud.com/natebelasco/kanye-west-black-skinhead-vs": (
            "Nate Belasco", "http://soundcloud.com/natebelasco"),
        "http://soundcloud.com/NOTAREALURL": None
    }

    print "Soundcloud Extractor:"
    for id, response in id_to_response.iteritems():
        if y.channel_id(id) != response:
            print "Failed on: ", id, response
            return False

    print "Passed"
    return True


def testBandcampExtractor(credentials):
    y = DataExtractors.BandCampExtractor()

    id_to_response = {
        "http://wayneszalinski.bandcamp.com/": ("wayneszalinski.bandcamp.com", "http://wayneszalinski.bandcamp.com"),
        "http://www.sleepwalkersbandcamp.bandcamp.com/": (
            "sleepwalkersbandcamp.bandcamp.com", "http://www.sleepwalkersbandcamp.bandcamp.com"),
        "http://rivka.bandcamp.com/track/better-days": ("rivka.bandcamp.com", "http://rivka.bandcamp.com"),
        "jghkgkjgjhjhg.com": ("jghkgkjgjhjhg.com", "jghkgkjgjhjhg.com"),
        "jghkgkjgjhjhg": ("jghkgkjgjhjhg", "jghkgkjgjhjhg"),
        "http://rivka.bandcamp.com/track/better-days/https://www.youtube.com/watch?v=RVLwCLGz5hM": (
            "rivka.bandcamp.com", "http://rivka.bandcamp.com")
    }

    print "Bandcamp Extractor:"
    for id, response in id_to_response.iteritems():
        if y.channel_id(id) != response:
            print "Failed on ", id, response
            return False
    print "Passed"
    return True


def test_create_wiki(reddit, sub, page):
    wiki = a.get_or_create_wiki(reddit, sub, page)
    print "Wiki get/create: " + str(wiki != None)
    return wiki


def test_write_wiki(wiki):
    write_test = a.write_wiki_page(wiki, "test")
    print "Wiki write: " + str(write_test)
    return write_test


def test_get_wiki(wiki):
    read_test = a.get_wiki_content(wiki)
    print "Wiki read: " + str(read_test == "test")
    return read_test == "test"


def test_black_list(credentials):
    # remove old database
    try:
        os.remove("test_database.db")
    except:
        pass
    with DataBase.DataBaseWrapper("test_database.db") as db:
        pass
    y = DataExtractors.YoutubeExtractor(credentials['GOOGLEID'])
    ids = ["https://www.youtube.com/watch?v=-vihDAj5VkY", "http://youtu.be/Cg9PWSHL4Vg",
           "https://www.youtube.com/watch?v=WkqziN8F8oM"]
    blist = Blacklist.Blacklist(y, "test_database.db")
    if not blist:
        print "Blacklist creation: Failed"
        return False
    print "Blacklist creation: Passed"

    #make sure the blacklist is empty from any previously failed tests
    if blist.get_blacklisted_channels(""):
        blist.remove_blacklist(blist.get_blacklisted_channels(""))

    if blist.get_whitelisted_channels(""):
        blist.remove_blacklist(blist.get_whitelisted_channels(""))

    #test adding to blacklist
    check = blist.add_blacklist(ids[0:2])
    check = len(check) == 0 and all(
        val == Blacklist.BlacklistEnums.Blacklisted for val in blist.check_blacklist(urls=ids[0:2]))
    check = check and blist.check_blacklist(urls=ids[2])[0] == Blacklist.BlacklistEnums.NotFound
    if not check:
        print "Blacklist addition: Failed"
        return False
    print "Blacklist addition: Passed"

    #test channels
    channels = blist.get_blacklisted_channels("arghdos")[0]
    if len(channels) > 0 and channels[0] == "arghdos":
        print "Blacklist channel get: Passed"
    else:
        print "Blacklist channel get: Failed"
        return False

    #test blacklist removal
    blist.remove_blacklist_url(ids[0])
    check = blist.check_blacklist(urls=ids[0])[0] == Blacklist.BlacklistEnums.NotFound
    if not check:
        print "Blacklist removal: Failed"
        return False
    print "Blacklist removal: Passed"

    #test whitelist
    blist.add_whitelist(ids[0])
    check = blist.check_blacklist(urls=ids[0])[0] == Blacklist.BlacklistEnums.Whitelisted
    if not check:
        print "Whitelist addition: Failed"
        return False
    print "Whitelist addition: Passed"

    #test whitelist removal / basic behaviour
    blist.remove_whitelist_url(ids[0])
    check = blist.check_blacklist(urls=ids[0])[0] == Blacklist.BlacklistEnums.NotFound
    if not check:
        print "Whitelist removal: Failed"
        return False
    print "Whitelist removal: Passed"

    #now test blacklist loading
    blist2 = Blacklist.Blacklist(y, "test_database.db")
    if blist2.check_blacklist(urls=ids[1])[0] != Blacklist.BlacklistEnums.Blacklisted:
        print "Blacklist load: Failed"
        return False
    print "Blacklist load: Passed"
    blist.remove_blacklist_url(ids[1])
    return True


def test_send_message(reddit, credentials):
    if a.send_message(reddit, credentials['ALTUSER'], "test", "testmessage"):
        print "Test Message Send: Passed"
        return True
    else:
        print "Test Message Send: Failed"
        return False


def test_get_message(credentials):
    r = praw.Reddit(user_agent=credentials['USERAGENT'])
    r.login(username=credentials['ALTUSER'], password=credentials['ALTPASS'])
    messages = a.get_unread(r)
    message = messages.next()
    success = message.author.name == 'centralscruuutinizer' and message.body == "testmessage" and message.subject == "test"
    if success:
        print "Test Get Message: Passed"
        return True
    print "Test Get Message: Failed"
    return True


def test_approve_post(post):
    print "Approve Post:"
    if a.approve_post(post):
        print "Passed"
        return True
    print "Failed"
    return False

def test_get_by_id(praw, ids):
    list = a.get_by_ids(praw, ids)
    if list:
        list = [l for l in list]
        if len(list):
            print "Passed"
            return True
    print "Failed"
    return False


import ScanSub
import Policies
import CentralScrutinizer


def test_scan_sub():
    try:
        os.remove("test_database.db")
    except:
        pass
    credentials = CRImport("TestCredentials.cred")
    credentials["SUBREDDIT"] = "centralscrutinizer"

    # clear old subs
    u.clear_sub(credentials, "thewhitezone")
    u.clear_sub(credentials, "centralscrutinizer")

    #get subs
    mypraw = u.create_multiprocess_praw(credentials)
    wz = u.get_subreddit(credentials, mypraw, "thewhitezone")
    cz = u.get_subreddit(credentials, mypraw, "centralscrutinizer")
    pol = Policies.DebugPolicy(wz)

    print "Starting ScanSub tests..."
    print "Simple blacklist identification:"
    #h'ok here we go.
    #first we'll create three posts from a black/whitelisted channel and a not found
    with DataBase.DataBaseWrapper("test_database.db") as db:
        entries = [
            ("arghdos", "youtube.com", "http://www.youtube.com/user/arghdos", Blacklist.BlacklistEnums.Whitelisted, 0),
            ("IGN", "youtube.com", "http://www.youtube.com/user/IGN", Blacklist.BlacklistEnums.Blacklisted, 0),
            ("Karen Jones", "youtube.com", "http://www.youtube.com/user/Karen Jones", Blacklist.BlacklistEnums.NotFound,
             0)]
        db.add_channels(entries)

        #create scrutinizer
        cs = CentralScrutinizer.CentralScrutinizer(credentials, pol, "test_database.db")
        ss = cs.ss

        #now make posts
        urls = ["https://www.youtube.com/watch?v=-vihDAj5VkY", "https://m.youtube.com/watch?v=G4ApQrbhQp8",
                "http://youtu.be/Cg9PWSHL4Vg"]
        ids = []
        for i in range(len(urls)):
            ids.append(a.make_post_url(cz, url=urls[i], title=str(i)).id)

        #ok, now scan
        ss.scan(3)

        #next check for a 0//whitelist, 1//blacklist
        posts = a.get_posts(wz, 3)
        one = posts.next()
        two = posts.next()

        if (one.title == "0//whitelist") and (two.title == "1//blacklist"):
            print "Passed"
        else:
            print "Failed"
            return False

        print "Reddit record:"
        results = db.get_reddit(date_added=(datetime.datetime.now() - datetime.timedelta(days=1)))
        if len([p for p in results if p[0] in ids]) == 2:
            print "Passed"
        else:
            print "Failed"
            return False

        result = db.newest_reddit_entries(1)
        ss.last_seen = result.next()[0]
        print "Found old:"
        result = ss.scan(3)
        if result == ScanSub.scan_result.FoundOld:
            print "Passed"
        else:
            print "Failed"
            return False


from time import sleep

def test_strike_counter():
    try:
        os.remove("test_database.db")
    except:
        pass
    credentials = CRImport("TestCredentials.cred")

    mypraw = u.create_multiprocess_praw(credentials)
    pol = Policies.DebugPolicy(None)
    sub = u.get_subreddit(credentials, mypraw)

    cs = CentralScrutinizer.CentralScrutinizer(credentials, pol, "test_database.db")
    scount = cs.scount

    print "Simple strike count test:"
    #make post
    post = a.make_post_url(sub, "test", "https://www.youtube.com/watch?v=vmT0lCfybR4")

    with DataBase.DataBaseWrapper("test_database.db") as db:
        db.add_reddit([(post.name, "arghdos", "youtube", datetime.datetime.today())])
        db.add_channels([("arghdos", "youtube", "http://www.youtube.com/user/arghdos", Blacklist.BlacklistEnums.NotFound, 2)])

    post.set_flair("test")

    #delete
    post.delete()

    #run counter
    scount.scan()

    #check strikes
    with DataBase.DataBaseWrapper("test_database.db") as db:
        result = db.get_channels(id_filter="arghdos", return_strikes=True)[0][-1]

    if result != 3:
        print "Failed"
        return False

    with DataBase.DataBaseWrapper("test_database.db") as db:
        result = db.get_blacklist([("arghdos", "youtube")])[0] == Blacklist.BlacklistEnums.Blacklisted
    if not result:
        print "Failed"
        return False

    #set to non-blacklisted and run again to check deletion
    db.set_blacklist([("arghdos", "youtube")], Blacklist.BlacklistEnums.NotFound)

     #run counter
    scount.scan()

    #check strikes
    with DataBase.DataBaseWrapper("test_database.db") as db:
        result = db.get_channels(id_filter="arghdos", return_strikes=True)[0][-1]

    if result != 3:
        print "Failed"
        return False

    print "Passed"





def test_blacklist_query():
    try:
        os.remove("test_database.db")
    except:
        pass
    credentials = CRImport("TestCredentials.cred")
    credentials["SUBREDDIT"] = "centralscrutinizer"

    # swap usernames
    temp = credentials['USERNAME']
    credentials['USERNAME'] = credentials['ALTUSER']
    credentials['ALTUSER'] = temp

    temp = credentials['PASSWORD']
    credentials['PASSWORD'] = credentials['ALTPASS']
    credentials['ALTPASS'] = temp

    #get subs
    mypraw = u.create_multiprocess_praw(credentials)
    pol = Policies.DebugPolicy(None)

    #alt user
    my_handler = praw.handlers.MultiprocessHandler()
    r = praw.Reddit(user_agent="message-send-test", handler=my_handler)
    r.login(username=credentials['ALTUSER'], password=credentials['ALTPASS'])

    #mark all old as read
    for x in a.get_unread(mypraw, None):
        x.mark_as_read()
    for x in a.get_unread(r, None):
        x.mark_as_read()

    class author_dummy:
        def __init__(self):
            self.name = credentials['ALTUSER']

    class message_dummy:
        def __init__(self, text, id):
            self.author = author_dummy()
            self.body = text
            self.id = id
            self.subject = "test"

        def mark_as_read(self):
            pass

    print "Starting Blacklist Query tests..."
    #h'ok here we go.
    #first we'll create three posts from a black/whitelisted channel and a not found
    with DataBase.DataBaseWrapper("test_database.db") as db:
        entries = [
            ("arghdos", "youtube.com", "http://www.youtube.com/user/arghdos", Blacklist.BlacklistEnums.Whitelisted, 0),
            ("IGN", "youtube.com", "http://www.youtube.com/user/IGN", Blacklist.BlacklistEnums.Blacklisted, 0),
            ("Karen Jones", "youtube.com", "http://www.youtube.com/user/Karen Jones", Blacklist.BlacklistEnums.NotFound,
             0)]
        db.add_channels(entries)

        #create scrutinizer
        cs = CentralScrutinizer.CentralScrutinizer(credentials, pol, "test_database.db")
        bq = cs.bquery

        print "Testing Add/Remove..."
        #test print functions
        id = 0
        message = message_dummy("add\nwhitelist\nhttp://soundcloud.com/maggiesmithmusic/100-needles-for-zil", id)
        id += 1
        result = bq.process_message(message)
        r_list = db.get_channels(blacklist=Blacklist.BlacklistEnums.Whitelisted, domain="soundcloud",
                                 id_filter="MaggieSmithMusic")
        if not len(r_list) or result != "":
            print "Failed"
            return False

        message = message_dummy("remove\nwhitelist\nMaggieSmithMusic\nsoundcloud", id)
        id += 1
        result = bq.process_message(message)
        #result should be "" and "" should be listed in the message
        r_list = db.get_channels(blacklist=Blacklist.BlacklistEnums.Whitelisted, domain="soundcloud",
                                 id_filter="MaggieSmithMusic")
        if len(r_list) or result != "":
            print "Failed"
            return False

        message = message_dummy("add\nblacklist\nhttp://soundcloud.com/maggiesmithmusic/100-needles-for-zil", id)
        id += 1
        result = bq.process_message(message)
        r_list = db.get_channels(blacklist=Blacklist.BlacklistEnums.Blacklisted, domain="soundcloud",
                                 id_filter="MaggieSmithMusic")
        if not len(r_list) or result != "":
            print "Failed"
            return False

        message = message_dummy("remove\nblacklist\nhttp://soundcloud.com/maggiesmithmusic/100-needles-for-zil", id)
        id += 1
        result = bq.process_message(message)
        #result should be "" and "" should be listed in the message
        r_list = db.get_channels(blacklist=Blacklist.BlacklistEnums.Blacklisted, domain="soundcloud",
                                 id_filter="MaggieSmithMusic")
        if len(r_list) or result != "":
            print "Failed"
            return False
        message.mark_as_read()
        print "Add/Remove passed"

        #test help message
        print "Testing Help Message..."
        message = message_dummy("testmessage", id)
        id += 1
        result = bq.process_message(message)
        #result should be "unknown", and we should get the help message
        message = [m for m in a.get_unread(r)][-1]
        if not message.body.startswith('Sorry, I did not recognize your query.') or result != "unknown":
            print "Failed"
            return False
        message.mark_as_read()
        sleep(30)

        message = message_dummy("help", id)
        id += 1
        result = bq.process_message(message)
        #result should be "", and we should get the help message
        message = [m for m in a.get_unread(r)][-1]
        if message.body.startswith("Available Commands:") and result == "":
            print "Passed"
        else:
            print "Failed"
            return False
        message.mark_as_read()
        print "Testing print statement..."
        sleep(30)

        message = message_dummy("print\nwhitelist\nyoutube", id)
        id += 1
        #test print functions
        result = bq.process_message(message)
        #result should be "", and we should get arghdos back
        message = [m for m in a.get_unread(r)][-1]
        if message.body != "Results:\narghdos" or result != "":
            print "Failed"
            return False
        message.mark_as_read()
        sleep(30)

        message = message_dummy("print\nwhitelist\nyoutube.com\n\"danny\"", id)
        id += 1
        result = bq.process_message(message)
        #result should be "" and "" should be listed in the message
        message = [m for m in a.get_unread(r)][-1]
        if message.body != "Results:\n" or result != "":
            print "Failed"
            return False
        message.mark_as_read()
        sleep(30)

        message = message_dummy("print\nblacklist\nyoutube.com", id)
        id += 1
        result = bq.process_message(message)
        #result should be "", and we should get arghdos back
        message = [m for m in a.get_unread(r)][-1]
        if message.body != "Results:\nIGN" or result != "":
            print "Failed"
            return False
        message.mark_as_read()
        sleep(30)

        message = message_dummy("print\nBlacklist\nyoutube\ndanny", id)
        id += 1
        result = bq.process_message(message)
        #result should be "" and "" should be listed in the message
        message = [m for m in a.get_unread(r)][-1]
        if message.body != "Results:\n" or result != "":
            print "Failed"
            return False
        message.mark_as_read()
        print "Passed"
        print "Test update mods..."

        sleep(30)
        #finally update-mods
        message = message_dummy("update-mods", id)
        id += 1
        result = bq.process_message(message)
        #result should be "" and "" should be listed in the message
        message = [m for m in a.get_unread(r)][-1]
        if message.body != "Mod update successful!" or result != "":
            print "Failed"
            return False
        message.mark_as_read()
        print "Passed"
    return True


def error_tests():
    # kill the multiprocess
    os.system("taskkill /f /im praw-multiprocess.exe")
    try:
        os.remove("test_database.db")
    except:
        pass
    credentials = CRImport("TestCredentials.cred")
    credentials["SUBREDDIT"] = "centralscrutinizer"

    #clear old subs
    u.clear_sub(credentials, "thewhitezone")
    u.clear_sub(credentials, "centralscrutinizer")

    #get subs
    mypraw = u.create_multiprocess_praw(credentials)
    wz = u.get_subreddit(credentials, mypraw, "thewhitezone")
    cz = u.get_subreddit(credentials, mypraw, "centralscrutinizer")
    pol = Policies.DebugPolicy(wz)

    print "Starting ScanSub tests..."
    print "Simple blacklist identification:"
    #h'ok here we go.

    #create scrutinizer
    cs = CentralScrutinizer.CentralScrutinizer(credentials, pol, "test_database.db")
    ss = cs.ss

    #test error
    print "Error Test:"
    result = ss.scan(1)
    if result != ScanSub.scan_result.Error:
        print "Failed"
        return False

    print "Passed"


import os


def data_base_tests():
    """
    :type db: Database.Database
    :return:
    """
    try:
        os.remove("test_database.db")
    except:
        pass
    try:
        with DataBase.DataBaseWrapper("test_database.db", False) as db:
            print "Database Creation:"
            if not db._DataBase__create_table():
                return False
            print "Passed"

            print "Check Empty:"
            val = db.check_channel_empty() and db.check_reddit_empty()
            if not val:
                print "Failed"
                return False
            print "Passed"

            print "Database Channel Add:"
            # channel_id, channel_url, blacklist, three_strikes
            channels = [('arghdos', 'youtube.com', 'https://www.youtube.com/user/arghdos', '0', '0'),
                        ("wayneszalinski.bandcamp.com", 'bandcamp.com', "wayneszalinski.bandcamp.com", '0', '1'),
                        ("https://soundcloud.com/matt-spencer-37", 'soundcloud.com', "Morty Spin", '1', '0')]
            db.add_channels(channels)
            print "Passed"

            print "Database Channel Check:"
            result = db.channel_exists([('arghdos', 'youtube.com'), ("wayneszalinski.bandcamp.com", 'bandcamp.com'),
                                        ('dummy', 'dummy.com')])
            if result != [True, True, False]:
                print "Failed"
                return False
            print "Passed"

            print "Database Channel Get:"
            result = db.get_channels(domain='youtube.com', blacklist=0)
            if len(result) != 1 or result[0][0] != 'arghdos' or result[0][1] != 'youtube.com':
                print "Failed"
                return False
            result = db.get_channels(domain='youtube.com', blacklist=0, id_filter='test')
            if len(result):
                print "Failed"
                return False
            result = db.get_channels(blacklist=0, strike_count=1)
            if len(result) != 1 and result[0][0] != "wayneszalinski.bandcamp.com":
                print "Failed"
                return False
            print "Passed"

            print "Database Channel Blacklist Set:"
            db.set_blacklist([('arghdos', 'youtube.com')], 1)
            result = db.get_channels(blacklist=1, domain='youtube.com', id_filter='arghdos')
            if not len(result):
                print "Failed"
                return False
            print "Passed"

            print "Database Channel Blacklist Get:"
            result = db.get_blacklist([('arghdos', 'youtube.com')])
            if not len(result) or result[0] != 1:
                print "Failed"
                return False
            print "Passed"

            print "Database Set Strikes:"
            db.set_strikes([('arghdos', 'youtube.com', 2)])
            result = db.get_channels(strike_count=2, id_filter='arghdos')
            if len(result) == 0:
                print "Failed"
                return False
            print "Passed"

            print "Database Add Strike:"
            db.add_strike([('arghdos', 'youtube.com')])
            result = db.get_channels(strike_count=3, id_filter='arghdos')
            if len(result) == 0:
                print "Failed"
                return False

            print "Add Reddit:"
            #short_url, channel_id, domain, date_added
            reddit_entries = [('dsadas', 'arghdos', 'youtube.com', datetime.datetime.now()),
                              ('sdafasf', 'arghdos', 'youtube.com',
                               datetime.datetime.now() - datetime.timedelta(days=5))]
            db.add_reddit(reddit_entries)
            print "Passed"

            print "Reddit Check:"
            result = db.get_reddit('arghdos', 'youtube.com')
            if [r[0] for r in result] != ['dsadas', 'sdafasf']:
                print "Failed"
                return False
            print "Passed"

            print "Newer Than:"
            result = db.get_reddit(date_added=(datetime.datetime.now() - datetime.timedelta(days=1)))
            if len([r for r in result if r[0] == "sdafasf"]):
                print "Failed"
                return False
            print "Passed"

            print "Remove Older Than:"
            db.remove_reddit_older_than(1)
            result = db.get_reddit('arghdos', 'youtube.com')
            if len([r for r in result if r[0] == "sdafasf"]):
                print "Failed"
                return False
            print "Passed"

            print "Remove Reddit:"
            db.remove_reddit(["dsadas"])
            result = db.get_reddit('arghdos', 'youtube.com')
            if len([r for r in result if r[0] == "dsadas"]):
                print "Failed"
                return False
            print "Passed"

            print "Database Tests Complete"
            return True

    except Exception, e:
        print "Failed"
        return False


def test_xpost(post, credentials, praw, sub):
    mysub = u.get_subreddit(credentials, praw, sub)
    val = a.xpost(post, mysub, "test")
    print "Xpost:"
    if val:
        print "Passed"
        return True
    else:
        print "Failed"
        return False


def test_get_moderators(r, sub):
    print "Test Get Mods:"
    mods = a.get_mods(r, sub)
    if len([u for u in mods if any(name == u.name for name in ['arghdos', 'centralscruuutinizer'])]) == 2:
        print "Passed"
        return True
    print "Failed"
    return False


def main():

    passed = True
    # import credentials
    credentials = CRImport("TestCredentials.cred")

    #run multiproc handler test (run before scansub tests as that kills our praw-multiproc as a test)
    r2 = testMultiprocess(credentials)
    passed = passed and r2 is not None

    #db tests
    passed &= data_base_tests()

    #create my reddit
    r = u.create_praw(credentials)

    sub = r.get_subreddit(credentials['SUBREDDIT'])

    passed &= testBandcampExtractor(credentials)

    passed &= testSoundcloudExtractor(credentials)

    passed &= testYoutubeExtractor(credentials)

    passed &= test_black_list(credentials)

    #run MakePost test
    post = testMakePostText(sub)
    passed &= post is not None

    #run RemovePost test
    passed &= testBanUser(sub, "StudabakerHoch")

    #run RemovePost test
    passed &= testUnBanUser(sub, "StudabakerHoch")

    #run get post test
    passed &= testGetPosts(sub)

    #run make comment test
    comment = testMakeComment(post)
    passed &= comment is not None

    #run get comments post
    passed &= testGetComments(sub)

    #run make comment test
    passed &= testRemoveComment(comment)

    #run approval test
    passed &= test_approve_post(post)

    #get by id
    passed &= test_get_by_id(r, [post.name])

    #xpost
    passed &= test_xpost(post, credentials, r, "centralscrutinizer")

    #run RemovePost test
    passed &= testRemovePost(sub, post)

    #run message tests
    passed &= test_send_message(r, credentials)
    passed &= test_get_message(credentials)

    #run wiki tests
    wiki = test_create_wiki(r, sub, "test")
    passed &= wiki is not None
    passed &= test_write_wiki(wiki)
    passed &= test_get_wiki(wiki)

    #moderators
    passed &= test_get_moderators(r, sub)

    #ScanSub tests
    passed &= test_scan_sub()

    #BQ tests
    passed &= test_blacklist_query()

    #strike counter
    passed &= test_strike_counter()

if __name__ == "__main__":
    main()
