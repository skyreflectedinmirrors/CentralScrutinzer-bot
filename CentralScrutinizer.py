import DataExtractors
import logging
import Blacklist
import threading
import ScanSub
import BlacklistQuery

class CentralScrutinizer(object):
    """
    The main bot object.  Owns / controls / moniters all other threads
    """
    def __init__(self, credentials, policy, database_file):
        self.credentials = credentials
        self.policy = policy
        self.database_file = database_file

        #first try to create all the data extractors
        try:
            youtube = DataExtractors.YoutubeExtractor(credentials['GOOGLEID'])
        except Exception, e:
            logging.critical("Could not create Youtube data extractor!")
            logging.debug(str(e))

        try:
            soundcloud = DataExtractors.SoundCloudExtractor(credentials['SOUNDCLOUDID'])
        except Exception, e:
            logging.critical("Could not create Youtube data extractor!")
            logging.debug(str(e))

        try:
            bandcamp = DataExtractors.BandCampExtractor()
        except Exception, e:
            logging.critical("Could not create Youtube data extractor!")
            logging.debug(str(e))

        #next create a blacklist object for each
        self.extractors = [youtube, soundcloud, bandcamp]
        self.extractors = [e for e in self.extractors if e]
        self.blacklists = [Blacklist.Blacklist(e, database_file) for e in self.extractors]

        #store policy
        self.policy = policy

        #locking and errors
        self.lock = threading.Lock()
        self.err_count = 0

        self.ss = ScanSub.SubScanner(self, self.database_file)
        self.bquery = BlacklistQuery.BlacklistQuery(self)

    def request_pause(self):
        raise NotImplementedError
