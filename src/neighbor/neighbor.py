import threading

import general.timer as timer
import conf.conf as conf
import general.utils as utils

'''
This class represents the OSPF neighbor and contains its data and operations
'''


class Neighbor:
    inactivity_timer = None
    thread = None

    neighbor_id = '0.0.0.0'
    neighbor_options = 0
    neighbor_state = conf.NEIGHBOR_STATE_DOWN  # Initial state

    reset = None
    timeout = None
    shutdown = None

    utils = utils.Utils()

    def __init__(self, neighbor_id, neighbor_options):
        is_valid, message = self.parameter_validation(neighbor_id, neighbor_options)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)

        self.neighbor_id = neighbor_id
        self.neighbor_options = neighbor_options
        self.neighbor_state = conf.NEIGHBOR_STATE_INIT  # Hello packet received from neighbor
        print("Neighbor found with ID", self.neighbor_id)

        self.reset = threading.Event()
        self.timeout = threading.Event()
        self.shutdown = threading.Event()

        #  Sets timer that monitors neighbor last activity
        timeout_seconds = conf.ROUTER_DEAD_INTERVAL
        self.inactivity_timer = timer.Timer()
        self.thread = threading.Thread(target=self.inactivity_timer.single_shot_timer,
                                       args=(self.reset, self.timeout, self.shutdown, timeout_seconds))
        self.thread.start()

    #  Returns True is timer has fired - No activity from neighbor was received lately
    def is_expired(self):
        return self.timeout.is_set()

    #  Resets timer - Activity from neighbor has just been received
    def reset_timer(self):
        self.reset.set()

    #  Stops thread so that neighbor can be deleted
    def delete_neighbor(self):
        self.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        self.shutdown.set()
        self.thread.join()

    #  Changes neighbor state and prints a message
    def set_neighbor_state(self, new_state):
        old_state = self.neighbor_state
        if new_state != old_state:
            print("Neighbor", self.neighbor_id, "changed state from", old_state, "to", new_state)
            self.neighbor_state = new_state

    #  Validates constructor parameters - Returns error message in case of failed validation
    def parameter_validation(self, neighbor_id, neighbor_options):
        try:
            if not self.utils.is_ipv4_address(neighbor_id):
                return False, "Invalid neighbor ID"
            if not (0 <= neighbor_options <= conf.MAX_VALUE_8_BITS):
                return False, "Invalid neighbor options"
            return True, ''
        except (ValueError, TypeError):
            return False, "Invalid parameter type"
