import unittest
import CredentialsImport as cr
import musicbrainzinterface as mbi
from dateutil.parser import parse as parsedate


class TestMusicBrainz(unittest.TestCase):
    def __init__(self, methodname="runTest"):
        self.cred = cr.CRImport('credentials.cred')
        self.user_agent='centralscrutinizer-musicbrainz-query-test'
        self.max_tries = 5
        self.wait = 2
        import os
        if os.name == 'nt':
            self.host=None
        else:
            self.host = self.cred['MUSICBRAINZHOST']
        super(TestMusicBrainz, self).__init__(methodname)

    def test_create(self):
        with mbi.MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            self.assertTrue(mbz is not None)

    def test_search_good(self):
        with mbi.MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_artist('Talking Heads')
            self.assertTrue(result[0]['name'] == 'Talking Heads')

    def test_search_filter(self):
        with mbi.MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_artist('Talking Heads', 101)
            self.assertTrue(len(result) == 0)

    def test_search_bad(self):
        with mbi.MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_artist('thisisnotarealbandorshoulditreturnanysubstantiveresults.com')
            self.assertTrue(len(result) == 0 or
                            not any(x['ext:score'] > 1 for x in result))

    def test_release(self):
        with mbi.MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:

            year = mbz.get_release_date('Talking Heads', 'This Must Be The Place (Naive Melody)').year

            result = mbz.get_release('Talking Heads', 'This Must Be The Place (Naive Melody)', 0)
            for r in result:
                name = next((x for x in r['release-list'] if 'date' in x and parsedate(x['date']).year == year), None)
                if name is not None:
                    self.assertTrue(name['title'] == 'Speaking in Tongues')
                    break

            result = mbz.get_release('Talking Heads', 'This Must Be The Place (Naive Melody)', 100)
            for r in result:
                name = next((x for x in r['release-list'] if 'date' in x and parsedate(x['date']).year == year), None)
                if name is not None:
                    self.assertTrue(name['title'] == 'Speaking in Tongues')
                    break

    def test_fail_release(self):
        with mbi.MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_release('Talking Heads', 'this is not a song or a place or a time', 100)
            self.assertTrue(len(result) == 0 or result[0]['artist-credit-phrase'] != 'Talking Heads')

            result = mbz.get_release('Talking Heads', 'this is not a song or a place or a time', 0)
            self.assertTrue(len(result) == 0 or result[0]['artist-credit-phrase'] != 'Talking Heads')

    def test_release_date(self):
        with mbi.MusicBrainzWrapper(self.cred, host=self.host, useragent=self.user_agent,
                                max_tries=self.max_tries, wait=self.wait) as mbz:
            result = mbz.get_release_date('Talking Heads', 'This Must Be The Place (Naive Melody)')
            self.assertTrue(result.year == 1983)

            result = mbz.get_release_date('Talking Heads', 'This Must Be The Place (Naive Melody)', 100)
            self.assertTrue(result.year == 1983)

