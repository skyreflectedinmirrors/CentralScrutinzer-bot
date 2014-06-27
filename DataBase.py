# DataBase.py -- contains wrappers for various databases


class DataBase(object):
    def __init__(self, ID):
        self.ID = ID

    def __write__(self):
        raise Exception("Cannot instantiate abstract class DataBase")

    def log(self, text):
        self.__write__(text)


#the dream, but I know shit all about SQL
class SQLDataBase(DataBase):
    def __init__(self, ID):
        super(SQLDataBase, self).__init__(ID)


#probably to be used initially for simplicity
class TextFileDataBase(DataBase):
    def __init__(self, File):
        super(SQLDataBase, self).__init__(file)
        self.File = File