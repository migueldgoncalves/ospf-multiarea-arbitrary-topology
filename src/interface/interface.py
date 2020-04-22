import threading
import time

import neighbor.neighbor as neighbor
import packet.packet as packet
import conf.conf as conf
import general.timer as timer
import general.sock as sock
import general.utils as utils
import lsa.header as lsa_header
import lsa.lsa as lsa

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

    #  Implementation-specific parameters
    socket = None  # Socket that will send packets
    pipeline = None  # For receiving incoming packets
    interface_shutdown = None  # Signals interface thread to shutdown
    hello_packet_to_send = None
    hello_thread = None

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

                if packet_type == conf.PACKET_TYPE_HELLO:
                    neighbor_id = incoming_packet.header.router_id
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
                    self.neighbors[neighbor_id].reset_timer()
                    time.sleep(0.1)  # Required to immediately give the CPU to the neighbor timer thread
                    if conf.ROUTER_ID in incoming_packet.body.neighbors:  # Neighbor acknowledges router as neighbor
                        self.neighbors[neighbor_id].set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
                    else:  # Neighbor does not, even if it did in the last packets
                        self.neighbors[neighbor_id].set_neighbor_state(conf.NEIGHBOR_STATE_INIT)

            #  Sends Hello packet
            if self.timeout.is_set():
                packet_bytes = self.create_packet()
                if self.ipv4_address != '':  # OSPFv2
                    self.socket.send_ipv4(packet_bytes, conf.ALL_OSPF_ROUTERS_IPV4, self.physical_identifier)
                else:  # OSPFv3
                    self.socket.send_ipv6(packet_bytes, conf.ALL_OSPF_ROUTERS_IPV6, self.physical_identifier)
                self.timeout.clear()

                #  FIXME: Temporary
                interface_mtu = 1
                options = 2
                i_bit = False
                m_bit = True
                ms_bit = True
                dd_sequence_number = 3
                lsa_header_1 = lsa_header.Header(10, 20, 1, 30, '1.1.1.1', 40, conf.VERSION_IPV4)
                lsa_header_1.length = 24
                lsa_header_2 = lsa_header.Header(50, 60, 2, 70, '2.2.2.2', 80, conf.VERSION_IPV4)
                lsa_header_2.length = 28
                lsa_header_3 = lsa_header.Header(90, 0, 3, 100, '3.3.3.3', 110, conf.VERSION_IPV6)
                lsa_header_4 = lsa_header.Header(120, 0, 4, 130, '4.4.4.4', 140, conf.VERSION_IPV6)
                lsa_header_5 = lsa_header.Header(150, 0, 5, 160, '5.5.5.5', 170, conf.VERSION_IPV6)
                db_description_packet = packet.Packet()
                ls_request_packet = packet.Packet()
                ls_update_packet = packet.Packet()
                ls_acknowledgement_packet = packet.Packet()
                if self.ipv4_address != '':
                    db_description_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                                           self.area_id, conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                    db_description_packet.create_db_description_packet_body(
                        interface_mtu, options, i_bit, m_bit, ms_bit, dd_sequence_number, (lsa_header_1, lsa_header_2),
                        conf.VERSION_IPV4)
                    db_description_packet_bytes = db_description_packet.pack_packet()

                    ls_request_packet.create_header_v2(conf.PACKET_TYPE_LS_REQUEST, conf.ROUTER_ID, self.area_id,
                                                       conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                    ls_request_packet.create_ls_request_packet_body(conf.VERSION_IPV4)
                    ls_request_packet.add_lsa_info(conf.LSA_TYPE_ROUTER, '4.4.4.4', '4.4.4.4')
                    ls_request_packet.add_lsa_info(conf.LSA_TYPE_NETWORK, '222.222.1.2', '4.4.4.4')
                    ls_request_packet_bytes = ls_request_packet.pack_packet()

                    ls_update_packet.create_header_v2(conf.PACKET_TYPE_LS_UPDATE, conf.ROUTER_ID, self.area_id,
                                                      conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                    ls_update_packet.create_ls_update_packet_body(conf.VERSION_IPV4)
                    router_lsa = lsa.Lsa()
                    router_lsa.create_header(1, 34, 1, '1.1.1.1', '1.1.1.1', 2147483654, conf.VERSION_IPV4)
                    router_lsa.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
                    router_lsa.add_link_info_v2('3.3.3.3', '222.222.6.1', 1, 0, 64)
                    router_lsa.add_link_info_v2('222.222.6.0', '255.255.255.0', 3, 0, 64)
                    router_lsa.add_link_info_v2('222.222.3.2', '222.222.3.1', 2, 0, 10)
                    router_lsa.add_link_info_v2('222.222.2.0', '255.255.255.0', 3, 0, 10)
                    router_lsa.add_link_info_v2('222.222.1.0', '255.255.255.0', 3, 0, 1)
                    network_lsa = lsa.Lsa()
                    network_lsa.create_header(1, 34, 2, '222.222.3.2', '2.2.2.2', 2147483649, conf.VERSION_IPV4)
                    network_lsa.create_network_lsa_body('255.255.255.0', 0, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV4)
                    ls_update_packet.add_lsa(router_lsa)
                    ls_update_packet.add_lsa(network_lsa)
                    ls_update_packet_bytes = ls_update_packet.pack_packet()

                    ls_acknowledgement_packet.create_header_v2(conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, conf.ROUTER_ID,
                                                               self.area_id, conf.NULL_AUTHENTICATION,
                                                               conf.DEFAULT_AUTH)
                    ls_acknowledgement_packet.create_ls_acknowledgement_packet_body(conf.VERSION_IPV4)
                    ls_acknowledgement_packet.add_lsa_header(router_lsa.header)
                    ls_acknowledgement_packet.add_lsa_header(network_lsa.header)
                    ls_acknowledgement_packet_bytes = ls_acknowledgement_packet.pack_packet()

                    self.socket.send_ipv4(db_description_packet_bytes, '222.222.1.1', self.physical_identifier)
                    self.socket.send_ipv4(ls_request_packet_bytes, '222.222.1.1', self.physical_identifier)
                    self.socket.send_ipv4(ls_update_packet_bytes, '222.222.1.1', self.physical_identifier)
                    self.socket.send_ipv4(ls_acknowledgement_packet_bytes, '222.222.1.1', self.physical_identifier)
                else:
                    source_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(
                        self.physical_identifier)
                    destination_address = 'fe80::c001:18ff:fe34:10'
                    db_description_packet.create_header_v3(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                                           self.area_id, self.instance_id, source_address,
                                                           destination_address)
                    db_description_packet.create_db_description_packet_body(
                        interface_mtu, options, i_bit, m_bit, ms_bit, dd_sequence_number, (lsa_header_3, lsa_header_4),
                        conf.VERSION_IPV6)
                    db_description_packet_bytes = db_description_packet.pack_packet()

                    ls_request_packet.create_header_v3(conf.PACKET_TYPE_LS_REQUEST, conf.ROUTER_ID, self.area_id,
                                                       self.instance_id, source_address, destination_address)
                    ls_request_packet.create_ls_request_packet_body(conf.VERSION_IPV6)
                    ls_request_packet.add_lsa_info(conf.LSA_TYPE_ROUTER, '0.0.0.0', '4.4.4.4')
                    ls_request_packet.add_lsa_info(conf.LSA_TYPE_NETWORK, '0.0.0.1', '4.4.4.4')
                    ls_request_packet.add_lsa_info(conf.LSA_TYPE_INTRA_AREA_PREFIX, '0.0.0.0', '4.4.4.4')
                    ls_request_packet.add_lsa_info(conf.LSA_TYPE_LINK, '0.0.0.1', '4.4.4.4')
                    ls_request_packet_bytes = ls_request_packet.pack_packet()

                    ls_update_packet.create_header_v3(conf.PACKET_TYPE_LS_UPDATE, conf.ROUTER_ID, self.area_id,
                                                      self.instance_id, source_address, destination_address)
                    ls_update_packet.create_ls_update_packet_body(conf.VERSION_IPV6)
                    router_lsa = lsa.Lsa()
                    router_lsa.create_header(1, 0, 1, '0.0.0.0', '2.2.2.2', 2147483655, conf.VERSION_IPV6)
                    router_lsa.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
                    router_lsa.add_link_info_v3(2, 1, 6, 4, '3.3.3.3')
                    router_lsa.add_link_info_v3(2, 10, 5, 5, '2.2.2.2')
                    network_lsa = lsa.Lsa()
                    network_lsa.create_header(1, 34, 2, '222.222.3.2', '2.2.2.2', 2147483649, conf.VERSION_IPV4)
                    network_lsa.create_network_lsa_body('255.255.255.0', 0, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV4)
                    intra_area_prefix_lsa = lsa.Lsa()
                    intra_area_prefix_lsa.create_header(1, 0, 9, '0.0.0.0', '2.2.2.2', 2147483653, conf.VERSION_IPV6)
                    intra_area_prefix_lsa.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '2.2.2.2')
                    intra_area_prefix_lsa.add_prefix_info(64, 0, 10, '2001:db8:cafe:4::',
                                                          conf.LSA_TYPE_INTRA_AREA_PREFIX)
                    link_lsa = lsa.Lsa()
                    link_lsa.create_header(38, 0, 8, '0.0.0.4', '1.1.1.1', 2147483650, conf.VERSION_IPV6)
                    link_lsa.create_link_lsa_body(1, 51, 'fe80::c001:18ff:fe34:0')
                    link_lsa.add_prefix_info(64, 0, 0, '2001:db8:cafe:3::', conf.LSA_TYPE_LINK)
                    ls_update_packet.add_lsa(router_lsa)
                    ls_update_packet.add_lsa(network_lsa)
                    ls_update_packet.add_lsa(intra_area_prefix_lsa)
                    ls_update_packet.add_lsa(link_lsa)
                    ls_update_packet_bytes = ls_update_packet.pack_packet()

                    ls_acknowledgement_packet.create_header_v3(conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, conf.ROUTER_ID,
                                                               self.area_id, self.instance_id, source_address,
                                                               destination_address)
                    ls_acknowledgement_packet.create_ls_acknowledgement_packet_body(conf.VERSION_IPV6)
                    ls_acknowledgement_packet.add_lsa_header(router_lsa.header)
                    ls_acknowledgement_packet.add_lsa_header(network_lsa.header)
                    ls_acknowledgement_packet.add_lsa_header(intra_area_prefix_lsa.header)
                    ls_acknowledgement_packet.add_lsa_header(link_lsa.header)
                    ls_acknowledgement_packet_bytes = ls_acknowledgement_packet.pack_packet()

                    self.socket.send_ipv6(
                        db_description_packet_bytes, 'fe80::c001:18ff:fe34:10', self.physical_identifier)
                    self.socket.send_ipv6(
                        ls_request_packet_bytes, 'fe80::c001:18ff:fe34:10', self.physical_identifier)
                    self.socket.send_ipv6(
                        ls_update_packet_bytes, 'fe80::c001:18ff:fe34:10', self.physical_identifier)
                    self.socket.send_ipv6(
                        ls_acknowledgement_packet_bytes, 'fe80::c001:18ff:fe34:10', self.physical_identifier)

        #  Interface signalled to shutdown
        self.shutdown_interface()

    #  Creates an OSPF packet to be sent
    def create_packet(self):
        if self.ipv4_address != '':  # OSPFv2
            self.hello_packet_to_send.create_hello_v2_packet_body(
                self.network_mask, self.hello_interval, conf.OPTIONS, self.router_priority, self.router_dead_interval,
                self.designated_router, self.backup_designated_router, self.neighbors)
        else:  # OSPFv3
            self.hello_packet_to_send.create_hello_v3_packet_body(
                self.ospf_identifier, self.hello_interval, conf.OPTIONS, self.router_priority,
                self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors)
        return self.hello_packet_to_send.pack_packet()

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
