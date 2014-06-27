#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import bz2
# liberally stolen from moderator-bot
class Filter(object):
    """Base filter class"""

    def __init__(self):
        self.regex = None
        self.comment_template = (
            "##This submission has been removed automatically.\nAccording to our [subreddit rules]("
            "/r/{sub}/wiki/rules/) {reason}.  If you feel this was in error, please [message the mo"
            "derators](/message/compose/?to=/r/{sub}&subject=Removal%20Dispute&message={link}).  If"
            " this submission was removed in error, do not delete it.  The moderators will fix this"
            " submission.")
        self.comment = ""
        self.tag = ""
        self.action = 'remove'
        self.log_text = ""
        self.ban = False
        self.report_subreddit = None
        self.nuke = True
        self.reddit = None

    def filterComment(self, comment):
        raise NotImplementedError

    def filterSubmission(self, submission):
        raise NotImplementedError

    def runFilter(self, post):
        if 'title' in vars(post):
            try:
                if self.filterSubmission(post):
                    if self.log_text:
                        logToDisk(self.log_text)
                    return True
            except NotImplementedError:
                pass
        elif 'body' in vars(post):
            try:
                if self.filterComment(post):
                    if self.log_text:
                        logToDisk(self.log_text)
                    return True
            except NotImplementedError:
                pass


def cache_url():
    """Url caching decorator.  For decorating class functions that take a single url as an arg
    and return the response."""

    def wrap(function):
        def new_function(*args):
            url = args[1]
            expire_after = args[0].cache_time
            try:
                with bz2.open(CACHEFILE, 'rt') as f:
                    d = json.loads(f.read())
            except (IOError, ValueError):
                d = dict()
            if 'cache' not in d:
                d['cache'] = dict()
            if url in d['cache']:
                output = d['cache'][url]
                expire_time = output['time'] + expire_after
                if expire_after == 0 or time.time() < expire_time:
                    return output['data']
                else:
                    del d['cache'][url]
            output = function(*args)
            if output:
                to_cache = {'time': time.time(), 'data': output}
                d['cache'][url] = to_cache
                with bz2.open(CACHEFILE, 'wt') as f:
                    f.write(json.dumps(d))
                return output

        return new_function

    return wrap


class Youtube(object):
    def __init__(self, cache_time=0):
        self.opener = urllib.request.build_opener()
        self.opener.addheaders = [('User-agent', USERAGENT)]
        self.last_request = 0
        self.cache_time = cache_time

    @cache_url()
    def _request(self, url):
        try:
            since_last = time.time() - self.last_request
            if not since_last >= 2:
                time.sleep(2 - since_last)
            with self.opener.open(url, timeout=30) as w:
                youtube = w.read().decode('utf-8')
                yt_json = json.loads(youtube)
        except:
            self.last_request = time.time()
            return None

        if 'errors' not in yt_json:
            return yt_json['entry']

    def _get_id(self, url):
        # regex via: http://stackoverflow.com/questions/3392993/php-regex-to-get-youtube-video-id
        regex = re.compile(
            r'''(?<=(?:v|i)=)[a-zA-Z0-9-]+(?=&)|(?<=(?:v|i)\/)[^&\n]+|(?<=embed\/)[^"&\n]+|'''
            r'''(?<=(?:v|i)=)[^&\n]+|(?<=youtu.be\/)[^&\n]+''', re.I)
        yt_id = regex.findall(
            url.replace('%3D', '=').replace('%26', '&').replace('%2F', '?').replace('&amp;', '&'))

        if yt_id:
            # temp fix:
            yt_id = yt_id[0].split('#')[0]
            yt_id = yt_id.split('?')[0]
            return yt_id

    def _get(self, url):
        """Decides if we're grabbing video info or a profile."""
        urls = {
            'profile': 'http://gdata.youtube.com/feeds/api/users/{}?v=2&alt=json',
            'video': 'http://gdata.youtube.com/feeds/api/videos/{}?v=2&alt=json'}

        yt_id = self._get_id(url)

        if yt_id:
            return self._request(urls['video'].format(yt_id))
        else:
            username = re.findall(r'''(?i)\.com\/(?:user\/|channel\/)?(.*?)(?:\/|\?|$)''', url)
            if username:
                return self._request(urls['profile'].format(username[0]))

    def get_author(self, url):
        """Returns the author id of the youtube url"""
        output = self._get(url)
        if output:
            # There has to be a reason for the list in there...
            return output['author'][0]['yt$userId']['$t']

    def get_info(self, url):
        """Returns the title and description of a video."""
        output = self._get(url)
        if output:
            if 'media$group' in output:
                title = output['title']['$t']
                description = output['media$group']['media$description']['$t']
                return {'title': title, 'description': description}

    def is_video(self, url):
        if self._get_id(url) is not None:
            return True
        else:
            return False


