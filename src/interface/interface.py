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
        self.dd_packet = packet.Packet()
        self.ls_request_packet = packet.Packet()
        self.ls_update_packet = packet.Packet()
        self.ls_acknowledgement_packet = packet.Packet()
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

            #  Retransmits last DD Description, LS Request or LS Update packet to neighbor, if needed
            for n in list(self.neighbors):
                if self.neighbors[n].is_retransmission_time():
                    packet_to_send = self.neighbors[n].last_sent_packet
                    destination_address = self.neighbors[n].neighbor_ip_address
                    if packet_to_send is not None:  # Safety check
                        self.send_packet(packet_to_send, destination_address)

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

                    if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_DOWN:
                        continue

                    if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_INIT:
                        self.event_2_way_received(neighbor_router, neighbor_id, source_ip)

                    if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_2_WAY:
                        continue

                    neighbor_options = incoming_packet.body.options
                    neighbor_i_bit = incoming_packet.body.i_bit
                    neighbor_m_bit = incoming_packet.body.m_bit
                    neighbor_ms_bit = incoming_packet.body.ms_bit
                    neighbor_lsa_headers = incoming_packet.body.lsa_headers
                    received_at_exstart_state = False  # For packets processed both at Exstart and Exchange states

                    if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_EXSTART:
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
                                    neighbor_router.dd_sequence += 1
                                    neighbor_router.neighbor_options = neighbor_options
                                    received_at_exstart_state = True
                                    self.event_negotiation_done(neighbor_router)
                        else:
                            continue

                    if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_EXCHANGE:
                        #  TODO: Check if this verification is in the right place
                        neighbor_router.stop_retransmission_timer()
                        #  TODO: Implement resending if incoming packet is duplicate
                        invalid_ls_type = False
                        for header in incoming_packet.body.lsa_headers:
                            #  TODO: Consider other types of LSAs
                            if ((self.version == conf.VERSION_IPV4) & (header.get_ls_type(header.ls_type) not in [
                                conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK])) | (
                                    (self.version == conf.VERSION_IPV6) & (header.get_ls_type(header.ls_type) not in [
                                    conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK, conf.LSA_TYPE_INTRA_AREA_PREFIX,
                                    conf.LSA_TYPE_LINK])):
                                invalid_ls_type = True
                            else:  # LSA with valid type
                                local_lsa = self.lsdb.get_lsa(header.ls_type, header.link_state_id,
                                                              header.advertising_router, [self])
                                #  TODO: Implement LSA instance comparison
                                if local_lsa is None:  # This router does not have the LSA
                                    neighbor_router.add_lsa_identifier(
                                        neighbor_router.ls_request_list, header.get_lsa_identifier())
                        if invalid_ls_type:
                            self.event_seq_number_mismatch(neighbor_router, source_ip)
                            continue
                        if received_at_exstart_state:
                            continue  # Packet was received at Exstart state - All processing has been done

                        if neighbor_router.master_slave:  # This router is the master
                            if incoming_packet.body.dd_sequence_number != neighbor_router.dd_sequence:
                                self.event_seq_number_mismatch(neighbor_router, source_ip)
                                continue
                            neighbor_router.dd_sequence += 1
                            neighbor_router.db_summary_list = []  # All of this router LSAs are acknowledged  # TODO: Improve
                            #  This router and neighbor acknowledged that they have no more LSA headers to send
                            if (not incoming_packet.body.m_bit) & (not self.dd_packet.body.m_bit):
                                self.event_exchange_done(neighbor_router)
                            else:
                                #  Sends DB Description packet with M-bit clear
                                self.dd_packet.create_db_description_packet_body(
                                    self.max_ip_datagram, conf.OPTIONS, False, False, True, neighbor_router.dd_sequence,
                                    self.lsdb.get_lsa_headers([self], neighbor_router.db_summary_list), self.version)
                                self.send_packet(self.dd_packet, neighbor_router.neighbor_ip_address)
                            #  TODO: Implement case where LSA headers are sent in more than 1 DB Description packet
                        else:  # This router is the slave
                            if incoming_packet.body.dd_sequence_number != (neighbor_router.dd_sequence + 1):
                                self.event_seq_number_mismatch(neighbor_router, source_ip)
                                continue
                            neighbor_router.dd_sequence = incoming_packet.body.dd_sequence_number
                            #  Previous packet sent by slave is acknowledged
                            for header in self.dd_packet.body.lsa_headers:
                                neighbor_router.delete_lsa_identifier(
                                    neighbor_router.db_summary_list, header.get_lsa_identifier())
                            if len(neighbor_router.db_summary_list) == 0:
                                m_bit = True
                            else:
                                m_bit = False
                            #  Sends DB Description packet as response to master
                            self.dd_packet.create_db_description_packet_body(
                                self.max_ip_datagram, conf.OPTIONS, False, m_bit, False, neighbor_router.dd_sequence,
                                self.lsdb.get_lsa_headers([self], neighbor_router.db_summary_list), self.version)
                            self.send_packet(self.dd_packet, neighbor_router.neighbor_ip_address)
                            if (not m_bit) & (not incoming_packet.body.m_bit):
                                self.event_exchange_done(neighbor_router)

                    if neighbor_router.neighbor_state in [conf.NEIGHBOR_STATE_LOADING, conf.NEIGHBOR_STATE_FULL]:
                        #  TODO: Implement reception of duplicate packets both as master and as slave
                        #  self.event_seq_number_mismatch(neighbor_router, source_ip)
                        continue

                elif packet_type == conf.PACKET_TYPE_LS_REQUEST:
                    neighbor_router = self.neighbors[neighbor_id]
                    if neighbor_router.neighbor_state not in [
                            conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING, conf.NEIGHBOR_STATE_FULL]:
                        continue  # Packet ignored
                    if self.version == conf.VERSION_IPV4:
                        self.ls_update_packet.create_header_v2(conf.PACKET_TYPE_LS_UPDATE, conf.ROUTER_ID, self.area_id,
                                                               conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
                    else:
                        self.ls_update_packet.create_header_v3(
                            conf.PACKET_TYPE_LS_UPDATE, conf.ROUTER_ID, self.area_id, self.instance_id,
                            self.ipv6_address, neighbor_router.neighbor_ip_address)

                    lsa_not_found = False
                    self.ls_update_packet.create_ls_update_packet_body(self.version)
                    for lsa_identifier in incoming_packet.body.lsa_identifiers:
                        ls_type = lsa_identifier[0]
                        link_state_id = lsa_identifier[1]
                        advertising_router = lsa_identifier[2]
                        full_lsa = self.lsdb.get_lsa(ls_type, link_state_id, advertising_router, [self])
                        if full_lsa is None:
                            lsa_not_found = True
                        else:
                            self.ls_update_packet.add_lsa(full_lsa)
                    if lsa_not_found:
                        self.event_bad_ls_req(neighbor_router, source_ip)
                        continue
                    self.send_packet(self.ls_update_packet, neighbor_router.neighbor_ip_address)

                elif packet_type == conf.PACKET_TYPE_LS_UPDATE:
                    neighbor_router = self.neighbors[neighbor_id]
                    if neighbor_router.neighbor_state not in [
                            conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING, conf.NEIGHBOR_STATE_FULL]:
                        continue

                    lsa_identifiers = []
                    for lsa in incoming_packet.body.lsa_list:
                        lsa_identifiers.append(lsa.get_lsa_identifier())
                    for identifier in lsa_identifiers:
                        neighbor_router.delete_lsa_identifier(neighbor_router.ls_request_list, identifier)  # If there
                    # TODO: Implement retransmission of LS Request packets

                    for new_lsa in incoming_packet.body.lsa_list:
                        #  TODO: Compare instances of the same LSA
                        if self.lsdb.get_lsa(new_lsa.header.ls_type, new_lsa.header.link_state_id,
                                             new_lsa.header.advertising_router, [self]) is None:  # LSA is new
                            self.lsdb.add_lsa(new_lsa)
                    if self.version == conf.VERSION_IPV4:
                        self.ls_acknowledgement_packet.create_header_v2(
                            conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, conf.ROUTER_ID, self.area_id, conf.DEFAULT_AUTH,
                            conf.NULL_AUTHENTICATION)
                    else:
                        self.ls_acknowledgement_packet.create_header_v3(
                            conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, conf.ROUTER_ID, self.area_id, self.instance_id,
                            self.ipv6_address, neighbor_router.neighbor_ip_address)
                    self.ls_acknowledgement_packet.create_ls_acknowledgement_packet_body(self.version)
                    for new_lsa in incoming_packet.body.lsa_list:
                        self.ls_acknowledgement_packet.add_lsa_header(new_lsa.header)
                    self.send_packet(self.ls_acknowledgement_packet, neighbor_router.neighbor_ip_address)

                    if len(neighbor_router.ls_request_list) == 0:
                        self.event_loading_done(neighbor_router)

                elif packet_type == conf.PACKET_TYPE_LS_ACKNOWLEDGMENT:
                    pass  # TODO: Implement

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
        neighbor_router.reset_inactivity_timer()
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
                neighbor_router.master_slave = True
                if self.version == conf.VERSION_IPV4:
                    self.dd_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                                    self.area_id, conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                    self.dd_packet.create_db_description_packet_body(
                        conf.MTU, conf.OPTIONS, True, True, neighbor_router.master_slave,
                        self.neighbors[neighbor_id].dd_sequence, [], conf.VERSION_IPV4)
                else:
                    self.dd_packet.create_header_v3(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID,
                                                    self.area_id, self.instance_id, self.ipv6_address, source_ip)
                    self.dd_packet.create_db_description_packet_body(
                        conf.MTU, conf.OPTIONS, True, True, neighbor_router.master_slave,
                        self.neighbors[neighbor_id].dd_sequence, [], conf.VERSION_IPV6)
                self.send_packet(self.dd_packet, source_ip)
                neighbor_router.last_sent_packet = self.dd_packet
                neighbor_router.start_retransmission_timer()
        else:  # Nothing to do
            pass

    #  NegotiationDone event
    def event_negotiation_done(self, neighbor_router):
        neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_EXCHANGE)
        lsdb_summary = self.lsdb.get_lsa_headers([self], None)
        neighbor_router.db_summary_list = []
        for header in lsdb_summary:
            if header.ls_age == conf.MAX_AGE:
                neighbor_router.add_lsa_identifier(neighbor_router.ls_retransmission_list, header.get_lsa_identifier())
            else:
                neighbor_router.add_lsa_identifier(neighbor_router.db_summary_list, header.get_lsa_identifier())
        if neighbor_router.master_slave:  # This router is the master
            if self.version == conf.VERSION_IPV4:
                self.dd_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID, self.area_id,
                                                conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
            else:
                self.dd_packet.create_header_v3(
                    conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID, self.area_id, self.instance_id, self.ipv6_address,
                    neighbor_router.neighbor_ip_address)
            self.dd_packet.create_db_description_packet_body(
                self.max_ip_datagram, conf.OPTIONS, False, True, True, neighbor_router.dd_sequence,
                self.lsdb.get_lsa_headers([self], neighbor_router.db_summary_list), self.version)  # TODO: Case where not all LSAs fit in one packet
            self.send_packet(self.dd_packet, neighbor_router.neighbor_ip_address)

    #  ExchangeDone event
    def event_exchange_done(self, neighbor_router):
        if len(neighbor_router.ls_request_list) == 0:
            neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)
        else:
            neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_LOADING)
            if self.version == conf.VERSION_IPV4:
                self.ls_request_packet.create_header_v2(
                    conf.PACKET_TYPE_LS_REQUEST, conf.ROUTER_ID, self.area_id, conf.DEFAULT_AUTH,
                    conf.NULL_AUTHENTICATION)
            else:
                self.ls_request_packet.create_header_v3(
                    conf.PACKET_TYPE_LS_REQUEST, conf.ROUTER_ID, self.area_id, self.instance_id, self.ipv6_address,
                    neighbor_router.neighbor_ip_address)
            self.ls_request_packet.create_ls_request_packet_body(self.version)
            for identifier in neighbor_router.ls_request_list:
                self.ls_request_packet.add_lsa_info(identifier[0], identifier[1], identifier[2])
            self.send_packet(self.ls_request_packet, neighbor_router.neighbor_ip_address)

    #  LoadingDone event
    def event_loading_done(self, neighbor_router):
        neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)

    #  AdjOK? event
    def event_adj_ok(self):
        pass  # TODO: Implement event after DR election is implemented

    #  SeqNumberMismatch event
    def event_seq_number_mismatch(self, neighbor_router, source_ip):
        neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_EXSTART)
        neighbor_router.ls_retransmission_list = []
        neighbor_router.db_summary_list = []
        neighbor_router.ls_request_list = []
        neighbor_router.dd_sequence += 1
        neighbor_router.master_slave = True
        if self.version == conf.VERSION_IPV4:
            self.dd_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID, self.area_id,
                                            conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
            self.dd_packet.create_db_description_packet_body(
                conf.MTU, conf.OPTIONS, True, True, neighbor_router.master_slave, neighbor_router.dd_sequence, [],
                conf.VERSION_IPV4)
        else:
            self.dd_packet.create_header_v3(conf.PACKET_TYPE_DB_DESCRIPTION, conf.ROUTER_ID, self.area_id,
                                            self.instance_id, self.ipv6_address, source_ip)
            self.dd_packet.create_db_description_packet_body(
                conf.MTU, conf.OPTIONS, True, True, neighbor_router.master_slave, neighbor_router.dd_sequence, [],
                conf.VERSION_IPV6)
        self.send_packet(self.dd_packet, source_ip)
        neighbor_router.last_sent_packet = self.dd_packet
        neighbor_router.start_retransmission_timer()

    #  BadLSReq event
    def event_bad_ls_req(self, neighbor_router, source_ip):
        self.event_seq_number_mismatch(neighbor_router, source_ip)

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
            neighbor_router.ls_retransmission_list = []
            neighbor_router.db_summary_list = []
            neighbor_router.ls_request_list = []
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
