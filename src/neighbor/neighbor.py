import threading
import random

import general.timer as timer
import conf.conf as conf
import general.utils as utils

'''
This class represents the OSPF neighbor and contains its data and operations
'''

DB_DESCRIPTION = "DB Description"
LS_REQUEST = "LS Request"
LS_UPDATE = "LS Update"


class Neighbor:

    def __init__(self, neighbor_id, neighbor_priority, neighbor_interface_id, neighbor_ip_address, neighbor_options,
                 neighbor_dr, neighbor_bdr, router_id):
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
        print(router_id + ": OSPFv" + str(utils.Utils.get_ospf_version(self.neighbor_ip_address)),
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
        self.inactivity_shutdown = threading.Event()
        self.last_sent_dd_description_packet = None  # Last DD Description packet sent to neighbor
        self.router_id = router_id

        #  Sets timer that monitors neighbor last activity
        timeout_seconds = conf.ROUTER_DEAD_INTERVAL
        self.inactivity_timer = timer.Timer()
        self.inactivity_thread = threading.Thread(
            target=self.inactivity_timer.single_shot_timer,
            args=(self.reset, self.inactivity_timeout, self.inactivity_shutdown, timeout_seconds))
        self.inactivity_thread.start()

        #  Packet retransmission timers
        self.retransmission_timer = timer.Timer()
        self.retransmission_thread = None
        self.retransmission_timeout = threading.Event()
        self.retransmission_shutdown = threading.Event()
        self.dd_packet_retransmit_timer = timer.Timer()
        self.dd_packet_retransmit_thread = None
        self.dd_packet_retransmit_timeout = threading.Event()
        self.dd_packet_retransmit_shutdown = threading.Event()
        self.ls_request_retransmit_timer = timer.Timer()
        self.ls_request_retransmit_thread = None
        self.ls_request_retransmit_timeout = threading.Event()
        self.ls_request_retransmit_shutdown = threading.Event()
        self.ls_update_retransmit_timer = timer.Timer()
        self.ls_update_retransmit_thread = None
        self.ls_update_retransmit_timeout = threading.Event()
        self.ls_update_retransmit_shutdown = threading.Event()

    #  Starts retransmission timer for specified packet type
    def start_retransmission_timer(self, packet_type):
        if packet_type not in [DB_DESCRIPTION, LS_REQUEST, LS_UPDATE]:
            raise ValueError("Invalid packet type")
        self.stop_retransmission_timer(packet_type)
        if packet_type == DB_DESCRIPTION:
            self.dd_packet_retransmit_timeout.clear()
            self.dd_packet_retransmit_shutdown.clear()
            self.dd_packet_retransmit_thread = threading.Thread(
                target=self.dd_packet_retransmit_timer.interval_timer,
                args=(0, self.dd_packet_retransmit_timeout, self.dd_packet_retransmit_shutdown,
                      conf.RETRANSMISSION_INTERVAL))
            self.dd_packet_retransmit_thread.start()
        elif packet_type == LS_REQUEST:
            self.ls_request_retransmit_timeout.clear()
            self.ls_request_retransmit_shutdown.clear()
            self.ls_request_retransmit_thread = threading.Thread(
                target=self.ls_request_retransmit_timer.interval_timer,
                args=(0, self.ls_request_retransmit_timeout, self.ls_request_retransmit_shutdown,
                      conf.RETRANSMISSION_INTERVAL))
            self.ls_request_retransmit_thread.start()
        else:  # LS Update packets
            self.ls_update_retransmit_timeout.clear()
            self.ls_update_retransmit_shutdown.clear()
            self.ls_update_retransmit_thread = threading.Thread(
                target=self.ls_update_retransmit_timer.interval_timer,
                args=(0, self.ls_update_retransmit_timeout, self.ls_update_retransmit_shutdown,
                      conf.RETRANSMISSION_INTERVAL))
            self.ls_update_retransmit_thread.start()

    #  Returns True if inactivity timer has fired - No activity from neighbor was received lately
    def is_expired(self):
        return self.inactivity_timeout.is_set()

    #  Returns True if retransmission timer for provided packet type has fired and resets flag if so
    def is_retransmission_time(self, packet_type):
        if packet_type not in [DB_DESCRIPTION, LS_REQUEST, LS_UPDATE]:
            raise ValueError("Invalid packet type")
        if packet_type == DB_DESCRIPTION:
            if self.dd_packet_retransmit_timeout.is_set() & (self.dd_packet_retransmit_thread is not None):
                if self.dd_packet_retransmit_thread.isAlive():
                    self.dd_packet_retransmit_timeout.clear()
                    return True
        elif packet_type == LS_REQUEST:
            if self.ls_request_retransmit_timeout.is_set() & (self.ls_request_retransmit_thread is not None):
                if self.ls_request_retransmit_thread.isAlive():
                    self.ls_request_retransmit_timeout.clear()
                    return True
        else:  # LS Update packet
            if self.ls_update_retransmit_timeout.is_set() & (self.ls_update_retransmit_thread is not None):
                if self.ls_update_retransmit_thread.isAlive():
                    self.ls_update_retransmit_timeout.clear()
                    return True
        return False

    #  Resets inactivity timer - Activity from neighbor has just been received
    def reset_inactivity_timer(self):
        self.reset.set()

    #  Stops retransmission timer
    def stop_retransmission_timer(self, packet_type):
        if packet_type not in [DB_DESCRIPTION, LS_REQUEST, LS_UPDATE]:
            raise ValueError("Invalid packet type")
        if packet_type == DB_DESCRIPTION:
            if self.dd_packet_retransmit_thread is not None:
                self.dd_packet_retransmit_shutdown.set()
                if self.dd_packet_retransmit_thread.isAlive():
                    self.dd_packet_retransmit_thread.join()
        elif packet_type == LS_REQUEST:
            if self.ls_request_retransmit_thread is not None:
                self.ls_request_retransmit_shutdown.set()
                if self.ls_request_retransmit_thread.isAlive():
                    self.ls_request_retransmit_thread.join()
        else:  # LS Update packet
            if self.ls_update_retransmit_thread is not None:
                self.ls_update_retransmit_shutdown.set()
                if self.ls_update_retransmit_thread.isAlive():
                    self.ls_update_retransmit_thread.join()

    #  Stops timer thread so that neighbor can be deleted
    def delete_neighbor(self):
        self.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        self.ls_retransmission_list = []
        self.db_summary_list = []
        self.ls_request_list = []
        self.inactivity_shutdown.set()
        self.inactivity_thread.join()
        self.stop_retransmission_timer(DB_DESCRIPTION)
        self.stop_retransmission_timer(LS_REQUEST)
        self.stop_retransmission_timer(LS_UPDATE)

    #  Changes neighbor state and prints a message
    def set_neighbor_state(self, new_state):
        old_state = self.neighbor_state
        if new_state != old_state:
            if old_state != conf.NEIGHBOR_STATE_DOWN:
                print(self.router_id + ": OSPFv" + str(utils.Utils.get_ospf_version(self.neighbor_ip_address)),
                      "neighbor", self.neighbor_id, "changed state from", old_state, "to", new_state)
            self.neighbor_state = new_state

    #  Increments DD Sequence Number, or generates a random number if set for first time
    def generate_dd_sequence_number(self):
        if self.dd_sequence == 0:
            self.dd_sequence = random.randrange(conf.MAX_VALUE_16_BITS + 1)
        else:
            self.dd_sequence += 1

    #  Updates the last received DB Description packet from the neighbor
    def update_last_received_dd_packet(self, i_bit, m_bit, ms_bit, options, dd_sequence):
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
        if lsa_identifier not in lsa_list:
            lsa_list.append(lsa_identifier)

    #  Deletes LSA identifier from one of the LSA lists
    def delete_lsa_identifier(self, lsa_list, lsa_identifier):
        if lsa_list not in [self.ls_retransmission_list, self.db_summary_list, self.ls_request_list]:
            raise ValueError("Invalid LSA list")
        if lsa_identifier in lsa_list:
            lsa_list.remove(lsa_identifier)
        if (lsa_list == self.ls_request_list) & (len(self.ls_request_list) == 0):
            self.stop_retransmission_timer(LS_REQUEST)
        elif (lsa_list == self.ls_retransmission_list) & (len(self.ls_retransmission_list) == 0):
            self.stop_retransmission_timer(LS_UPDATE)

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
