# DataMiner.py -- scans old listentothis posts to create a nice testbase

import praw
import Actions

#accepted domains
domains = ["youtube.com", "archive.org", "bandcamp.com", "grooveshark.com", "npr.org", "radd.it", "soundcloud.com",
           "spotify.com", "youtu.be", "vimeo.com"]

#limits on different groups
POSTS_FROM_URL = 10
POST_LIMIT = 10000

def process_domain(post):
    #check that the domain supplied is good
    domain_match = [domain for domain in domains if domain in post.url]
    if len(domain_match) >= 1:
        post.domain = domain_match[0]
        return True
    return False

def process_comments(post):
    raddit_comments = [process_raddit_comment(comment.body) for comment in post.comments if comment.author and comment.author.name == "raddit-bot"]
    if not len(raddit_comments):
        return None
    return raddit_comments[0]

def make_post(sub, post, comment):
    try:
        #make post and comment
        post = Actions.make_post_url(sub, post.title, post.url)
        Actions.make_comment(post, comment)
    except Exception, e:
        print str(e)

artist_match = "**name**|[**"
track_match = "**track**|**"
def process_raddit_comment(body):
    info = ""
    try:
        #get artist
        index = body.index(artist_match) + len(artist_match)
        info += 'artist: ' + body[index:body.index('**', index)] + '  \n'

        #get track
        index = body.index(track_match) + len(track_match)
        info += 'track: ' + body[index:body.index('**', index)] + '  '
    except ValueError:
        pass
    return info


def main():
    from CredentialsImport import CRImport
    import utilitymethods as u
    import logging

    testbed = None
    saved_posts = {}

    # mark true if the script should remove all old posts from the testbed
    DELETE_OLD = True

    #import credentials
    credentials = CRImport("TestCredentials.cred")

    #create my reddit
    r = u.create_multiprocess_praw(credentials)

    #get testbed sub
    testbed = u.get_subreddit(credentials, r)

    #create datasource object
    datasource = u.get_subreddit(credentials, r, credentials["DATAMININGSUB"])

    if DELETE_OLD:
        old_stream = praw.helpers.submission_stream(r, testbed, limit=POST_LIMIT)
        results = []
        try:
            #delete all old posts
            for post in old_stream:
                try:
                    Actions.remove_post(post, delete=True)
                    print("deleted old post: %s..." % post.title[:20])
                except AttributeError:
                    # Post or Comment may have been deleted between retrieving it
                    # and accessing its fields
                    pass
        except AssertionError, e:
            logging.log(logging.DEBUG, str(e) + "\nNo Posts!")

    for domain in domains:
        saved_posts[domain] = 0
    #now go through datasource subreddit
    try:
        #create stream
        stream = datasource.get_new(limit=POST_LIMIT)
        count = 0
        for post in stream:
            if not len(domains):
                break
            count += 1
            print "processing post " + str(count)

            #process posts
            results = []
            if not process_domain(post):
                continue
            print "valid domain..."

            #load comments
            print "scanning comments..."
            #process comments
            comment = process_comments(post)
            if comment:
                #check domain
                if saved_posts[post.domain] < POSTS_FROM_URL:
                    saved_posts[post.domain] += 1
                    print "X-Posting " + post.title[:20] + "...   " + post.domain + "[" + str(saved_posts[post.domain]) + "/" + str(POSTS_FROM_URL) + "]"
                    make_post(testbed, post, comment)
                elif saved_posts[post.domain] >= POSTS_FROM_URL and post.domain in domains:
                    domains.remove(post.domain)


    except Exception, e:
        print str(e)


if (__name__ == "__main__"):
    main()