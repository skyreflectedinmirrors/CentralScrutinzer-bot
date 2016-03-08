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
            self.assertTrue(result['artist-list'][0]['name'] == 'Talking Heads')

    def test_search_bad(self):
        with MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_artist('thisisnotarealbandorshoulditreturnanysubstantiveresults.com')
            self.assertTrue(result['artist-count'] == 0 or
                            not any(x['ext:score'] > 1 for x in result['artist-list']))