class YoutubeSpam(Filter):
    def __init__(self, reddit, youtube):
        Filter.__init__(self)
        self.tag = "[Youtube Spam]"
        self.reddit = reddit
        self.y = youtube

    def _isVideo(self, submission):
        '''Returns video author name if this is a video'''
        if submission.domain in ('m.youtube.com', 'youtube.com', 'youtu.be'):
            return self.y.get_author(submission.url)

    def _checkProfile(self, submission):
        '''Returns the percentage of things that the user only contributed to themselves.
        ie: submitting and only commenting on their content.  Currently, the criteria is:
            * linking to videos of the same author (which implies it is their account)
            * commenting on your own submissions (not just videos)
        these all will count against the user and an overall score will be returned.  Also, we only
        check against the last 100 items on the user's profile.'''

        try:
            start_time = time.time() - (60 * 60 * 24 * 30 * 6)  # ~six months
            redditor = self.reddit.get_redditor(submission.author.name)
            comments = [i for i in redditor.get_comments(limit=100) if i.created_utc > start_time]
            submitted = [i for i in redditor.get_submitted(limit=100) if i.created_utc > start_time]
        except urllib.error.HTTPError:
            # This is a hack to get around shadowbanned or deleted users
            p("Could not parse /u/{}, probably shadowbanned or deleted".format(user))
            return False
        video_count = defaultdict(lambda: 0)
        video_submissions = set()
        comments_on_self = 0
        initial_author = self._isVideo(submission)
        for item in submitted:
            video_author = self._isVideo(item)
            if video_author:
                video_count[video_author] += 1
                video_submissions.add(item.name)
        if video_count:
            most_submitted_author = max(video_count.items(), key=operator.itemgetter(1))[0]
        else:
            return False
        for item in comments:
            if item.link_id in video_submissions:
                comments_on_self += 1
        try:
            video_percent = max(
                [video_count[i] / sum(video_count.values()) for i in video_count])
        except ValueError:
            video_percent = 0
        if video_percent > .85 and sum(video_count.values()) >= 3:
            spammer_value = (sum(video_count.values()) + comments_on_self) / (len(
                comments) + len(submitted))
            if spammer_value > .85 and initial_author == most_submitted_author:
                return True

    def filterSubmission(self, submission):
        self.report_subreddit = None
        DAY = 24 * 60 * 60
        if submission.domain in ('m.youtube.com', 'youtube.com', 'youtu.be'):
            link = 'http://reddit.com/r/{}/comments/{}/'.format(
                submission.subreddit, submission.id)
            # check if we've already parsed this submission
            try:
                with bz2.open(DATABASEFILE, 'rt') as db:
                    db = json.loads(db.read())
            except IOError:
                db = dict()
                db['users'] = dict()
                db['submissions'] = list()

            if submission.id in db['submissions']:
                return False
            if submission.author.name in db['users']:
                user = db['users'][submission.author.name]
            else:
                user = {'checked_last': 0, 'warned': False, 'banned': False}

            if time.time() - user['checked_last'] > DAY:
                p("Checking profile of /u/{}".format(submission.author.name), end='')
                user['checked_last'] = time.time()
                if self._checkProfile(submission):
                    if user['warned']:
                        self.log_text = "Confirmed video spammer"
                        p(self.log_text + ":")
                        self.comment = ''
                        self.report_subreddit = 'spam'
                        self.ban = True
                        self.nuke = True
                        user['banned'] = True
                    else:
                        self.comment = (
                            """Hello, /u/{user}, it looks like you're on the verge with submittin"""
                            """g videos, so consider this a friendly warning/guideline:\n\nReddit"""
                            """ has [guidelines as to what constitutes spam](http://www.reddit.co"""
                            """m/wiki/faq#wiki_what_constitutes_spam.3F). To summarize:\n\n* It's"""
                            """ not strictly forbidden to submit links to videos of yours, but pl"""
                            """ease only do so in a moderate amount.\n\n* If you spend more time """
                            """submitting to reddit than reading it, you're almost certainly a sp"""
                            """ammer. As a rule of thumb, for every post promoting your own video"""
                            """(s), you should have made 10 other submissions or comments on othe"""
                            """r posts. (Bear in mind that pointless comments like "nice" and "lo"""
                            """l" do not count as actual contribution.)\n\n* If your contribution"""
                            """ to reddit consists mostly of your own videos, and additionally if"""
                            """ you do not participate in this community in other ways, for examp"""
                            """le by submitting other content or joining the discussion on other """
                            """posts, you are a spammer.\n\n* If people historically downvote you"""
                            """r links or ones similar to yours, and you feel the need to keep su"""
                            """bmitting them anyway, they're probably spam.\n\nFor right now, thi"""
                            """s is just a friendly message, but here in /r/{sub}, we take action"""
                            """ against anyone that fits the above definition.\n\nIf you feel thi"""
                            """s was in error, feel free to [message the moderators](/message/com"""
                            """pose/?to=/r/{sub}&subject=Video%20Spam&message={link}).""".format(
                                user=submission.author.name, sub=SUBREDDIT, link=link))
                        self.ban = False
                        self.nuke = False
                        self.log_text = "Found potential video spammer"
                        p(self.log_text + ":")
                        p("http://reddit.com/u/{}".format(submission.author.name),
                          color_seed=submission.author.name)
                        user['warned'] = True
                    output = True
                else:
                    output = False
                db['users'][submission.author.name] = user
                db['submissions'].append(submission.id)
                with bz2.open(DATABASEFILE, 'wt') as f:
                    f.write(json.dumps(db))
                return output


