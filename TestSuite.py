# Test-Suite.py

#I'm a man who (now) believes in unit test driven development, so this is where the unit tests live!

import praw
import praw.errors as perr
import praw.handlers as phand
from CredentialsImport import CRImport
import DataBase
import Actions as a
import globaldata as g
import utilitymethods as u
import DataExtractors
import Blacklist

def store_post(post):
    global my_post
    my_post = post
    print "my_post = "  + my_post.title

def store_comment(comment):
    global my_comment
    my_comment = comment
    print "my_comment = "  + my_comment.id

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
        "https://www.youtube.com/watch?v=-vihDAj5VkY": "arghdos",
        "https://m.youtube.com/watch?v=G4ApQrbhQp8": "IGN",
        "http://youtu.be/Cg9PWSHL4Vg": "Karen Jones",
        "https://www.youtube.com/watch?v=iMoNJ_UiRQY": "PRIVATE",
        "https://www.youtube.com/watch?v=WkqziN8F8oM": "BBrucker2"
    }

    for id, response in id_to_response.iteritems():
        print id, response
        if y.channel_id(id) != response:
            return False

    return True

def testSoundcloudExtractor(credentials):
    y = DataExtractors.SoundCloudExtractor(credentials['SOUNDCLOUDID'])

    id_to_response = {
        "https://soundcloud.com/matt-spencer-37": "Morty Spin",
        "https://soundcloud.com/maggiesmithmusic/100-needles-for-zil": "MaggieSmithMusic",
        "https://soundcloud.com/natebelasco/kanye-west-black-skinhead-vs": "Nate Belasco",
        "https://soundcloud.com/NOTAREALURL": None
    }

    for id, response in id_to_response.iteritems():
        print id, response
        if y.channel_id(id) != response:
            return False
    return True

def testBandcampExtractor(credentials):
    y = DataExtractors.BandCampExtractor()

    id_to_response = {
        "http://wayneszalinski.bandcamp.com/": "wayneszalinski.bandcamp.com",
        "http://www.sleepwalkersbandcamp.bandcamp.com/": "sleepwalkersbandcamp.bandcamp.com",
        "http://rivka.bandcamp.com/track/better-days": "rivka.bandcamp.com",
        "jghkgkjgjhjhg.com": "jghkgkjgjhjhg.com",
        "jghkgkjgjhjhg": "jghkgkjgjhjhg",
        "http://rivka.bandcamp.com/track/better-days/https://www.youtube.com/watch?v=RVLwCLGz5hM": "rivka.bandcamp.com"
    }

    for id, response in id_to_response.iteritems():
        print id, response
        if y.channel_id(id) != response:
            return False
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
    print "Wiki write: " + str(read_test == "test")
    return read_test == "test"

def test_black_list(credentials):
    y = DataExtractors.YoutubeExtractor(credentials['GOOGLEID'])
    ids = ["https://www.youtube.com/watch?v=-vihDAj5VkY", "https://www.youtube.com/watch?v=AkzOLOih0HA"]
    blist = Blacklist.Blacklist(credentials, y)
    if not blist:
        print "Blacklist creation: False"
        return False
    print "Blacklist creation: True"

    #test adding to blacklist
    blist.add_blacklist(ids[0])
    check = blist.check_blacklist(ids[1])
    if not check:
        print "Blacklist addition: False"
    print "Blacklist addition: True"

    #test channels
    channels = blist.get_blacklisted_channels("arghdos")
    if len(channels) > 0 and channels[0] == "arghdos":
        print "Blacklist channel get: True"
    else:
        print "Blacklist channel get: False"
        return False

    #test blacklist removal
    blist.remove_blacklist_url(ids[0])
    check = blist.check_blacklist(ids[0])
    if check:
        print "Blacklist removal: False"
        return False
    print "Blacklist removal: True"
    return True



def main():
    g.init()
    g.close()
    #import credentials
    credentials = CRImport("TestCredentials.cred")

    testBandcampExtractor(credentials)

    testSoundcloudExtractor(credentials)

    testYoutubeExtractor(credentials)

    #create my reddit
    r = u.create_praw(credentials)

    sub = r.get_subreddit(credentials['SUBREDDIT'])

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

    import logging
    logging.info("Tests complete")

if (__name__ == "__main__"):
    main()