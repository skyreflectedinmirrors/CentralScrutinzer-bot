import unittest
import os


if __name__ == '__main__':
    testsuite = unittest.TestLoader().discover('./test/', )
    unittest.TextTestRunner(verbosity=2).run(testsuite)