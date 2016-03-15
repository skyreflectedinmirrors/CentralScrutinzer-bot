import musicbrainzngs
import logging
from dateutil.parser import parse as parsedate


class MusicBrainzWrapper(object):
    def __init__(self, credentials, host=None, useragent=None, max_tries=5, wait=2.0):
        self.credentials = credentials
        self.host = host
        self.useragent = useragent
        self.max_tries = max_tries
        self.wait = wait

    def __enter__(self):
        class MusicBrainz(object):
            def __init__(self, credentials, host=None, useragent=None, max_tries=None, wait=None):
                """

                :param credentials: the credentials object read in by CRImport
                :param host: a local musicbrainz instance, e.g.  'localhost:8000' (optional)
                :param useragent: useragent for muscbrainz (optional)
                :return:
                """

                try:
                    if useragent is None:
                        useragent = ('central-scrutinizer-/r/{}'.format(credentials['VERSION'], credentials['SUBREDDIT']))
                    musicbrainzngs.set_useragent(
                        useragent,
                        credentials['VERSION'],
                        "https://github.com/arghdos/CentralScrutinzer-bot",
                    )
                    if host is not None:
                        musicbrainzngs.set_hostname(host)
                    if max_tries is not None and wait is not None:
                        musicbrainzngs.set_rate_limit(wait, max_tries)
                except KeyError, e:
                    logging.critical('Version or subreddit missing from credentials object, cannot open musicbrainz')

            def get_artist(self, artist_name, filter_score=None):
                result = musicbrainzngs.search_artists(artist=artist_name, type='artist')
                if filter_score is not None:
                    result = [x for x in result['artist-list'] if float(x['ext:score']) >= filter_score]
                else:
                    result = [x for x in result['artist-list']]
                return result

            def get_release(self, artist_name, track_name, filter_score=None):
                result = musicbrainzngs.search_recordings(track_name, artist=artist_name)
                if filter_score is not None:
                    result = [x for x in result['recording-list'] if float(x['ext:score']) >= filter_score]
                else:
                    result = [x for x in result['recording-list']]
                return result

            def get_release_date(self, artist_name, track_name, filter_score=None):
                result = self.get_release(artist_name, track_name, filter_score)
                if not len(result):
                    return result
                date = None
                for artist_credit in result:
                    for release in artist_credit['release-list']:
                        try:
                            testdate = parsedate(release['date'])
                        except KeyError:
                            #release w/o date
                            pass
                        if date is None:
                            date = testdate
                        else:
                            date = testdate if testdate < date else date
                return date

        self.mbz = MusicBrainz(self.credentials, self.host, self.useragent, self.max_tries, self.wait)
        return self.mbz

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
