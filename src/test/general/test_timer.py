import unittest
import timeout_decorator
import threading
import time

import general.timer as timer

'''
This class tests the timer operations in the router
'''

TIMEOUT_SECONDS = 3
OFFSET = 1


#  Full successful run - 11-12 s
class TimerTest(unittest.TestCase):
    reset = None
    timeout = None
    shutdown = None
    timer = None

    def setUp(self):
        self.reset = threading.Event()
        self.timeout = threading.Event()
        self.shutdown = threading.Event()
        self.timer = timer.Timer()

    #  Successful run - 3 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS + 1)
    def test_one_shot_timer_successful_timeout(self):
        thread = threading.Thread(target=self.timer.single_shot_timer, args=(self.reset, self.timeout, self.shutdown,
                                                                             TIMEOUT_SECONDS))
        self.assertFalse(self.timeout.is_set())
        thread.start()
        thread.join()
        self.assertTrue(self.timeout.is_set())

    #  Successful run - 3 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS + 1)
    def test_one_shot_timer_successful_reset(self):
        thread = threading.Thread(target=self.timer.single_shot_timer, args=(self.reset, self.timeout, self.shutdown,
                                                                             TIMEOUT_SECONDS))
        self.assertFalse(self.reset.is_set())
        thread.start()
        self.reset.set()
        time.sleep(TIMEOUT_SECONDS)
        self.assertFalse(self.reset.is_set())
        thread.join()

    #  Successful run - 1 s
    @timeout_decorator.timeout(1)
    def test_one_shot_timer_successful_shutdown(self):
        thread = threading.Thread(target=self.timer.single_shot_timer, args=(self.reset, self.timeout, self.shutdown,
                                                                             TIMEOUT_SECONDS))
        thread.start()
        self.shutdown.set()
        thread.join()

    #  Successful run - Instant
    def test_one_shot_timer_invalid_parameters(self):
        with self.assertRaises(ValueError):
            self.timer.single_shot_timer(None, self.timeout, self.shutdown, TIMEOUT_SECONDS)
        with self.assertRaises(ValueError):
            self.timer.single_shot_timer(self.reset, None, self.shutdown, TIMEOUT_SECONDS)
        with self.assertRaises(ValueError):
            self.timer.single_shot_timer(self.reset, self.timeout, None, TIMEOUT_SECONDS)
        with self.assertRaises(ValueError):
            self.timer.single_shot_timer(self.reset, self.timeout, self.shutdown, 0.99)
        with self.assertRaises(ValueError):
            self.timer.single_shot_timer(self.reset, self.timeout, self.shutdown, 0)
        with self.assertRaises(ValueError):
            self.timer.single_shot_timer(self.reset, self.timeout, self.shutdown, -1)

    #  Successful run - 6 s
    @timeout_decorator.timeout(2*TIMEOUT_SECONDS+1)
    def test_interval_timer_successful(self):
        thread = threading.Thread(target=self.timer.interval_timer, args=(OFFSET, self.timeout, self.shutdown,
                                                                          TIMEOUT_SECONDS))
        thread.start()
        for i in range(2):
            self.assertFalse(self.timeout.is_set())
            time.sleep(TIMEOUT_SECONDS)
            self.assertTrue(self.timeout.is_set())
            self.timeout.clear()
        self.shutdown.set()
        thread.join()

    #  Successful run - Instant
    def test_interval_timer_invalid_parameters(self):
        with self.assertRaises(ValueError):
            self.timer.interval_timer(-1, self.timeout, self.shutdown, TIMEOUT_SECONDS)
        with self.assertRaises(ValueError):
            self.timer.interval_timer(OFFSET, None, self.shutdown, TIMEOUT_SECONDS)
        with self.assertRaises(ValueError):
            self.timer.interval_timer(OFFSET, self.timeout, None, TIMEOUT_SECONDS)
        with self.assertRaises(ValueError):
            self.timer.interval_timer(OFFSET, self.timeout, self.shutdown, 0.99)
        with self.assertRaises(ValueError):
            self.timer.interval_timer(OFFSET, self.timeout, self.shutdown, 0)
        with self.assertRaises(ValueError):
            self.timer.interval_timer(OFFSET, self.timeout, self.shutdown, -1)
