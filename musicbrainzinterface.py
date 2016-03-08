import musicbrainzngs
import logging


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

            def get_artist(self, artist_name, song_name=None):
                return musicbrainzngs.search_artists(artist=artist_name, type='artist')


        self.mbz = MusicBrainz(self.credentials, self.host, self.useragent, self.max_tries, self.wait)
        return self.mbz

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
