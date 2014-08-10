# Test-Suite.py

# I'm a man who (now) believes in unit test driven development, so this is where the unit tests live!

import praw
from CredentialsImport import CRImport
import Actions as a
import globaldata as g
import utilitymethods as u
import DataExtractors
import Blacklist
import DataBase
import datetime


def store_post(post):
    global my_post
    my_post = post
    print "my_post = " + my_post.title


def store_comment(comment):
    global my_comment
    my_comment = comment
    print "my_comment = " + my_comment.id


def print_posts(posts):
    try:
        for posts in posts:
            print posts.title
    except:
        pass


def print_comments(comments):
    try:
        for comment in comments:
            print comment.text
    except:
        pass


def testMultiprocess(credentials):
    #create my reddit
    return u.create_multiprocess_praw(credentials)


def testRemoveComment(comment):
    #spawn an action
    a.remove_comment(comment)


def testGetComments(post):
    a.get_comments(post, print_comments)


def testMakeComment(post):
    #spawn an action
    a.make_comment(post, "test comment", store_comment)


def testGetPosts(sub):
    #spawn an action
    a.get_posts(sub, print_posts)


def testMakePostText(sub):
    #spawn a  action
    a.make_post_text(sub, "testpost", "please ignore", store_post)


def testRemovePost(sub, post=None):
    #spawn a Removal action
    a.remove_post(post)


def testBanUser(sub, user):
    #spawn a Removal action
    a.ban_user(sub, "test", user)


def testUnBanUser(sub, user):
    #spawn a Removal action
    a.unban_user(sub, user)


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
        "http://soundcloud.com/maggiesmithmusic/100-needles-for-zil": ("MaggieSmithMusic", "http://soundcloud.com/maggiesmithmusic"),
        "http://soundcloud.com/natebelasco/kanye-west-black-skinhead-vs": ("Nate Belasco", "http://soundcloud.com/natebelasco"),
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
        "http://www.sleepwalkersbandcamp.bandcamp.com/": ("sleepwalkersbandcamp.bandcamp.com", "http://www.sleepwalkersbandcamp.bandcamp.com"),
        "http://rivka.bandcamp.com/track/better-days": ("rivka.bandcamp.com", "http://rivka.bandcamp.com"),
        "jghkgkjgjhjhg.com": ("jghkgkjgjhjhg.com", "jghkgkjgjhjhg.com"),
        "jghkgkjgjhjhg": ("jghkgkjgjhjhg", "jghkgkjgjhjhg"),
        "http://rivka.bandcamp.com/track/better-days/https://www.youtube.com/watch?v=RVLwCLGz5hM": ("rivka.bandcamp.com", "http://rivka.bandcamp.com")
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
    #remove old database
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
    check = len(check) == 0 and all(blist.check_blacklist(val) == Blacklist.BlacklistEnums.Blacklisted for val in ids[0:2])
    check = check and blist.check_blacklist(ids[2]) == Blacklist.BlacklistEnums.NotFound
    if not check:
        print "Blacklist addition: Failed"
        return False
    print "Blacklist addition: Passed"

    #test channels
    channels = blist.get_blacklisted_channels("arghdos")
    if len(channels) > 0 and channels[0] == "arghdos":
        print "Blacklist channel get: Passed"
    else:
        print "Blacklist channel get: Failed"
        return False

    #test blacklist removal
    blist.remove_blacklist_url(ids[0])
    check = blist.check_blacklist(ids[0]) == Blacklist.BlacklistEnums.NotFound
    if not check:
        print "Blacklist removal: Failed"
        return False
    print "Blacklist removal: Passed"

    #test whitelist
    blist.add_whitelist(ids[0])
    check = blist.check_blacklist(ids[0]) == Blacklist.BlacklistEnums.Whitelisted
    if not check:
        print "Whitelist addition: Failed"
        return False
    print "Whitelist addition: Passed"

    #test whitelist removal / basic behaviour
    blist.remove_whitelist_url(ids[0])
    check = blist.check_blacklist(ids[0]) == Blacklist.BlacklistEnums.NotFound
    if not check:
        print "Whitelist removal: Failed"
        return False
    print "Whitelist removal: Passed"

    #now test blacklist loading
    blist2 = Blacklist.Blacklist(y, "test_database.db")
    if blist2.check_blacklist(ids[1]) != Blacklist.BlacklistEnums.Blacklisted:
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

            print "Database Channel Add:"
            #channel_id, channel_url, blacklist, three_strikes
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
            db.set_blacklist([('arghdos', 'youtube.com', 1)])
            result = db.get_channels(blacklist=1, domain='youtube.com', id_filter='arghdos')
            if not len(result):
                print "Failed"
                return False
            print "Passed"

            print "Database Set Strikes:"
            db.set_strikes([('arghdos', 'youtube.com', 2)])
            result = db.get_channels(strike_count=2, id_filter='arghdos')
            if len(result) == 0:
                print "Failed"
                return False

            print "Add Reddit:"
            #short_url, channel_id, domain, date_added
            reddit_entries = [('dsadas', 'arghdos', 'youtube.com', datetime.datetime.now()),
                              ('sdafasf', 'arghdos', 'youtube.com', datetime.datetime.now() - datetime.timedelta(days=5))]
            db.add_reddit(reddit_entries)
            print "Passed"

            print "Reddit Check:"
            result = db.get_reddit('arghdos', 'youtube.com')
            if [r[0] for r in result] != ['dsadas', 'sdafasf']:
                print "Failed"
                return False
            print "Passed"

            print "Remove Older Than:"
            db.remove_reddit_older_than(1)
            result = db.get_reddit('arghdos', 'youtube.com')
            if len([r for r in result if r[0] == "sdafasf"]):
                print "Failed"
                #return False
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


def main():
    g.init()
    g.close()
    #import credentials
    credentials = CRImport("TestCredentials.cred")

    data_base_tests()

    #create my reddit
    r = u.create_praw(credentials)

    sub = r.get_subreddit(credentials['SUBREDDIT'])

    testBandcampExtractor(credentials)

    testSoundcloudExtractor(credentials)

    testYoutubeExtractor(credentials)

    wiki = test_create_wiki(r, sub, "test")
    test_write_wiki(wiki)
    test_get_wiki(wiki)

    test_black_list(credentials)

    #run MakePost test
    testMakePostText(sub)

    #run RemovePost test
    testBanUser(sub, "StudabakerHoch")

    #run RemovePost test
    testUnBanUser(sub, "StudabakerHoch")

    #run get post test
    testGetPosts(sub)

    #run make comment test
    testMakeComment(my_post)

    #run get comments post
    testGetComments(my_post)

    #run make comment test
    testRemoveComment(my_comment)

    #run RemovePost test
    testRemovePost(sub, my_post)

    #run multiproc handler test
    r = testMultiprocess(credentials)

    #run message tests
    test_send_message(r, credentials)
    test_get_message(credentials)


    import logging

    logging.info("Tests complete")


if __name__ == "__main__":
    main()
