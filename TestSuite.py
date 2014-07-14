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
        "https://www.youtube.com/watch?v=-vihDAj5VkY": "UC9TOJlW5ZLaiWdMjAUoTpqQ",
        "https://m.youtube.com/watch?v=G4ApQrbhQp8": "UCKy1dAqELo0zrOtPkf0eTMw",
        "http://youtu.be/Cg9PWSHL4Vg": "UCEvxaotno5fO12ylDsV1hpQ",
        "https://www.youtube.com/watch?v=iMoNJ_UiRQY": "PRIVATE",
        "https://www.youtube.com/watch?v=WkqziN8F8oM": "UCEsBZQzpSmHbzFTUva00Wlw"
    }
    channel_to_name = {
        "UC9TOJlW5ZLaiWdMjAUoTpqQ": "arghdos",
        "UCKy1dAqELo0zrOtPkf0eTMw": "IGN",
        "UCEvxaotno5fO12ylDsV1hpQ": "Karen Jones",
        "UCEsBZQzpSmHbzFTUva00Wlw": "BBrucker2"
    }

    url_to_name = {
        "https://www.youtube.com/watch?v=iMoNJ_UiRQY": "PRIVATE",
    }

    for id, response in id_to_response.iteritems():
        print id, response
        if y.channel_id(id) != response:
            return False

    for channel, id in channel_to_name.iteritems():
        if y.channel_name(channel) != channel_to_name[channel]:
            return False

    for url, id in url_to_name.iteritems():
        if y.channel_name_url(url) != url_to_name[url]:
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

    responses = []
    for id, response in id_to_response.iteritems():
        print id, response
        if y.channel_name_url(id) != response:
            return False
    return True


def main():
    g.init()
    g.close()
    #import credentials
    credentials = CRImport("TestCredentials.cred")

    testSoundcloudExtractor(credentials)

    testYoutubeExtractor(credentials)

    #create my reddit
    r = u.create_praw(credentials)

    sub = r.get_subreddit(credentials['SUBREDDIT'])

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