class SpamNBan(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.regex = re.compile(
            r'''teslabots\.jimbo\.com|topminecraftworldseeds\.com|\/r\/mcgriefservers|'''
            r'''F2sTr6yNJ2A|instagc\.com|minecraftstack\.com''', re.I)
        self.ban = True
        self.action = 'spammed'

    def filterSubmission(self, submission):
        if self.regex.search(submission.title) or \
                self.regex.search(submission.selftext) or \
                self.regex.search(submission.url):
            self.log_text = "Found spam domain in submission"
            p(self.log_text + ":")
            p('http://reddit.com/r/{}/comments/{}/'.format(
                submission.subreddit, submission.id), color_seed=submission.name)
            return True

    def filterComment(self, comment):
        if self.regex.search(comment.body):
            self.log_text = "Found spam domain in comment"
            p(self.log_text + ":")
            p('http://reddit.com/r/{}/comments/{}/a/{}'.format(
                comment.subreddit.display_name, comment.link_id[3:], comment.id),
              color_seed=comment.link_id)
            return True


class BannedYoutubers(Filter):
    def __init__(self, reddit, youtube):
        self.last_update = 0
        Filter.__init__(self)
        self.reddit = reddit
        self.youtube = youtube
        self.action = 'spammed'

    def _update_list(self):
        if (time.time() - self.last_update) >= 1800:
            update_page = False
            added_ids = []
            self.youtube_list = []
            self.last_update = time.time()
            p('Updating youtube blacklist...', end='')
            blacklist = self.reddit.get_wiki_page(SUBREDDIT, 'youtube_blacklist')
            blacklist_text = blacklist.content_md
            youtube_list = [
                i.replace(' ', '') for i in re.split(r'''[\r\n]*''', blacklist_text) if not
                i.startswith("//")]
            youtube_list = [i for i in youtube_list if i]
            for youtuber in youtube_list:
                if youtuber.startswith('http'):
                    user_id = self.youtube.get_author(youtuber)
                    blacklist_text = blacklist_text.replace(youtuber, user_id)
                    self.youtube_list.append(user_id)
                    added_ids.append(user_id)
                    update_page = True
                else:
                    self.youtube_list.append(youtuber)
            if update_page:
                p('Updating youtube blacklist with {} new entries.'.format(
                    len(added_ids)))
                blacklist.edit(
                    content=blacklist_text, reason='Added ids: {}'.format(', '.join(added_ids)))

    def filterSubmission(self, submission):
        self._update_list()
        if submission.domain in ('m.youtube.com', 'youtube.com', 'youtu.be'):
            yt = self.youtube.get_author(submission.url)
            if yt:
                if yt in self.youtube_list:
                    link = 'http://reddit.com/r/{}/comments/{}/'.format(
                        submission.subreddit, submission.id)
                    self.log_text = "Found link to banned Youtuber in submission"
                    p(self.log_text + ":")
                    p(link, color_seed=submission.name)
                    return True
