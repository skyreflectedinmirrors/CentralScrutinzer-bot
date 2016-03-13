import unittest
from CredentialsImport import CRImport
from musicbrainzinterface import MusicBrainzWrapper


class TestMusicBrainz(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        self.cred = CRImport('credentials.cred')
        self.user_agent='centralscrutinizer-musicbrainz-query-test'
        self.max_tries = 5
        self.wait = 2
        self.host=None
        super(TestMusicBrainz, self).__init__(methodName)

    def test_create(self):
        with MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            self.assertTrue(mbz is not None)

    def test_search_good(self):
        with MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_artist('Talking Heads')
            self.assertTrue(result[0]['name'] == 'Talking Heads')

    def test_search_filter(self):
        with MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_artist('Talking Heads', 101)
            self.assertTrue(len(result) == 0)

    def test_search_bad(self):
        with MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_artist('thisisnotarealbandorshoulditreturnanysubstantiveresults.com')
            self.assertTrue(len(result) == 0 or
                            not any(x['ext:score'] > 1 for x in result))

    def test_release(self):
        with MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_release('Talking Heads', 'This Must Be The Place (Naive Melody)')
            self.assertTrue(len(result) >= 1 and result[0]['release-list'][0]['title'] == 'Speaking in Tongues')

            result = mbz.get_release('Talking Heads', 'This Must Be The Place (Naive Melody)', 100)
            self.assertTrue(len(result) >= 1 and result[0]['release-list'][0]['title'] == 'Speaking in Tongues')

    def test_fail_release(self):
        with MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_release('Talking Heads', 'this is not a song or a place or a time', 100)
            self.assertTrue(len(result) == 0 or result[0]['artist-credit-phrase'] != 'Talking Heads')

            result = mbz.get_release('Talking Heads', 'this is not a song or a place or a time', 0)
            self.assertTrue(len(result) == 0 or result[0]['artist-credit-phrase'] != 'Talking Heads')

    def test_release_date(self):
        with MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_release_date('Talking Heads', 'This Must Be The Place (Naive Melody)')
            self.assertTrue(result.year == 1983)

            result = mbz.get_release_date('Talking Heads', 'This Must Be The Place (Naive Melody)', 100)
            self.assertTrue(result.year == 1983)
