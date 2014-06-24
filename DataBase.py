#DataBase.py -- contains wrappers for various databases

class DataBase(object):
	def __init__(self, ID):
		self.ID = ID
	
#the dream, but I know shit all about SQL
class SQLDataBase(object):
	def __init__(self, ID):
		super(SQLDataBase, self).__init__(ID)
		
#probably to be used initially for simplicity
class TextFileDataBase(object):
	def __init__(self, File):
		super(SQLDataBase, self).__init__(file)
		self.File = File