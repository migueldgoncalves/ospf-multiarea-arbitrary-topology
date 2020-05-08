import threading
import random

import general.timer as timer
import conf.conf as conf
import general.utils as utils

'''
This class represents the OSPF neighbor and contains its data and operations
'''


class Neighbor:

    def __init__(self, neighbor_id, neighbor_priority, neighbor_interface_id, neighbor_ip_address, neighbor_options,
                 neighbor_dr, neighbor_bdr):
        is_valid, message = self.parameter_validation(neighbor_id, neighbor_options)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)

        self.neighbor_id = neighbor_id
        self.neighbor_priority = neighbor_priority
        self.neighbor_interface_id = neighbor_interface_id  # Only for OSPFv3
        self.neighbor_ip_address = neighbor_ip_address  # Link-local address in OSPFv3
        self.neighbor_options = neighbor_options
        self.neighbor_state = conf.NEIGHBOR_STATE_DOWN  # Initial state
        self.neighbor_dr = neighbor_dr  # 0.0.0.0 means no DR is known by the neighbor
        self.neighbor_bdr = neighbor_bdr
        print("OSPFv" + str(utils.Utils.get_ospf_version(self.neighbor_ip_address)),
              "neighbor found with ID", self.neighbor_id)
        self.master_slave = False  # True -> This router is master
        self.dd_sequence = 0
        self.last_dd_packet = []  # [I-bit, M-bit, MS-bit, options, dd_sequence] from last DD packet from neighbor

        #  LSA lists
        self.ls_retransmission_list = []
        self.db_summary_list = []
        self.ls_request_list = []

        #  Implementation-specific parameters
        self.reset = threading.Event()
        self.timeout = threading.Event()
        self.shutdown = threading.Event()

        #  Sets timer that monitors neighbor last activity
        timeout_seconds = conf.ROUTER_DEAD_INTERVAL
        self.inactivity_timer = timer.Timer()
        self.thread = threading.Thread(target=self.inactivity_timer.single_shot_timer,
                                       args=(self.reset, self.timeout, self.shutdown, timeout_seconds))
        self.thread.start()

    #  Returns True if timer has fired - No activity from neighbor was received lately
    def is_expired(self):
        return self.timeout.is_set()

    #  Resets timer - Activity from neighbor has just been received
    def reset_timer(self):
        self.reset.set()

    #  Stops timer thread so that neighbor can be deleted
    def delete_neighbor(self):
        self.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        self.ls_retransmission_list = []
        self.db_summary_list = []
        self.ls_request_list = []
        self.shutdown.set()
        self.thread.join()

    #  Changes neighbor state and prints a message
    def set_neighbor_state(self, new_state):
        old_state = self.neighbor_state
        if new_state != old_state:
            if old_state != conf.NEIGHBOR_STATE_DOWN:
                print("OSPFv" + str(utils.Utils.get_ospf_version(self.neighbor_ip_address)),
                      "neighbor", self.neighbor_id, "changed state from", old_state, "to", new_state)
            self.neighbor_state = new_state

    #  Increments DD Sequence Number, or generates a random number if set for first time
    def generate_dd_sequence_number(self):
        if self.dd_sequence == 0:
            self.dd_sequence = random.randrange(conf.MAX_VALUE_16_BITS + 1)
        else:
            self.dd_sequence += 1

    #  Updates the last received DB Description packet from the neighbor
    def update_last_dd_packet(self, i_bit, m_bit, ms_bit, options, dd_sequence):
        packet_data = [i_bit, m_bit, ms_bit, options, dd_sequence]
        if packet_data == self.last_dd_packet:
            return False  # Duplicate packet received from neighbor
        else:
            self.last_dd_packet = packet_data
            return True

    #  Validates constructor parameters - Returns error message in case of failed validation
    @staticmethod
    def parameter_validation(neighbor_id, neighbor_options):  # TODO: Implement validation for rest of parameters
        try:
            if not utils.Utils.is_ipv4_address(neighbor_id):
                return False, "Invalid neighbor ID"
            if not (0 <= neighbor_options <= conf.MAX_VALUE_8_BITS):
                return False, "Invalid neighbor options"
            return True, ''
        except (ValueError, TypeError):
            return False, "Invalid parameter type"
