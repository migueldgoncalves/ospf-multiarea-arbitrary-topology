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

    def __init__(self, physical_identifier, ipv4_address, ipv6_address, network_mask, link_prefixes, area_id, pipeline,
                 interface_shutdown, version, lsdb):

        #  OSPF interface parameters

        self.type = conf.BROADCAST_INTERFACE  # TODO: Create point-to-point interface
        self.physical_identifier = physical_identifier  # Ex: ens33 - Interface identifier given by the OS
        #  Just for OSPFv3 - Interface identifier given by OSPF
        self.ospf_identifier = Interface.ospf_identifier_generator(self.physical_identifier, conf.INTERFACE_NAMES)
        self.ipv4_address = ipv4_address  # Just for OSPFv2
        self.ipv6_address = ipv6_address  # Just for OSPFv3 - Link-local address
        self.network_mask = network_mask  # Just for OSPFv2
        self.link_prefixes = link_prefixes  # Just for OSPFv3
        self.area_id = area_id  # 0.0.0.0 - Backbone area
        self.hello_interval = conf.HELLO_INTERVAL
        self.router_dead_interval = conf.ROUTER_DEAD_INTERVAL
        self.router_priority = conf.ROUTER_PRIORITY
        self.neighbors = {}
        self.designated_router = conf.DEFAULT_DESIGNATED_ROUTER  # 0.0.0.0 - No DR known
        self.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.cost = conf.INTERFACE_COST
        self.max_ip_datagram = conf.MTU
        #  TODO: Allow router to operate more than one instance of OSPFv3
        self.instance_id = 0  # Just for OSPFv3 - Default is 0
        self.transmission_delay = 0
        self.retransmission_interval = 0
        self.link_local_lsa_list = []  # Just for OSPFv3

        #  Implementation-specific parameters

        self.version = version
        self.socket = sock.Socket()  # Socket that will send packets
        self.pipeline = pipeline  # For receiving incoming packets
        self.interface_shutdown = interface_shutdown  # Signals interface thread to shutdown
        self.hello_packet_to_send = packet.Packet()
        if self.version == conf.VERSION_IPV4:  # Running OSPFv2 protocol
            self.hello_packet_to_send.create_header_v2(
                conf.PACKET_TYPE_HELLO, conf.ROUTER_ID, area_id, conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
        else:  # Running OSPFv3 protocol
            source_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(self.physical_identifier)
            destination_address = conf.ALL_OSPF_ROUTERS_IPV6
            self.hello_packet_to_send.create_header_v3(
                conf.PACKET_TYPE_HELLO, conf.ROUTER_ID, area_id, self.instance_id, source_address, destination_address)
        self.hello_thread = None
        self.lsa_lock = threading.RLock()  # For controlling access to interface LSA list
        self.lsdb = lsdb  # Reference to the area LSDB
        #  TODO: Implement retransmission timer

        self.hello_timer = timer.Timer()
        self.offset = 0
        self.timeout = threading.Event()
        self.timer_shutdown = threading.Event()
        self.timer_seconds = self.hello_interval

    #  #  #  #  #  #
    #  Main methods  #
    #  #  #  #  #  #

    #  Processes incoming packets forwarded by the router layer
    def interface_loop(self):
        #  Starts Hello timer
        self.hello_thread = threading.Thread(target=self.hello_timer.interval_timer,
                                             args=(self.offset, self.timeout, self.timer_shutdown, self.timer_seconds))
        self.hello_thread.start()  # Thread must be created and started after every interface shutdown
        self.timeout.set()  # If this thread reaches "if" below before losing CPU, it will immediately send Hello packet
        self.interface_shutdown.clear()

        while not(self.interface_shutdown.is_set()):  # Until interface is signalled to shutdown
            #  Deletes neighbors that reached timeout
            for n in list(self.neighbors):
                if self.neighbors[n].is_expired():  # Neighbors that reached timeout can be deleted
                    self.event_inactivity_timer(n)

            #  Processes incoming packets
            if not self.pipeline.empty():
                data_array = self.pipeline.get()
                incoming_packet = data_array[0]
                source_ip = data_array[1]
                version = incoming_packet.header.version
                packet_type = incoming_packet.header.packet_type
                neighbor_id = incoming_packet.header.router_id

                if packet_type == conf.PACKET_TYPE_HELLO:
                    #  Checks if Hello packet values match interface values
                    neighbor_network_mask = incoming_packet.body.network_mask
                    neighbor_hello_interval = incoming_packet.body.hello_interval
                    neighbor_dead_interval = incoming_packet.body.router_dead_interval
                    #  TODO: Do not check network mask on point-to-point links
                    if (self.network_mask != neighbor_network_mask) & (self.version == conf.VERSION_IPV4):
                        continue  # Discard Hello packet
                    if (neighbor_hello_interval != self.hello_interval) | (
                            neighbor_dead_interval != self.router_dead_interval):
                        continue
                    #  TODO: Check if E-bit value of neighbor matched this area's E-bit

                    #  New neighbor
                    if neighbor_id not in self.neighbors:
                        neighbor_interface_id = 0
                        if version == conf.VERSION_IPV6:
                            neighbor_interface_id = incoming_packet.body.interface_id
                        neighbor_priority = incoming_packet.body.router_priority
                        neighbor_options = incoming_packet.body.options
                        neighbor_dr = incoming_packet.body.designated_router
                        neighbor_bdr = incoming_packet.body.backup_designated_router
                        new_neighbor = neighbor.Neighbor(
                            neighbor_id, neighbor_priority, neighbor_interface_id, source_ip, neighbor_options,
                            neighbor_dr, neighbor_bdr)
                        self.neighbors[neighbor_id] = new_neighbor

                    #  Existing neighbor
                    self.event_hello_received(incoming_packet, source_ip, neighbor_id)

                if neighbor_id not in self.neighbors:  # Packet does not come from a neighbor router
                    continue

                if packet_type == conf.PACKET_TYPE_DB_DESCRIPTION:
                    if incoming_packet.body.interface_mtu > self.max_ip_datagram:
                        continue  # Neighbor MTU too large

                    neighbor_router = self.neighbors[neighbor_id]
                    neighbor_state = neighbor_router.neighbor_state

                    if neighbor_state == conf.NEIGHBOR_STATE_DOWN:
                        continue

                    if neighbor_state == conf.NEIGHBOR_STATE_INIT:
                        self.event_2_way_received(neighbor_router, neighbor_id, source_ip)

                    if neighbor_state == conf.NEIGHBOR_STATE_2_WAY:
                        continue

                    neighbor_options = incoming_packet.body.options
                    neighbor_i_bit = incoming_packet.body.i_bit
                    neighbor_m_bit = incoming_packet.body.m_bit
                    neighbor_ms_bit = incoming_packet.body.ms_bit
                    neighbor_lsa_headers = incoming_packet.body.lsa_headers

                    if neighbor_state == conf.NEIGHBOR_STATE_EXSTART:
                        #  This router is the slave
                        if neighbor_i_bit & neighbor_m_bit & neighbor_ms_bit:
                            if len(neighbor_lsa_headers) == 0:
                                if utils.Utils.ipv4_to_decimal(neighbor_id) > \
                                        utils.Utils.ipv4_to_decimal(conf.ROUTER_ID):
                                    neighbor_router.master_slave = False
                                    neighbor_router.dd_sequence = incoming_packet.body.dd_sequence_number
                                    neighbor_router.neighbor_options = neighbor_options
                                    self.event_negotiation_done(neighbor_router)
                        #  This router is the master
                        elif (not incoming_packet.body.i_bit) & (not incoming_packet.body.ms_bit):
                            if incoming_packet.body.dd_sequence_number == neighbor_router.dd_sequence:
                                if utils.Utils.ipv4_to_decimal(neighbor_id) < \
                                        utils.Utils.ipv4_to_decimal(conf.ROUTER_ID):
                                    neighbor_router.master_slave = True
                                    neighbor_router.neighbor_options = neighbor_options
                                    self.event_negotiation_done(neighbor_router)
                        else:
                            continue

                    if neighbor_state == conf.NEIGHBOR_STATE_EXCHANGE:
                        #  TODO: Implement resending if incoming packet is duplicate
                        invalid_ls_type = False
                        for header in incoming_packet.body.lsa_headers:
                            if ((self.version == conf.VERSION_IPV4) & (
                                    header.ls_type not in [conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK])) | (
                                    (self.version == conf.VERSION_IPV6) & (
                                    header.ls_type not in [conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK,
                                                           conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.LSA_TYPE_LINK])):
                                invalid_ls_type = True
                            else:  # LSA with valid type
                                local_lsa = self.lsdb.get_lsa(header.ls_type, header.link_state_id,
                                                              header.advertising_router, [self])
                                #  TODO: Implement LSA instance comparison
                                if local_lsa is None:  # This router does not have the LSA
                                    neighbor_router.ls_request_list.append(header)
                        if invalid_ls_type:
                            continue  # TODO: Invoke event SeqNumberMismatch

                        if neighbor_router.master_slave:  # This router is the master
                            if incoming_packet.body.dd_sequence_number != neighbor_router.dd_sequence:
                                continue  # TODO: Invoke event SeqNumberMismatch
                            #  TODO: Continue
                        else:  # This router is the slave
                            if incoming_packet.body.dd_sequence_number != (neighbor_router.dd_sequence + 1):
                                continue  # TODO: Invoke event SeqNumberMismatch
                            #  TODO: Continue

                    if neighbor_state == conf.NEIGHBOR_STATE_LOADING:
                        pass

                    if neighbor_state == conf.NEIGHBOR_STATE_FULL:
                        pass

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
                if self.version == conf.VERSION_IPV4:
                    self.send_packet(self.hello_packet_to_send, conf.ALL_OSPF_ROUTERS_IPV4)
                else:
                    self.send_packet(self.hello_packet_to_send, conf.ALL_OSPF_ROUTERS_IPV6)
                self.timeout.clear()

        #  Interface signalled to shutdown
        self.shutdown_interface()

    #  Sends an OSPF packet through the interface
    def send_packet(self, packet_to_send, destination_address):
        packet_bytes = packet_to_send.pack_packet()
        if self.version == conf.VERSION_IPV4:
            self.socket.send_ipv4(packet_bytes, destination_address, self.physical_identifier)
        else:
            self.socket.send_ipv6(packet_bytes, destination_address, self.physical_identifier)

    #  Performs the DR/BDR election
    def elect_dr(self):
        #  TODO: Implement DR election
        self.designated_router = '1.1.1.1'
        self.backup_designated_router = '0.0.0.0'

    #  Performs shutdown operations on the interface
    def shutdown_interface(self):
        for n in list(self.neighbors):  # Stops timer thread in all neighbors
            self.event_kill_nbr(n)
        self.neighbors = {}  # Cleans neighbor list - It will be reconstructed if interface is reactivated
        self.timer_shutdown.set()
        self.hello_thread.join()

    #  #  #  #  #  #  #  #  #  #  #  #  #
    #  Neighbor event handling methods  #
    #  #  #  #  #  #  #  #  #  #  #  #  #

    #  HelloReceived event
    def event_hello_received(self, incoming_packet, source_ip, neighbor_id):
        neighbor_router = self.neighbors[neighbor_id]
        neighbor_router.reset_timer()
        time.sleep(0.1)  # Required to immediately give the CPU to the neighbor timer thread
        if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_DOWN:
            neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_INIT)
        if conf.ROUTER_ID in incoming_packet.body.neighbors:
            #  Neighbor acknowledges this router as neighbor
            self.event_2_way_received(neighbor_router, neighbor_id, source_ip)
        else:
            self.event_1_way_received(neighbor_router)  # Neighbor does not, even if it did in the last Hello packets

    #  2-WayReceived event
    def event_2_way_received(self, neighbor_router, neighbor_id, source_ip):
        if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_INIT:
            self.elect_dr()  # TODO: Will this method be called here after interface state machine implementation?
            #  Neither this router nor neighbor are DR/BDR
            if (conf.ROUTER_ID not in [self.designated_router, self.backup_designated_router]) & (
                    neighbor_id not in [self.designated_router, self.backup_designated_router]):
                neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
            else:  # Routers can become fully adjacent
                neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_EXSTART)
                neighbor_router.generate_dd_sequence_number()
                dd_packet = packet.Packet()
                if self.version == conf.VERSION_IPV4:
                    dd_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                               self.area_id, conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                    dd_packet.create_db_description_packet_body(
                        conf.MTU, conf.OPTIONS, True, True, True, self.neighbors[neighbor_id].dd_sequence, [],
                        conf.VERSION_IPV4)
                else:
                    dd_packet.create_header_v3(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                               self.area_id, self.instance_id, self.ipv6_address, source_ip)
                    dd_packet.create_db_description_packet_body(
                        conf.MTU, conf.OPTIONS, True, True, True, self.neighbors[neighbor_id].dd_sequence, [],
                        conf.VERSION_IPV6)
                self.send_packet(dd_packet, source_ip)
        else:  # Nothing to do
            pass

    #  NegotiationDone event
    def event_negotiation_done(self, neighbor_router):
        neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_EXCHANGE)
        lsdb_summary = self.lsdb.get_lsa_headers([self])
        current_lsa_list = []
        for header in lsdb_summary:
            if header.ls_age == conf.MAX_AGE:
                neighbor_router.ls_retransmission_list.append(header)
            else:
                current_lsa_list.append(header)
        neighbor_router.db_summary_list = current_lsa_list

    #  ExchangeDone event
    def event_exchange_done(self):
        pass

    #  LoadingDone event
    def event_loading_done(self):
        pass

    #  AdjOK? event
    def event_adj_ok(self):
        pass  # TODO: Implement event after DR election is implemented

    #  SeqNumberMismatch event
    def event_seq_number_mismatch(self):
        pass

    #  BadLSReq event
    def event_bad_ls_req(self):
        pass

    #  KillNbr event
    def event_kill_nbr(self, neighbor_id):
        if neighbor_id in self.neighbors:
            self.neighbors[neighbor_id].delete_neighbor()  # Stops neighbor timer thread
            self.neighbors.pop(neighbor_id)

    #  InactivityTimer event
    def event_inactivity_timer(self, neighbor_id):
        self.event_kill_nbr(neighbor_id)

    #  1-WayReceived event
    def event_1_way_received(self, neighbor_router):
        if neighbor_router.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
            neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_INIT)
        else:
            pass

    #  #  #  #  #  #  #  #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #  #

    #  Creates an OSPF Hello packet to be sent
    def create_hello_packet(self):
        if self.version == conf.VERSION_IPV4:
            self.hello_packet_to_send.create_hello_v2_packet_body(
                self.network_mask, self.hello_interval, conf.OPTIONS, self.router_priority, self.router_dead_interval,
                self.designated_router, self.backup_designated_router, self.neighbors)
        else:
            self.hello_packet_to_send.create_hello_v3_packet_body(
                self.ospf_identifier, self.hello_interval, conf.OPTIONS, self.router_priority,
                self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors)
        return self.hello_packet_to_send

    def get_neighbor_count(self):
        return len(self.neighbors)

    #  Returns the number of adjacent neighbors
    def get_adjacent_neighbor_count(self):
        adjacent_neighbors = 0
        for n in self.neighbors:
            if self.neighbors[n].neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
                adjacent_neighbors += 1
        return adjacent_neighbors

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
