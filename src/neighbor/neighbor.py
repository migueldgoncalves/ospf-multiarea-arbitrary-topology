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

        #  LSA lists - Receive LSA Identifiers
        self.ls_retransmission_list = []
        self.db_summary_list = []
        self.ls_request_list = []

        #  Implementation-specific parameters
        self.reset = threading.Event()
        self.inactivity_timeout = threading.Event()
        self.retransmission_timeout = threading.Event()
        self.inactivity_shutdown = threading.Event()
        self.retransmission_shutdown = threading.Event()
        self.last_sent_packet = None  # Last DD Description, LS Request or LS Update sent to neighbor

        #  Sets timer that monitors neighbor last activity
        timeout_seconds = conf.ROUTER_DEAD_INTERVAL
        self.inactivity_timer = timer.Timer()
        self.inactivity_thread = threading.Thread(
            target=self.inactivity_timer.single_shot_timer,
            args=(self.reset, self.inactivity_timeout, self.inactivity_shutdown, timeout_seconds))
        self.inactivity_thread.start()

        #  Packet retransmission timer
        self.retransmission_timer = timer.Timer()
        self.retransmission_thread = None

    #  Starts retransmission timer
    def start_retransmission_timer(self):
        self.stop_retransmission_timer()
        self.retransmission_timeout.clear()
        self.retransmission_shutdown.clear()
        self.retransmission_thread = threading.Thread(
            target=self.retransmission_timer.interval_timer,
            args=(0, self.retransmission_timeout, self.retransmission_shutdown, conf.RETRANSMISSION_INTERVAL))
        self.retransmission_thread.start()

    #  Returns True if inactivity timer has fired - No activity from neighbor was received lately
    def is_expired(self):
        return self.inactivity_timeout.is_set()

    #  Returns True if retransmission timer has fired and resets flag if so
    def is_retransmission_time(self):
        if self.retransmission_timeout.is_set() & (self.retransmission_thread is not None):
            if self.retransmission_thread.isAlive():
                self.retransmission_timeout.clear()
                return True
        return False

    #  Resets inactivity timer - Activity from neighbor has just been received
    def reset_inactivity_timer(self):
        self.reset.set()

    #  Stops retransmission timer
    def stop_retransmission_timer(self):
        if self.retransmission_thread is not None:
            self.retransmission_shutdown.set()
            self.retransmission_thread.join()

    #  Stops timer thread so that neighbor can be deleted
    def delete_neighbor(self):
        self.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        self.ls_retransmission_list = []
        self.db_summary_list = []
        self.ls_request_list = []
        self.inactivity_shutdown.set()
        self.inactivity_thread.join()
        self.stop_retransmission_timer()

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

    #  Adds LSA identifier to one of the LSA lists
    def add_lsa_identifier(self, lsa_list, lsa_identifier):
        if lsa_list not in [self.ls_retransmission_list, self.db_summary_list, self.ls_request_list]:
            raise ValueError("Invalid LSA list")
        if len(lsa_identifier) != 3:
            raise ValueError("Invalid LSA identifier")
        if lsa_identifier[0] <= 0:
            raise ValueError("Invalid LS Type")
        if not utils.Utils.is_ipv4_address(lsa_identifier[1]):
            raise ValueError("Invalid Link State ID")
        if not utils.Utils.is_ipv4_address(lsa_identifier[2]):
            raise ValueError("Invalid Advertising Router")
        lsa_list.append(lsa_identifier)

    #  Deletes LSA identifier from one of the LSA lists
    def delete_lsa_identifier(self, lsa_list, lsa_identifier):
        if lsa_list not in [self.ls_retransmission_list, self.db_summary_list, self.ls_request_list]:
            raise ValueError("Invalid LSA list")
        if lsa_list.__contains__(lsa_identifier):
            lsa_list.remove(lsa_identifier)

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
