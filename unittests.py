import unittest
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    testsuite = unittest.TestLoader().discover('./test/', )
    unittest.TextTestRunner(verbosity=2).run(testsuite)