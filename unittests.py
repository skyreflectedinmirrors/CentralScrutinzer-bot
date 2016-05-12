import unittest
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    if __debug__:
        import logging
        logger = logging.getLogger(None)
        logger.setLevel(logging.DEBUG)

    testsuite = unittest.TestLoader().discover('./test/', pattern='*redditaction.py')
    unittest.TextTestRunner(verbosity=2).run(testsuite)