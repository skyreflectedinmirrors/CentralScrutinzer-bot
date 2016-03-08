import unittest
import pylast
from lastfm import LastFmQuery
from lastfm import ErrorCodes


class TestLastFm(unittest.TestCase):
    def __create(self):
        from CredentialsImport import CRImport
        cred = CRImport('credentials.cred')
        try:
            a = LastFmQuery(cred)
        except:
            return None
        return a

    def test_init(self):
        self.assertTrue(self.__create() is not None)

    def test_get_artist(self):
        lastfm = self.__create()
        a = lastfm.get_artist('Talking Heads')
        self.assertTrue(isinstance(a, pylast.Artist))
        try:
            self.assertTrue(a.get_listener_count() > 0)
        except:
            self.fail()
        a = lastfm.get_artist('thisisnotarealbandnameandshouldfail.com.org')
        try:
            a.get_listener_count()
            self.fail()
        except pylast.WSError, e:
            pass

    def test_get_listener_count(self):
        lastfm = self.__create()
        self.assertTrue(lastfm.get_listener_count('Talking Heads') > 1e6)
        self.assertTrue(lastfm.get_listener_count('thisisnotarealbandnameandshouldfail.com.org') ==
                        ErrorCodes.artist_not_found)

    def test_get_scrobble_count(self):
        lastfm = self.__create()
        self.assertTrue(lastfm.get_play_count('Talking Heads') > 38e6)
        self.assertTrue(lastfm.get_play_count('thisisnotarealbandnameandshouldfail.com.org') ==
                        ErrorCodes.artist_not_found)