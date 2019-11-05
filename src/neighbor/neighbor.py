import threading

import general.timer as timer
import conf.conf as conf

'''
This class represents the OSPF neighbor and contains its data and operations
'''


class Neighbor:
    inactivity_timer = None
    thread = None

    neighbor_id = ''
    neighbor_options = ''

    reset = None
    timeout = None
    shutdown = None

    def __init__(self, neighbor_id, neighbor_options):
        self.neighbor_id = neighbor_id
        self.neighbor_options = neighbor_options

        #  Sets timer that monitors neighbor last activity
        timeout_seconds = conf.ROUTER_DEAD_INTERVAL
        self.inactivity_timer = timer.Timer()
        self.thread = threading.Thread(target=self.inactivity_timer.single_shot_timer, args=(self.reset, self.timeout,
                                                                                        self.shutdown, timeout_seconds))
        self.thread.start()

    def get_neighbor_id(self):
        return self.neighbor_id

    def get_neighbor_options(self):
        return self.neighbor_options

    #  Returns True is timer has fired - No activity from neighbor was received lately
    def is_expired(self):
        return self.timeout.is_set()

    #  Resets timer - Activity from neighbor has just been received
    def reset_timer(self):
        self.reset.set()

    #  Stops thread so that neighbor can be deleted
    def delete_neighbor(self):
        self.shutdown.set()
        self.thread.join()
