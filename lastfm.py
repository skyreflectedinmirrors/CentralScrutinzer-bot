import pylast
import time
import logging


class _ErrorCodes:
    def __init__(self):
        pass

    artist_not_found, outage = range(2)
    codes = [artist_not_found]
    str_error_codes = {artist_not_found: u'The artist you supplied could not be found'}

    def check_error(self, exception):
        if isinstance(exception, Exception):
            exception = str(exception)
        return next((x for x in self.codes if self.str_error_codes[x] == exception), None)

ErrorCodes = _ErrorCodes()


def retry(func, max_tries=5, wait=2):
    def retried_func(*args, **kwargs):
        tries = 0
        while True:
            try:
                return func(*args, **kwargs)
            except pylast.WSError, e:
                code = ErrorCodes.check_error(e)
                if code is not None:
                    return code
                elif tries < max_tries:
                    tries += 1
                    if wait is not None:
                        time.sleep(wait)
                    continue
                else:
                    logging.warn('{} retries on last.fm function {}, potential last.fm outage'.format(
                        max_tries, func.__name__
                    ))
                    return ErrorCodes.outage
            except pylast.NetworkError, e:
                if tries < max_tries:
                    tries += 1
                    if wait is not None:
                        time.sleep(wait)
                    continue
                else:
                    logging.warn('{} retries on last.fm function {}, potential last.fm outage'.format(
                        max_tries, func.__name__
                    ))
                    return ErrorCodes.outage
            except Exception, e:
                raise e
            break
    return retried_func


class LastFmQuery(object):
    def __init__(self, credentials):
        self.cred = credentials

        assert('LASTFMID' in credentials and credentials['LASTFMID'])
        id = credentials['LASTFMID']

        assert('LASTFMSECRET' in credentials and credentials['LASTFMSECRET'])
        secret = credentials['LASTFMSECRET']

        self.lastfm = pylast.LastFMNetwork(api_key = id, api_secret = secret)

    @retry
    def get_artist(self, artist_name):
        return self.lastfm.get_artist(artist_name=artist_name)

    @retry
    def get_listener_count(self, artist_name):
        artist = self.get_artist(artist_name)
        return artist.get_listener_count()

    @retry
    def get_play_count(self, artist_name):
        artist = self.get_artist(artist_name)
        return artist.get_playcount()