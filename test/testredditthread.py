import unittest
from datetime import timedelta
from timeit import default_timer as timer
import multiprocessing
import RedditThread as rt

pp_short = 0.1
pp_test= 1
ebh = 3

manager = multiprocessing.Manager()
wait_event = manager.Event()
exit_event = manager.Event()


class ThreadTester(object):
    def __init__(self):
        self.Errors_Before_Halt = ebh
        self.Pause_Period = pp_test
        self.pause = False

        self.wait = wait_event
        self.exit = exit_event

    def request_pause(self):
        self.pause = True


class exit_rt(rt.RedditThread):
    def __init__(self, tt1, tt2):
        super(exit_rt, self).__init__(tt1, tt2)
        self.exitset = False

    def shutdown(self):
        self.exitset = True


def create_and_wait():
    tt = ThreadTester()
    red = rt.RedditThread(tt, tt)
    return red.check_status()


class TestRedditThread(unittest.TestCase):
    def test_status(self):
        tt = ThreadTester()
        red = rt.RedditThread(tt, tt)
        start = timer()
        red.check_status()
        end = timer()
        self.assertTrue(timedelta(seconds=end - start) < timedelta(seconds=tt.Pause_Period))

    def test_log_error(self):
        tt = ThreadTester()
        red = rt.RedditThread(tt, tt)
        for i in range(tt.Errors_Before_Halt):
            red.check_status()
            red.log_error()
        self.assertTrue(tt.pause)

    def test_exit(self):
        tt = ThreadTester()
        red = exit_rt(tt, tt)
        exit_event.set()
        red.check_status()
        exit_event.clear()
        self.assertTrue(red.exitset)

    def test_wait(self):
        import os
        if os.name == 'nt':
            self.skipTest('Windows sux')
        wait_event.set()
        p = multiprocessing.Pool()
        i = None
        try:
            i = p.apply_async(create_and_wait)
            i.get(pp_test)
        except multiprocessing.TimeoutError:
            pass
        wait_event.clear()
        try:
            x = i.get(pp_test)
            if x:
                self.assertTrue(True)
        except multiprocessing.TimeoutError:
            self.fail()



