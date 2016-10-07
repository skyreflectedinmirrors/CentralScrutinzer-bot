import unittest
import os
from DataBase import DataBaseWrapper as DB

test_dbname = 'testdatabase.db'

class TestLastFm(unittest.TestCase):
    def __init_test(self):
        os.remove(test_dbname)

    def test_create(self):
        self.__init_test()
        try:
            with DB(test_dbname) as db:
                pass
        except Exception, e:
            self.fail(e)

    def test_add_artist(self):
        self.__init_test()
        try:
            with DB(test_dbname) as db:
                pass
        except Exception, e:
            self.fail(e)