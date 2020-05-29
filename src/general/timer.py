import time

'''
This class performs the timer operations in the router
'''


class Timer:

    def __init__(self):
        self.initial_time = 0
        self.timeout = 0

    #  Implements a single-shot timer - Fires if timeout is reached, can be reset indefinite times
    def single_shot_timer(self, reset, timeout, shutdown, seconds):
        if reset is None:
            raise ValueError("No reset event provided")
        if timeout is None:
            raise ValueError("No timeout event provided")
        if shutdown is None:
            raise ValueError("No shutdown event provided")
        if int(seconds) <= 0:
            raise ValueError("Timeout must be positive and at least 1 second")

        self.reset_timer()
        self.timeout = seconds
        while int(time.perf_counter()) < int(self.initial_time + seconds):
            if reset.is_set():  # Timer is signalled to restart
                reset.clear()
                self.reset_timer()
            if shutdown.is_set():  # Timer is signalled to shutdown
                break
        timeout.set()

    #  Implements a regular timer - Fires at regular intervals
    def interval_timer(self, offset, timeout, shutdown, seconds):
        if int(offset) < 0:
            raise ValueError("Offset time must be at least 0")
        if timeout is None:
            raise ValueError("No timeout event provided")
        if shutdown is None:
            raise ValueError("No shutdown event provided")
        if int(seconds) <= 0:
            raise ValueError("Timeout must be positive and at least 1 second")

        self.reset_timer()
        self.timeout = seconds
        time.sleep(offset)  # This sleep helps to ensure different interval timers are not synchronized
        while True:
            if int(time.perf_counter()) >= int(self.initial_time + seconds):  # Timeout is reached
                timeout.set()
                self.reset_timer()
            if shutdown.is_set():  # Times is signalled to shutdown
                break

    def get_timer_time(self):
        timer_time = int(self.initial_time + self.timeout) - int(time.perf_counter())
        if timer_time > 0:
            return timer_time
        return 0

    def reset_timer(self):
        self.initial_time = int(time.perf_counter())  # Sets initial time with current system time in seconds
