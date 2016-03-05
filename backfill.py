from retrying import retry
import Actions
import sqlite3
import utilitymethods
from CredentialsImport import CRImport
import time
import re

def main():
    cred = CRImport("credentials.cred")
    db = sqlite3.connect('database.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    cursor = db.cursor()
    post_list = [post[0] for post in cursor.execute('select short_url from reddit_record where submitter is null').fetchall()]
    praw = utilitymethods.create_multiprocess_praw(cred)
    reddit = utilitymethods.get_subreddit(cred, praw, 'listentothis')
    mods = [mod.name for mod in Actions.get_mods(praw, reddit)]
    stride = 100
    total_len = len(post_list)
    count = 0
    while len(post_list):
        num_loaded = min(stride, len(post_list))
        reddit_posts = Actions.get_by_ids(praw, post_list[:num_loaded])
        update_list = []
        print "{} / {}".format(count, total_len)
        count += stride
        for i, post in enumerate(reddit_posts):
            #check
            submitter = cursor.execute('select submitter from reddit_record where short_url = ?', (post_list[i],)).fetchone()[0]
            if submitter is not None:
                continue
            assert(post_list[i] == post.name)
            success = False
            while not success:
                try:
                    success = True
                    if Actions.is_deleted(post):
                        #check comments
                        found = False
                        for comment in post.comments:
                            if comment.distinguished == 'moderator':
                                if re.search(r'^(?:\*\*)?/u/', comment.body):
                                    search = re.search(r'^(?:\*\*)?/u/([\w\d_\-\*]+)[,\s]', comment.body)
                                    if search:
                                        found = True
                                        success = True
                                        update_list.append((search.group(1), post_list[i]))
                                        break
                                elif re.search(r'^All apologies /u/([\w\d_\-\*]+)[,\s]', comment.body):
                                    search = re.search(r'^All apologies /u/([\w\d_\-\*]+)[,\s]', comment.body)
                                    if search:
                                        found = True
                                        success = True
                                        update_list.append((search.group(1), post_list[i]))
                                        break
                                elif re.search(r'/u/([\w\d\*-_]+), your submission', comment.body):
                                    search = re.search(r'/u/([\w\d\*-_]+), your submission', comment.body)
                                    if search:
                                        found = True
                                        success = True
                                        update_list.append((search.group(1), post_list[i]))
                                        break
                                elif re.search(r'^Hey /u/([\w\d_\-\*]+)[,\s]', comment.body):
                                    search = re.search(r'^Hey /u/([\w\d_\-\*]+)[,\s]', comment.body)
                                    if search:
                                        found = True
                                        success = True
                                        update_list.append((search.group(1), post_list[i]))
                                        break
                                elif re.search(r'/u/([\w\d_\-\*]+)[,\s]', comment.body):
                                    search = re.search(r'/u/([\w\d_\-\*]+)[,\s]', comment.body)
                                    if search and 'evilnight' not in search.group(1):
                                        print comment.body
                                        print search.group(1)
                        if not found:
                            success = True
                            update_list.append((None, post_list[i]))
                    else:
                        success = True
                        update_list.append((post.author.name, post_list[i]))
                    if update_list[-1][0] is not None and update_list[-1][0].endswith(','):
                        print update_list[-1]
                except Exception, e:
                    success = False
                    time.sleep(1)
        assert (not any(val[0].endswith(',') for val in update_list if val[0] is not None))
        post_list = post_list[num_loaded:]

        cursor.executemany('update reddit_record set submitter = ? where short_url = ?', update_list)
        db.commit()


if __name__ == '__main__':
    main()