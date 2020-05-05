import threading
import time

import neighbor.neighbor as neighbor
import packet.packet as packet
import conf.conf as conf
import general.timer as timer
import general.sock as sock
import general.utils as utils

'''
This class represents the OSPF interface and contains its data and operations
'''


class Interface:
    #  OSPF interface parameters
    type = 0
    physical_identifier = ''  # Ex: ens33 - Interface identifier given by the OS
    ospf_identifier = 0  # Just for OSPFv3 - Interface identifier given by OSPF
    ipv4_address = '0.0.0.0'  # Just for OSPFv2
    ipv6_address = '::'  # Just for OSPFv3 - Link-local address
    network_mask = '0.0.0.0'  # Just for OSPFv2
    link_prefixes = []  # Just for OSPFv3
    area_id = '0.0.0.0'  # 0.0.0.0 - Backbone area
    hello_interval = 0
    router_dead_interval = 0
    router_priority = 0
    neighbors = {}
    designated_router = '0.0.0.0'  # 0.0.0.0 - No DR known
    backup_designated_router = '0.0.0.0'
    cost = 0
    max_ip_datagram = 0
    instance_id = 0  # Just for OSPFv3 - Default is 0 TODO: Allow router to operate more than one instance of OSPFv3
    transmission_delay = 0
    retransmission_interval = 0
    link_local_lsa_list = []  # Just for OSPFv3

    #  Implementation-specific parameters
    socket = None  # Socket that will send packets
    pipeline = None  # For receiving incoming packets
    interface_shutdown = None  # Signals interface thread to shutdown
    hello_packet_to_send = None
    hello_thread = None
    lsa_lock = None  # For controlling access to interface LSA list

    #  Hello timer and its parameters
    hello_timer = None
    offset = 0
    timeout = None
    timer_shutdown = None
    timer_seconds = 0

    def __init__(self, physical_identifier, ipv4_address, ipv6_address, network_mask, link_prefixes, area_id, pipeline,
                 interface_shutdown):
        self.type = conf.BROADCAST_INTERFACE  # TODO: Create point-to-point interface
        self.physical_identifier = physical_identifier
        self.ospf_identifier = Interface.ospf_identifier_generator(self.physical_identifier, conf.INTERFACE_NAMES)
        self.ipv4_address = ipv4_address
        self.ipv6_address = ipv6_address
        self.network_mask = network_mask
        self.link_prefixes = link_prefixes
        self.area_id = area_id
        self.hello_interval = conf.HELLO_INTERVAL
        self.router_dead_interval = conf.ROUTER_DEAD_INTERVAL
        self.router_priority = conf.ROUTER_PRIORITY
        self.neighbors = {}
        self.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.cost = conf.INTERFACE_COST
        self.max_ip_datagram = conf.MTU
        self.instance_id = 0
        self.transmission_delay = 0
        self.retransmission_interval = 0
        self.link_local_lsa_list = []

        self.socket = sock.Socket()
        self.pipeline = pipeline
        self.interface_shutdown = interface_shutdown
        self.hello_packet_to_send = packet.Packet()
        if self.ipv4_address != '':  # Running OSPFv2 protocol
            self.hello_packet_to_send.create_header_v2(
                conf.PACKET_TYPE_HELLO, conf.ROUTER_ID, area_id, conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
        else:  # Running OSPFv3 protocol
            source_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(self.physical_identifier)
            destination_address = conf.ALL_OSPF_ROUTERS_IPV6
            self.hello_packet_to_send.create_header_v3(
                conf.PACKET_TYPE_HELLO, conf.ROUTER_ID, area_id, self.instance_id, source_address, destination_address)
        self.lsa_lock = threading.RLock()

        self.hello_timer = timer.Timer()
        self.timeout = threading.Event()
        self.timer_shutdown = threading.Event()
        self.timer_seconds = self.hello_interval

    #  Interface main method
    def interface_loop(self):
        #  Starts Hello timer
        self.hello_thread = threading.Thread(target=self.hello_timer.interval_timer,
                                             args=(self.offset, self.timeout, self.timer_shutdown, self.timer_seconds))
        self.hello_thread.start()
        self.timeout.set()  # If this thread reaches "if" below before losing CPU, it will immediately send Hello packet
        self.interface_shutdown.clear()

        while not(self.interface_shutdown.is_set()):  # Until interface is signalled to shutdown
            #  Deletes neighbors that reached timeout
            for n in list(self.neighbors):
                if self.neighbors[n].is_expired():  # Neighbors that reached timeout can be deleted
                    self.delete_neighbor(n)

            #  Processes incoming packets
            if not self.pipeline.empty():
                data_array = self.pipeline.get()
                incoming_packet = data_array[0]
                source_ip = data_array[1]
                version = incoming_packet.header.version
                packet_type = incoming_packet.header.packet_type
                neighbor_id = incoming_packet.header.router_id

                if packet_type == conf.PACKET_TYPE_HELLO:
                    #  New neighbor
                    if neighbor_id not in self.neighbors:
                        neighbor_interface_id = 0
                        if version == conf.VERSION_IPV6:
                            neighbor_interface_id = incoming_packet.body.interface_id
                        neighbor_options = incoming_packet.body.options
                        new_neighbor = neighbor.Neighbor(  # Neighbor state is Init
                            neighbor_id, neighbor_interface_id, source_ip, neighbor_options, '0.0.0.0', '0.0.0.0')
                        self.neighbors[neighbor_id] = new_neighbor

                    #  Existing neighbor
                    neighbor_router = self.neighbors[neighbor_id]
                    neighbor_router.reset_timer()
                    time.sleep(0.1)  # Required to immediately give the CPU to the neighbor timer thread
                    #  Neighbor acknowledges router as neighbor
                    if (conf.ROUTER_ID in incoming_packet.body.neighbors) & (
                            neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_INIT):
                        self.elect_dr()
                        #  Neither this router nor neighbor are DR/BDR
                        if (conf.ROUTER_ID not in [self.designated_router, self.backup_designated_router]) & (
                                neighbor_id not in [self.designated_router, self.backup_designated_router]):
                            neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
                        else:  # Routers can become fully adjacent
                            neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_EXSTART)
                            neighbor_router.generate_dd_sequence_number()
                            dd_packet = packet.Packet()
                            if self.ipv4_address != '':
                                dd_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                                           self.area_id, conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                                dd_packet.create_db_description_packet_body(
                                    conf.MTU, conf.OPTIONS, True, True, True, self.neighbors[neighbor_id].dd_sequence,
                                    [], conf.VERSION_IPV4)
                            else:
                                dd_packet.create_header_v3(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                                           self.area_id, self.instance_id, self.ipv6_address, source_ip)
                                dd_packet.create_db_description_packet_body(
                                    conf.MTU, conf.OPTIONS, True, True, True, self.neighbors[neighbor_id].dd_sequence,
                                    [], conf.VERSION_IPV6)
                            self.send_packet(dd_packet, source_ip)
                    #  Neighbor does not, even if it did in the last Hello packets
                    elif conf.ROUTER_ID not in incoming_packet.body.neighbors:
                        neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_INIT)
                    else:
                        pass  # Timer already reset - Nothing else to do

                elif packet_type == conf.PACKET_TYPE_DB_DESCRIPTION:
                    if self.neighbors[neighbor_id].neighbor_state == conf.NEIGHBOR_STATE_EXSTART:
                        #  This router is the slave
                        if utils.Utils.ipv4_to_decimal(neighbor_id) > utils.Utils.ipv4_to_decimal(conf.ROUTER_ID):
                            self.neighbors[neighbor_id].set_neighbor_state(conf.NEIGHBOR_STATE_EXCHANGE)
                            self.neighbors[neighbor_id].master_slave = False
                            dd_packet = packet.Packet()
                            self.neighbors[neighbor_id].dd_sequence = incoming_packet.dd_sequence_number
                            if self.ipv4_address != '':
                                dd_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                                           self.area_id, conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                                dd_packet.create_db_description_packet_body(
                                    conf.MTU, conf.OPTIONS, False, True, False, self.neighbors[neighbor_id].dd_sequence,
                                    [], conf.VERSION_IPV4)
                            else:
                                dd_packet.create_header_v3(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                                           self.area_id, self.instance_id, self.ipv6_address, source_ip)
                                dd_packet.create_db_description_packet_body(
                                    conf.MTU, conf.OPTIONS, False, True, False, self.neighbors[neighbor_id].dd_sequence,
                                    [], conf.VERSION_IPV6)
                            self.send_packet(dd_packet, source_ip)
                        #  This router is the master
                        elif (not incoming_packet.body.i_bit) & (not incoming_packet.body.ms_bit) & (
                                incoming_packet.body.dd_sequence_number == self.neighbors[neighbor_id].dd_sequence) & (
                                utils.Utils.ipv4_to_decimal(neighbor_id) < utils.Utils.ipv4_to_decimal(conf.ROUTER_ID)):
                            self.neighbors[neighbor_id].set_neighbor_state(conf.NEIGHBOR_STATE_EXCHANGE)
                            self.neighbors[neighbor_id].master_slave = True
                elif packet_type == conf.PACKET_TYPE_LS_REQUEST:
                    pass

                elif packet_type == conf.PACKET_TYPE_LS_UPDATE:
                    pass

                elif packet_type == conf.PACKET_TYPE_LS_ACKNOWLEDGMENT:
                    pass

                else:
                    pass

            #  Sends Hello packet
            if self.timeout.is_set():
                self.create_hello_packet()
                if self.ipv4_address != '':
                    self.send_packet(self.hello_packet_to_send, conf.ALL_OSPF_ROUTERS_IPV4)
                else:
                    self.send_packet(self.hello_packet_to_send, conf.ALL_OSPF_ROUTERS_IPV6)
                self.timeout.clear()

        #  Interface signalled to shutdown
        self.shutdown_interface()

    #  Sends an OSPF packet through the interface
    def send_packet(self, packet_to_send, destination_address):
        packet_bytes = packet_to_send.pack_packet()
        if self.ipv4_address != '':  # OSPFv2
            self.socket.send_ipv4(packet_bytes, destination_address, self.physical_identifier)
        else:  # OSPFv3
            self.socket.send_ipv6(packet_bytes, destination_address, self.physical_identifier)

    #  Creates an OSPF Hello packet to be sent
    def create_hello_packet(self):
        if self.ipv4_address != '':  # OSPFv2
            self.hello_packet_to_send.create_hello_v2_packet_body(
                self.network_mask, self.hello_interval, conf.OPTIONS, self.router_priority, self.router_dead_interval,
                self.designated_router, self.backup_designated_router, self.neighbors)
        else:  # OSPFv3
            self.hello_packet_to_send.create_hello_v3_packet_body(
                self.ospf_identifier, self.hello_interval, conf.OPTIONS, self.router_priority,
                self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors)
        return self.hello_packet_to_send

    #  Performs the DR/BDR election
    def elect_dr(self):
        #  TODO: Implement DR election
        self.designated_router = '1.1.1.1'
        self.backup_designated_router = '0.0.0.0'

    def get_neighbor_count(self):
        return len(self.neighbors)

    #  Returns the number of adjacent neighbors
    def get_adjacent_neighbor_count(self):
        adjacent_neighbors = 0
        for n in self.neighbors:
            if self.neighbors[n].neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
                adjacent_neighbors += 1
        return adjacent_neighbors

    #  Deletes a neighbor from the list of active neighbors
    def delete_neighbor(self, neighbor_id):
        if neighbor_id in self.neighbors:
            self.neighbors[neighbor_id].delete_neighbor()  # Stops neighbor timer thread
            self.neighbors.pop(neighbor_id)

    #  Performs shutdown operations on the interface
    def shutdown_interface(self):
        for n in self.neighbors:  # Stops timer thread in all neighbors
            self.neighbors[n].delete_neighbor()
        self.neighbors = {}  # Cleans neighbor list - It will be reconstructed if interface is reactivated
        self.timer_shutdown.set()
        self.hello_thread.join()

    #  Given interface physical identifier, returns an unique OSPF interface identifier
    @staticmethod
    def ospf_identifier_generator(physical_identifier, identifiers_tuple):
        if physical_identifier in identifiers_tuple:
            i = 1
            for identifier in identifiers_tuple:
                if identifier == physical_identifier:
                    return i
                i += 1
        return 0

    #  #  #  #  #  #  #  #  #  #  #  #
    #  Link-local LSA list methods  #
    #  #  #  #  #  #  #  #  #  #  #  #

    #  Atomically gets all link-local LSAs from interface
    def get_link_local_lsa_list(self):
        with self.lsa_lock:
            return self.link_local_lsa_list

    #  Atomically gets a link-local LSA from interface
    def get_link_local_lsa(self, ls_type, link_state_id, advertising_router):
        with self.lsa_lock:
            for local_lsa in self.link_local_lsa_list:
                if local_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    return local_lsa
            return None

    #  Atomically deletes link-local LSA from interface
    def delete_link_local_lsa(self, ls_type, link_state_id, advertising_router):
        with self.lsa_lock:
            for local_lsa in self.link_local_lsa_list:
                if local_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    self.link_local_lsa_list.remove(local_lsa)

    #  Atomically deletes all link-local LSAs from interface
    def clean_link_local_lsa_list(self):
        with self.lsa_lock:
            self.link_local_lsa_list = []

    #  Atomically adds a link-local LSA to interface, or updates it if already present
    def add_link_local_lsa(self, new_lsa):
        with self.lsa_lock:
            #  Deletes previous instance of LSA, if present
            new_lsa_identifier = new_lsa.get_lsa_identifier()
            self.delete_link_local_lsa(new_lsa_identifier[0], new_lsa_identifier[1], new_lsa_identifier[2])

            self.link_local_lsa_list.append(new_lsa)
