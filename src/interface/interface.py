import threading
import time
import queue
import copy
import warnings

import neighbor.neighbor as neighbor
import packet.packet as packet
import conf.conf as conf
import general.timer as timer
import general.sock as sock
import general.utils as utils
import lsa.header as header
import lsa.lsa as lsa

'''
This class represents the OSPF interface and contains its data and operations
'''


class Interface:

    DR = 'DR'
    BDR = 'BDR'

    ospf_identifier = 1

    def __init__(self, router_id, physical_identifier, ipv4_address, ipv6_address, network_mask, link_prefixes, area_id,
                 pipeline, interface_shutdown, version, lsdb, localhost, is_abr):

        #  OSPF interface parameters

        self.type = conf.BROADCAST_INTERFACE  # TODO: Create point-to-point interface
        self.state = conf.INTERFACE_STATE_DOWN
        self.physical_identifier = physical_identifier  # Ex: ens33 - Interface identifier given by the OS
        if version == conf.VERSION_IPV6:
            self.ospf_identifier = Interface.ospf_identifier  # Just for OSPFv3 - Interface identifier given by OSPF
            Interface.ospf_identifier += 1
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

        self.router_id = router_id
        self.version = version
        self.socket = sock.Socket()  # Socket that will send packets
        self.pipeline = pipeline  # For receiving incoming packets
        self.interface_shutdown = interface_shutdown  # Signals interface thread to shutdown
        self.hello_packet_to_send = packet.Packet()
        if self.version == conf.VERSION_IPV4:  # Running OSPFv2 protocol
            self.hello_packet_to_send.create_header_v2(
                conf.PACKET_TYPE_HELLO, self.router_id, area_id, conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
        else:  # Running OSPFv3 protocol
            source_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(self.physical_identifier)
            destination_address = conf.ALL_OSPF_ROUTERS_IPV6
            self.hello_packet_to_send.create_header_v3(
                conf.PACKET_TYPE_HELLO, self.router_id, area_id, self.instance_id, source_address, destination_address)
        self.lsa_lock = threading.RLock()  # For controlling access to interface LSA list
        self.lsdb = lsdb  # Reference to the area LSDB
        self.localhost = localhost
        self.flooding_pipeline = queue.Queue()  # Router layer will flood any LSAs here through the proper interfaces
        self.flooded_pipeline = queue.Queue()  # Content states whether provided LSA was flooded or not
        self.lsa_list_to_ack = queue.Queue()  # Stores LSA headers to be flooded in same LS Acknowledgement packet
        self.is_abr = is_abr  # True if router is ABR
        self.extension_lsa_pipeline = queue.Queue()  # Allows router class to fetch received extension LSAs

        self.hello_thread = None
        self.hello_timer = timer.Timer()
        self.hello_offset = 0
        self.hello_timeout = threading.Event()
        self.hello_timer_shutdown = threading.Event()
        self.hello_timer_seconds = self.hello_interval

        self.waiting_thread = None
        self.waiting_timer = timer.Timer()
        self.waiting_reset = threading.Event()
        self.waiting_timeout = threading.Event()
        self.waiting_timer_shutdown = threading.Event()
        self.waiting_timer_seconds = conf.ROUTER_DEAD_INTERVAL

        self.ls_ack_thread = None
        self.ls_ack_timer_seconds = conf.LS_ACK_TRANSMISSION_DELAY

    #  #  #  #  #  #
    #  Main methods  #
    #  #  #  #  #  #

    #  Processes incoming packets forwarded by the router layer
    def interface_loop(self):
        self.event_interface_up()  # Starts Hello timer and changes interface state from Down

        while not(self.interface_shutdown.is_set()):  # Until interface is signalled to shutdown
            #  Deletes neighbors that reached timeout
            for n in list(self.neighbors):
                if self.neighbors[n].is_expired():  # Neighbors that reached timeout can be deleted
                    self.event_inactivity_timer(n)

            #  Checks whether interface has stayed 40 seconds in Waiting state
            if self.waiting_timeout.is_set():
                self.event_wait_timer()

            #  Retransmits last DD Description, LS Request or LS Update packet to neighbor, if needed
            for n in list(self.neighbors):
                packet_to_send = None

                if self.neighbors[n].is_retransmission_time(neighbor.DB_DESCRIPTION):
                    if self.neighbors[n].last_sent_dd_description_packet is None:
                        self.neighbors[n].stop_retransmission_timer(neighbor.DB_DESCRIPTION)
                    else:
                        packet_to_send = self.neighbors[n].last_sent_dd_description_packet

                elif self.neighbors[n].is_retransmission_time(neighbor.LS_REQUEST):
                    if len(self.neighbors[n].ls_request_list) == 0:
                        self.neighbors[n].stop_retransmission_timer(neighbor.LS_REQUEST)
                        continue
                    packet_to_send = packet.Packet()
                    if self.version == conf.VERSION_IPV4:
                        packet_to_send.create_header_v2(conf.PACKET_TYPE_LS_REQUEST, self.router_id, self.area_id,
                                                        conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                    else:
                        packet_to_send.create_header_v3(
                            conf.PACKET_TYPE_LS_REQUEST, self.router_id, self.area_id, self.instance_id,
                            self.ipv6_address, self.neighbors[n].neighbor_ip_address)
                    packet_to_send.create_ls_request_packet_body(self.version)
                    for lsa_identifier in self.neighbors[n].ls_request_list:
                        packet_to_send.add_lsa_info(lsa_identifier[0], lsa_identifier[1], lsa_identifier[2])

                elif self.neighbors[n].is_retransmission_time(neighbor.LS_UPDATE):
                    if len(self.neighbors[n].ls_retransmission_list) == 0:
                        self.neighbors[n].stop_retransmission_timer(neighbor.LS_UPDATE)
                        break
                    packet_to_send = packet.Packet()
                    if self.version == conf.VERSION_IPV4:
                        packet_to_send.create_header_v2(conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id,
                                                        conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
                    else:
                        packet_to_send.create_header_v3(
                            conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id, self.instance_id,
                            self.ipv6_address, self.neighbors[n].neighbor_ip_address)
                    packet_to_send.create_ls_update_packet_body(self.version)
                    ls_retransmission_list = self.neighbors[n].ls_retransmission_list
                    for lsa_identifier in ls_retransmission_list:
                        lsa_to_send = self.lsdb.get_lsa(lsa_identifier[0], lsa_identifier[1], lsa_identifier[2], [self])
                        if lsa_to_send is not None:
                            packet_to_send.add_lsa(lsa_to_send)
                        else:
                            self.neighbors[n].delete_lsa_identifier(ls_retransmission_list, lsa_identifier)
                    if len(packet_to_send.body.lsa_list) == 0:
                        continue
                if packet_to_send is not None:
                    destination_address = self.neighbors[n].neighbor_ip_address
                    self.send_packet(packet_to_send, destination_address, self.neighbors[n])

            #  Processes incoming packets
            if not self.pipeline.empty():
                data_array = self.pipeline.get()
                incoming_packet = data_array[0]
                source_ip = data_array[1]
                version = incoming_packet.header.version
                packet_type = incoming_packet.header.packet_type
                neighbor_id = incoming_packet.header.router_id

                #  Packet does not come from a neighbor router
                if (packet_type != conf.PACKET_TYPE_HELLO) & (neighbor_id not in self.neighbors):
                    continue

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

                    neighbor_priority = incoming_packet.body.router_priority
                    neighbor_dr = incoming_packet.body.designated_router
                    neighbor_bdr = incoming_packet.body.backup_designated_router

                    #  New neighbor
                    if neighbor_id not in self.neighbors:
                        neighbor_interface_id = 0
                        if version == conf.VERSION_IPV6:
                            neighbor_interface_id = incoming_packet.body.interface_id
                        neighbor_options = incoming_packet.body.options
                        new_neighbor = neighbor.Neighbor(
                            neighbor_id, neighbor_priority, neighbor_interface_id, source_ip, neighbor_options,
                            neighbor_dr, neighbor_bdr, self.router_id)
                        self.neighbors[neighbor_id] = new_neighbor

                    #  Existing neighbor
                    neighbor_data_changed = False
                    if neighbor_priority != self.neighbors[neighbor_id].neighbor_priority:  # Neighbor priority changed
                        neighbor_data_changed = True
                    self.neighbors[neighbor_id].neighbor_priority = neighbor_priority
                    if self.version == conf.VERSION_IPV4:
                        dr_bdr_id = source_ip  # DR/BDR identified by interface IP address
                    else:
                        dr_bdr_id = neighbor_id  # DR/BDR identified by router ID
                    #  Neighbor now declared itself as DR, or stops declaring itself as DR
                    if (neighbor_dr == dr_bdr_id) & (self.neighbors[neighbor_id].neighbor_dr != dr_bdr_id):
                        neighbor_data_changed = True
                    if (neighbor_dr != dr_bdr_id) & (self.neighbors[neighbor_id].neighbor_dr == dr_bdr_id):
                        neighbor_data_changed = True
                    self.neighbors[neighbor_id].neighbor_dr = neighbor_dr
                    #  Neighbor now declared itself as BDR, or stops declaring itself as BDR
                    if (neighbor_bdr == dr_bdr_id) & (self.neighbors[neighbor_id].neighbor_bdr != dr_bdr_id):
                        neighbor_data_changed = True
                    if (neighbor_bdr != dr_bdr_id) & (self.neighbors[neighbor_id].neighbor_bdr == dr_bdr_id):
                        neighbor_data_changed = True
                    self.neighbors[neighbor_id].neighbor_bdr = neighbor_bdr
                    if self.neighbors[neighbor_id].neighbor_state not in [
                            conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
                        if neighbor_data_changed:
                            self.event_neighbor_change()  # This router must reevaluate who is DR and BDR
                        elif ((self.neighbors[neighbor_id].neighbor_ip_address in [neighbor_dr, neighbor_bdr]) & (
                                self.version == conf.VERSION_IPV4)) | ((neighbor_id in [neighbor_dr, neighbor_bdr]) & (
                                self.version == conf.VERSION_IPV6)):
                            if self.state == conf.INTERFACE_STATE_WAITING:
                                self.event_backup_seen()

                    self.event_hello_received(incoming_packet, source_ip, neighbor_id)

                elif packet_type == conf.PACKET_TYPE_DB_DESCRIPTION:
                    neighbor_router = self.neighbors[neighbor_id]
                    neighbor_options = incoming_packet.body.options
                    neighbor_i_bit = incoming_packet.body.i_bit
                    neighbor_m_bit = incoming_packet.body.m_bit
                    neighbor_ms_bit = incoming_packet.body.ms_bit
                    neighbor_dd_sequence_number = incoming_packet.body.dd_sequence_number
                    neighbor_lsa_headers = incoming_packet.body.lsa_headers
                    neighbor_router.update_last_received_dd_packet(
                        neighbor_i_bit, neighbor_m_bit, neighbor_ms_bit, neighbor_options, neighbor_dd_sequence_number)

                    if incoming_packet.body.interface_mtu > self.max_ip_datagram:
                        continue  # Neighbor MTU too large

                    if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_DOWN:
                        continue

                    elif neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_INIT:
                        self.event_2_way_received(neighbor_router, neighbor_id, source_ip, False)

                    elif neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_2_WAY:
                        continue

                    elif neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_EXSTART:
                        #  This router is the slave
                        if neighbor_i_bit & neighbor_m_bit & neighbor_ms_bit:
                            if len(neighbor_lsa_headers) == 0:
                                if utils.Utils.ipv4_to_decimal(neighbor_id) > \
                                        utils.Utils.ipv4_to_decimal(self.router_id):
                                    neighbor_router.master_slave = False
                                    neighbor_router.dd_sequence = neighbor_dd_sequence_number
                                    neighbor_router.neighbor_options = neighbor_options
                                    neighbor_router.stop_retransmission_timer(neighbor.DB_DESCRIPTION)
                                    self.event_negotiation_done(neighbor_router)
                        #  This router is the master
                        elif (not incoming_packet.body.i_bit) & (not incoming_packet.body.ms_bit):
                            if neighbor_dd_sequence_number == neighbor_router.dd_sequence:
                                if utils.Utils.ipv4_to_decimal(neighbor_id) < \
                                        utils.Utils.ipv4_to_decimal(self.router_id):
                                    neighbor_router.master_slave = True
                                    neighbor_router.dd_sequence += 1
                                    neighbor_router.neighbor_options = neighbor_options
                                    self.event_negotiation_done(neighbor_router)
                                    neighbor_router.stop_retransmission_timer(neighbor.DB_DESCRIPTION)
                                    self.dd_packet_to_ls_request_list(neighbor_router, incoming_packet)
                        else:
                            continue  # Ex: This router is the master but has no information to know it

                    elif neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_EXCHANGE:
                        #  Stores new LSA headers in the LS Request list of the neighbor
                        invalid_ls_type = self.dd_packet_to_ls_request_list(neighbor_router, incoming_packet)
                        if invalid_ls_type:  # At least one LSA with invalid type was detected
                            self.event_seq_number_mismatch(neighbor_router, source_ip)
                            continue
                        #  Removes acknowledged LSAs from DB Summary list
                        for lsa_header in neighbor_router.last_sent_dd_description_packet.body.lsa_headers:
                            lsa_identifier = lsa_header.get_lsa_identifier()
                            neighbor_router.delete_lsa_identifier(neighbor_router.db_summary_list, lsa_identifier)
                        m_bit = (len(neighbor_router.db_summary_list) != 0)
                        if m_bit:
                            # TODO: Only suitable if LSAs fit in 1 packet
                            neighbor_router.stop_retransmission_timer(neighbor.DB_DESCRIPTION)

                        dd_packet = neighbor_router.last_sent_dd_description_packet
                        if neighbor_router.master_slave:  # This router is the master
                            if incoming_packet.body.dd_sequence_number != neighbor_router.dd_sequence:
                                self.event_seq_number_mismatch(neighbor_router, source_ip)
                                continue
                            neighbor_router.dd_sequence += 1
                            #  This router and neighbor acknowledged that they have no more LSA headers to send
                            if (not incoming_packet.body.m_bit) & (not dd_packet.body.m_bit):
                                self.event_exchange_done(neighbor_router)
                            else:
                                #  Sends DB Description packet with either M-bit clear or more LSA headers
                                dd_packet.create_db_description_packet_body(
                                    self.max_ip_datagram, conf.OPTIONS, False, m_bit, True, neighbor_router.dd_sequence,
                                    self.lsdb.get_lsa_headers([self], neighbor_router.db_summary_list), self.version)
                                self.send_packet(dd_packet, neighbor_router.neighbor_ip_address, neighbor_router)
                            #  TODO: Implement case where LSA headers are sent in more than 1 DB Description packet
                        else:  # This router is the slave
                            if incoming_packet.body.dd_sequence_number != (neighbor_router.dd_sequence + 1):
                                self.event_seq_number_mismatch(neighbor_router, source_ip)
                                continue
                            neighbor_router.dd_sequence = incoming_packet.body.dd_sequence_number
                            #  Sends DB Description packet as response to master
                            dd_packet.create_db_description_packet_body(
                                self.max_ip_datagram, conf.OPTIONS, False, m_bit, False, neighbor_router.dd_sequence,
                                self.lsdb.get_lsa_headers([self], neighbor_router.db_summary_list), self.version)
                            self.send_packet(dd_packet, neighbor_router.neighbor_ip_address, neighbor_router)
                            if (not m_bit) & (not incoming_packet.body.m_bit):
                                self.event_exchange_done(neighbor_router)

                    elif neighbor_router.neighbor_state in [conf.NEIGHBOR_STATE_LOADING, conf.NEIGHBOR_STATE_FULL]:
                        #  TODO: Implement reception of duplicate packets both as master and as slave
                        self.event_seq_number_mismatch(neighbor_router, source_ip)

                    else:
                        continue

                elif packet_type == conf.PACKET_TYPE_LS_REQUEST:
                    neighbor_router = self.neighbors[neighbor_id]
                    ls_update_packet = packet.Packet()
                    if neighbor_router.neighbor_state not in [
                            conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING, conf.NEIGHBOR_STATE_FULL]:
                        continue  # Packet ignored
                    if self.version == conf.VERSION_IPV4:
                        ls_update_packet.create_header_v2(conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id,
                                                          conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
                    else:
                        ls_update_packet.create_header_v3(
                            conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id, self.instance_id,
                            self.ipv6_address, neighbor_router.neighbor_ip_address)

                    lsa_not_found = False
                    ls_update_packet.create_ls_update_packet_body(self.version)
                    for lsa_identifier in incoming_packet.body.lsa_identifiers:
                        ls_type = lsa_identifier[0]
                        link_state_id = lsa_identifier[1]
                        advertising_router = lsa_identifier[2]
                        full_lsa = self.lsdb.get_lsa(ls_type, link_state_id, advertising_router, [self])
                        if full_lsa is None:
                            lsa_not_found = True
                        else:
                            ls_update_packet.add_lsa(full_lsa)
                    if lsa_not_found:
                        self.event_bad_ls_req(neighbor_router, source_ip)
                        continue
                    self.send_packet(ls_update_packet, neighbor_router.neighbor_ip_address, neighbor_router)

                elif packet_type == conf.PACKET_TYPE_LS_UPDATE:
                    neighbor_router = self.neighbors[neighbor_id]
                    if neighbor_router.neighbor_state not in [
                            conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING, conf.NEIGHBOR_STATE_FULL]:
                        continue

                    for received_lsa in incoming_packet.body.lsa_list:

                        if not received_lsa.is_lsa_checksum_valid():
                            continue
                        if not received_lsa.is_ls_type_valid(received_lsa.header.ls_type, self.version):
                            continue

                        if received_lsa.is_extension_lsa():
                            self.extension_lsa_pipeline.put(received_lsa)
                            continue  # Is not inserted in area LSDB

                        local_copy = self.lsdb.get_lsa(received_lsa.header.ls_type, received_lsa.header.link_state_id,
                                                       received_lsa.header.advertising_router, [self])

                        if received_lsa.header.ls_age == conf.MAX_AGE:
                            #  Received LSA not in LSDB
                            if local_copy is None:
                                neighbor_state_exchange_loading = False  # No neighbors in states EXCHANGE or LOADING
                                for n in self.neighbors:
                                    if self.neighbors[n].neighbor_state in [
                                            conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING]:
                                        neighbor_state_exchange_loading = True
                                if not neighbor_state_exchange_loading:
                                    #  Acknowledge LSA
                                    ls_ack_packet = packet.Packet()
                                    if self.version == conf.VERSION_IPV4:
                                        ls_ack_packet.create_header_v2(
                                            conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id, self.area_id,
                                            conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
                                    else:
                                        ls_ack_packet.create_header_v3(
                                            conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id, self.area_id,
                                            self.instance_id, self.ipv6_address, neighbor_router.neighbor_ip_address)
                                    ls_ack_packet.create_ls_acknowledgement_packet_body(self.version)
                                    ls_ack_packet.add_lsa_header(received_lsa.header)
                                    self.send_packet(ls_ack_packet, neighbor_router.neighbor_ip_address, None)
                                    continue  # Proceed to next LSA

                        #  If LSA instance is not in LSDB or if received instance is more recent
                        if (local_copy is None) | (lsa.Lsa.get_fresher_lsa(received_lsa, local_copy) == header.FIRST):
                            self.add_lsa_to_flooding_pipeline(received_lsa, neighbor_id)  # This LSA will be flooded
                            for n in self.neighbors:  # Implicit acknowledgement
                                self.neighbors[n].delete_lsa_identifier(
                                    self.neighbors[n].ls_retransmission_list, received_lsa.get_lsa_identifier())
                            neighbor_router.delete_lsa_identifier(
                                neighbor_router.ls_request_list, received_lsa.get_lsa_identifier())
                            self.lsdb.add_lsa(received_lsa, self)

                            #  Adds LSA header to list of LSAs to acknowledge
                            lsa_flooded = self.flooded_pipeline.get()  # True if LSA flooded back out this interface
                            if (not lsa_flooded) & ((self.state != conf.INTERFACE_STATE_BACKUP) | (
                                    self.get_router_id_by_interface_ip(self.designated_router) == neighbor_id)):
                                self.lsa_list_to_ack.put(received_lsa.header)

                            #  Handles self-originated LSAs
                            if (received_lsa.is_lsa_self_originated(self.router_id)) & (local_copy is not None):
                                if (received_lsa.get_lsa_type_from_lsa() == conf.LSA_TYPE_NETWORK) & (
                                        self.designated_router != self.router_id):
                                    received_lsa.set_ls_age_max()
                                    self.flush_lsa(local_copy)
                                else:
                                    local_copy.header.ls_sequence_number = received_lsa.header.ls_sequence_number
                                    self.generate_lsa_instance(local_copy, self.router_id)
                                
                        #  If local LSA instance and received LSA are equally recent
                        elif lsa.Lsa.get_fresher_lsa(received_lsa, local_copy) == header.BOTH:
                            #  Implicit acknowledgement
                            if received_lsa.get_lsa_identifier() in neighbor_router.ls_retransmission_list:
                                neighbor_router.delete_lsa_identifier(
                                    neighbor_router.ls_retransmission_list, received_lsa.get_lsa_identifier())
                                if (self.get_router_id_by_interface_ip(self.designated_router) == neighbor_id) & (
                                        self.state == conf.INTERFACE_STATE_BACKUP):
                                    self.lsa_list_to_ack.put(received_lsa.header)  # Delayed acknowledgement
                            else:
                                #  Direct acknowledgement
                                ls_ack_packet = packet.Packet()
                                if self.version == conf.VERSION_IPV4:
                                    ls_ack_packet.create_header_v2(
                                        conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id, self.area_id,
                                        conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
                                else:
                                    ls_ack_packet.create_header_v3(
                                        conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id, self.area_id,
                                        self.instance_id, self.ipv6_address, neighbor_router.neighbor_ip_address)
                                ls_ack_packet.create_ls_acknowledgement_packet_body(self.version)
                                ls_ack_packet.add_lsa_header(received_lsa.header)
                                self.send_packet(ls_ack_packet, neighbor_router.neighbor_ip_address, None)

                        elif received_lsa.get_lsa_identifier() in neighbor_router.ls_request_list:
                            self.event_bad_ls_req(neighbor_router, source_ip)
                            break  # Stop processing the packet

                        else:  # Local copy of LSA is more recent
                            if (time.perf_counter() - local_copy.installation_time) >= conf.MIN_LS_ARRIVAL:
                                ls_update_packet = packet.Packet()
                                if self.version == conf.VERSION_IPV4:
                                    ls_update_packet.create_header_v2(
                                        conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id, conf.DEFAULT_AUTH,
                                        conf.NULL_AUTHENTICATION)
                                else:
                                    ls_update_packet.create_header_v3(
                                        conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id, self.instance_id,
                                        self.ipv6_address, neighbor_router.neighbor_ip_address)
                                ls_update_packet.create_ls_update_packet_body(self.version)
                                ls_update_packet.add_lsa(local_copy)
                                self.send_packet(ls_update_packet, neighbor_router.neighbor_ip_address, neighbor_router)

                    if len(neighbor_router.ls_request_list) == 0:
                        self.event_loading_done(neighbor_router)

                elif packet_type == conf.PACKET_TYPE_LS_ACKNOWLEDGMENT:
                    neighbor_router = self.neighbors[neighbor_id]
                    if neighbor_router.neighbor_state not in [
                            conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING, conf.NEIGHBOR_STATE_FULL]:
                        continue
                    else:
                        for ack in incoming_packet.body.lsa_headers:
                            ack_id = ack.get_lsa_identifier()
                            retransmission_list = neighbor_router.ls_retransmission_list
                            if not (ack_id in retransmission_list):
                                continue
                            else:
                                neighbor_router.delete_lsa_identifier(retransmission_list, ack_id)
                                if len(retransmission_list) == 0:
                                    neighbor_router.stop_retransmission_timer(neighbor.LS_UPDATE)

                else:
                    pass

            #  Remove LSAs with MaxAge if criteria are met
            neighbors_state_exchange_loading = False
            for n in self.neighbors:
                if self.neighbors[n].neighbor_state in [conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING]:
                    neighbors_state_exchange_loading = True
            if not neighbors_state_exchange_loading:
                lsa_list = self.lsdb.get_lsdb([self], None)
                for query_lsa in lsa_list:
                    lsa_identifier = query_lsa.get_lsa_identifier()
                    lsa_in_retransmission_list = False
                    for n in self.neighbors:
                        if lsa_identifier in self.neighbors[n].ls_retransmission_list:
                            lsa_in_retransmission_list = True
                    if (not lsa_in_retransmission_list) & (query_lsa.header.ls_age >= conf.MAX_AGE):
                        self.lsdb.delete_lsa(lsa_identifier[0], lsa_identifier[1], lsa_identifier[2], [self])

            #  Creates new instances of own LSAs if previous reach LS Age of 30 minutes
            lsa_instances = self.lsdb.get_lsdb([self], None)
            for query_lsa in lsa_instances:
                if (query_lsa.header.ls_age >= conf.LS_REFRESH_TIME) & (
                        query_lsa.header.advertising_router == self.router_id):
                    #  Creates and floods new instance of LSA with same body
                    self.event_ls_age_refresh_time(query_lsa)

            #  Sends Hello packet
            if self.hello_timeout.is_set():
                self.create_hello_packet()
                if self.version == conf.VERSION_IPV4:
                    self.send_packet(self.hello_packet_to_send, conf.ALL_OSPF_ROUTERS_IPV4, None)
                else:
                    self.send_packet(self.hello_packet_to_send, conf.ALL_OSPF_ROUTERS_IPV6, None)
                self.hello_timeout.clear()

        #  Interface signalled to shutdown
        self.event_interface_down()

    #  Sends an OSPF packet through the interface
    def send_packet(self, packet_to_send, destination_address, neighbor_router):
        packet_bytes = packet_to_send.pack_packet()
        if self.version == conf.VERSION_IPV4:
            self.socket.send_ipv4(packet_bytes, destination_address, self.physical_identifier, self.localhost)
        else:
            self.socket.send_ipv6(packet_bytes, destination_address, self.physical_identifier, self.localhost)

        if packet_to_send.header.packet_type == conf.PACKET_TYPE_LS_REQUEST:
            neighbor_router.start_retransmission_timer(neighbor.LS_REQUEST)
            for lsa_identifier in packet_to_send.body.lsa_identifiers:
                neighbor_router.add_lsa_identifier(neighbor_router.ls_request_list, lsa_identifier)

        elif packet_to_send.header.packet_type == conf.PACKET_TYPE_LS_UPDATE:
            lsa_identifiers = []
            for query_lsa in packet_to_send.body.lsa_list:
                lsa_identifiers.append(query_lsa.get_lsa_identifier())
            self.update_ls_retransmission_lists(lsa_identifiers, destination_address)

        #  Only master retransmits DB Description packets in state higher than EXSTART
        elif packet_to_send.header.packet_type == conf.PACKET_TYPE_DB_DESCRIPTION:
            if (neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_EXSTART) | neighbor_router.master_slave:
                neighbor_router.last_sent_dd_description_packet = packet_to_send
                neighbor_router.start_retransmission_timer(neighbor.DB_DESCRIPTION)

    #  Performs shutdown operations on the interface
    def shutdown_interface(self):
        for n in list(self.neighbors):  # Stops timer thread in all neighbors
            self.event_kill_nbr(n)
        self.hello_timer_shutdown.set()
        self.hello_thread.join()
        self.waiting_timer_shutdown.set()
        self.waiting_thread.join()
        self.ls_ack_thread.join()
        #  Reset interface values
        self.__init__(self.router_id, self.physical_identifier, self.ipv4_address, self.ipv6_address, self.network_mask,
                      self.link_prefixes, self.area_id, self.pipeline, self.interface_shutdown, self.version, self.lsdb,
                      self.localhost, self.is_abr)

    #  Groups LSAs to acknowledge and sends delayed acknowledgments
    def send_delayed_acknowledgements(self):
        last_packet_sending = time.perf_counter()
        while not self.interface_shutdown.is_set():
            if (time.perf_counter() - last_packet_sending) >= self.ls_ack_timer_seconds:
                last_packet_sending = time.perf_counter()

                if self.lsa_list_to_ack.qsize() > 0:
                    destination_address = self.get_flooding_ip_address()
                    ls_ack_packet = packet.Packet()
                    if self.version == conf.VERSION_IPV4:
                        ls_ack_packet.create_header_v2(conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id, self.area_id,
                                                       conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
                    else:
                        ls_ack_packet.create_header_v3(conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id, self.area_id,
                                                       self.instance_id, self.ipv6_address, destination_address)
                    ls_ack_packet.create_ls_acknowledgement_packet_body(self.version)
                    while self.lsa_list_to_ack.qsize() > 0:
                        lsa_header = self.lsa_list_to_ack.get()
                        ls_ack_packet.add_lsa_header(lsa_header)
                    self.send_packet(ls_ack_packet, destination_address, None)

    #  #  #  #  #  #  #  #  #  #  #  #  #
    #  Interface event handling methods  #
    #  #  #  #  #  #  #  #  #  #  #  #  #

    #  InterfaceUp event
    def event_interface_up(self):
        if self.state == conf.INTERFACE_STATE_DOWN:
            #  Starts Hello timer
            self.hello_thread = threading.Thread(
                target=self.hello_timer.interval_timer,
                args=(self.hello_offset, self.hello_timeout, self.hello_timer_shutdown, self.hello_timer_seconds))
            self.hello_thread.start()  # Thread must be created and started after every interface shutdown
            self.hello_timeout.set()  # Hello packet will be sent immediately if CPU is not lost
            self.interface_shutdown.clear()

            if self.type == conf.POINT_TO_POINT_INTERFACE:
                self.set_interface_state(conf.INTERFACE_STATE_POINT_POINT)
            elif self.router_priority == 0:  # Router not eligible to become DR/BDR
                self.set_interface_state(conf.INTERFACE_STATE_DROTHER)
            else:
                self.set_interface_state(conf.INTERFACE_STATE_WAITING)
                self.waiting_thread = threading.Thread(
                    target=self.waiting_timer.single_shot_timer,
                    args=(self.waiting_reset, self.waiting_timeout, self.waiting_timer_shutdown,
                          self.waiting_timer_seconds))
                self.waiting_thread.start()

            self.ls_ack_thread = threading.Thread(target=self.send_delayed_acknowledgements)
            self.ls_ack_thread.start()

    #  WaitTimer event
    def event_wait_timer(self):
        self.waiting_timer_shutdown.set()
        self.waiting_thread.join()
        self.waiting_timeout.clear()
        if self.state == conf.INTERFACE_STATE_WAITING:
            self.election_algorithm()

    #  BackupSeen event
    def event_backup_seen(self):
        self.event_wait_timer()

    #  NeighborChange event
    def event_neighbor_change(self):
        if self.state in [conf.INTERFACE_STATE_DROTHER, conf.INTERFACE_STATE_BACKUP, conf.INTERFACE_STATE_DR]:
            self.election_algorithm()

    #  InterfaceDown event
    def event_interface_down(self):
        self.shutdown_interface()

    #  Full election algorithm
    def election_algorithm(self):
        if self.state != conf.INTERFACE_STATE_DOWN:
            old_dr = self.designated_router
            old_bdr = self.backup_designated_router
            known_routers = self.election_algorithm_step_1()
            determined_bdr = self.election_algorithm_step_2(known_routers)
            determined_dr = self.election_algorithm_step_3(known_routers, determined_bdr)
            rerun_algorithm = self.election_algorithm_step_4(determined_dr, determined_bdr, True)
            if rerun_algorithm:
                self.set_dr_bdr(Interface.BDR, determined_bdr)
                self.set_dr_bdr(Interface.DR, determined_dr)
                known_routers = self.election_algorithm_step_1()  # Refreshes declared DR/BDR of this router
                determined_bdr = self.election_algorithm_step_2(known_routers)
                determined_dr = self.election_algorithm_step_3(known_routers, determined_bdr)
            self.election_algorithm_step_5(determined_dr, determined_bdr)
            self.set_dr_bdr(Interface.BDR, determined_bdr)
            self.set_dr_bdr(Interface.DR, determined_dr)
            self.election_algorithm_step_6(determined_dr, determined_bdr, old_dr, old_bdr)

    #  Election algorithm - Step 1
    def election_algorithm_step_1(self):
        #  In OSPFv2 DR/BDR are identified by their interface IP address, in OSPFv3 by their RID
        if self.version == conf.VERSION_IPV4:
            identifier = self.ipv4_address
        else:
            identifier = self.router_id
        known_routers = [[identifier, self.router_priority, self.designated_router, self.backup_designated_router]]
        for neighbor_id in self.neighbors:
            if self.neighbors[neighbor_id].neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
                neighbor_structure = self.neighbors[neighbor_id]
                if self.version == conf.VERSION_IPV4:
                    known_routers.append([neighbor_structure.neighbor_ip_address, neighbor_structure.neighbor_priority,
                                          neighbor_structure.neighbor_dr, neighbor_structure.neighbor_bdr])
                else:
                    known_routers.append([neighbor_structure.neighbor_id, neighbor_structure.neighbor_priority,
                                          neighbor_structure.neighbor_dr, neighbor_structure.neighbor_bdr])
        return known_routers

    #  Election algorithm - Step 2
    @staticmethod
    def election_algorithm_step_2(known_routers):
        group_1 = []
        group_2 = []
        for router_data in known_routers:
            router_id = router_data[0]
            router_priority = router_data[1]
            router_dr = router_data[2]
            router_bdr = router_data[3]
            if (router_dr == router_id) | (router_priority == 0):  # Router declares itself as DR or priority is 0
                pass
            elif (router_bdr == router_id) & (router_dr != router_id):  # Router declares itself as BDR only
                group_1.append(router_data)
            else:
                group_2.append(router_data)
        if len(group_1) > 0:
            group_to_process = group_1
        elif len(group_2) > 0:
            group_to_process = group_2
        else:  # All routers declare themselves as DR - No BDR can be found
            return '0.0.0.0'
        return Interface.rank_routers(group_to_process)  # RID of BDR

    #  Election algorithm - Step 3
    @staticmethod
    def election_algorithm_step_3(known_routers, determined_bdr):
        declared_as_dr = []
        for router_data in known_routers:
            router_id = router_data[0]
            router_priority = router_data[1]
            router_dr = router_data[2]
            if (router_dr == router_id) & (router_priority > 0):  # Router declares itself as DR and priority is not 0
                declared_as_dr.append(router_data)
        if len(declared_as_dr) > 0:
            return Interface.rank_routers(declared_as_dr)
        else:  # If no router declares itself as DR, the DR becomes the BDR from the previous step
            return determined_bdr

    #  Election algorithm - Step 4
    def election_algorithm_step_4(self, determined_dr, determined_bdr, first_run):
        if self.version == conf.VERSION_IPV4:
            identifier = self.ipv4_address
        else:
            identifier = self.router_id
        #  Steps 2 and 3 can only be rerun eventually if it is the algorithm first run
        if first_run:
            #  This router has become DR/BDR, or ceased being DR/BDR
            if ((identifier not in [self.designated_router, self.backup_designated_router]) & (
                    identifier in [determined_dr, determined_bdr])) | (
                    (identifier in [self.designated_router, self.backup_designated_router]) & (
                    identifier not in [determined_dr, determined_bdr])):
                return True
            #  This router is no longer the DR, or became the DR
            elif ((identifier == self.designated_router) & (identifier != determined_dr)) | (
                    (identifier != self.designated_router) & (identifier == determined_dr)):
                return True
            #  This router is no longer the BDR, or became the BDR
            elif ((identifier == self.backup_designated_router) & (identifier != determined_bdr)) | (
                    (identifier != self.backup_designated_router) & (identifier == determined_bdr)):
                return True
        return False  # This router maintains its status - Step 5 will be run next

    #  Election algorithm - Step 5
    def election_algorithm_step_5(self, determined_dr, determined_bdr):
        if self.version == conf.VERSION_IPV4:
            identifier = self.ipv4_address
        else:
            identifier = self.router_id
        if identifier == determined_dr:
            self.set_interface_state(conf.INTERFACE_STATE_DR)  # Nothing is done if state is already the desired one
        elif identifier == determined_bdr:
            self.set_interface_state(conf.INTERFACE_STATE_BACKUP)
        else:
            self.set_interface_state(conf.INTERFACE_STATE_DROTHER)

    #  Election algorithm - Step 6
    def election_algorithm_step_6(self, determined_dr, determined_bdr, old_dr, old_bdr):
        #  Either DR or BDR have changed
        if (old_dr != determined_dr) | (old_bdr != determined_bdr):
            for neighbor_id in self.neighbors:
                if self.neighbors[neighbor_id].neighbor_state not in [  # Neighbors in state 2-WAY or higher
                        conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
                    self.event_adj_ok(
                        self.neighbors[neighbor_id], neighbor_id, self.neighbors[neighbor_id].neighbor_ip_address)

    #  Given a list of RIDs, returns the first RID according to router priority, then by RID
    @staticmethod
    def rank_routers(router_list):
        router_priorities = [conf.ROUTER_PRIORITY]
        for router_data in router_list:
            if router_data[1] not in router_priorities:
                router_priorities.append(router_data[1])
        router_priorities.sort()
        sorted_routers = []
        for priority in router_priorities:
            same_priority = []
            for router_data in router_list:
                if router_data[1] == priority:
                    same_priority.append(utils.Utils.ipv4_to_decimal(router_data[0]))
            same_priority.sort()
            sorted_routers.extend(same_priority)
        for i in range(len(sorted_routers)):
            sorted_routers[i] = utils.Utils.decimal_to_ipv4(sorted_routers[i])
        return sorted_routers[len(sorted_routers) - 1]  # First router

    #  Changes interface state and prints a message
    def set_interface_state(self, new_state):
        old_state = self.state
        if new_state != old_state:
            print(self.router_id + ": OSPFv" + str(self.version), "interface", self.physical_identifier,
                  "changed state from", old_state, "to", new_state)
            self.state = new_state
            self.event_interface_state_change(old_state, new_state)  # Updates Router-LSA if needed

    #  Changes DR or BDR value and prints a message
    def set_dr_bdr(self, value_name, new_value):
        if self.version == conf.VERSION_IPV4:
            prefix = utils.Utils.get_ipv4_prefix_from_interface_name(self.physical_identifier)[0]
        else:
            prefix = utils.Utils.get_ipv6_prefix_from_interface_name(self.physical_identifier)[0]
        if (value_name == Interface.DR) & (new_value != self.designated_router):
            print(self.router_id + ": OSPFv" + str(self.version), value_name, "changed from", self.designated_router,
                  "to", new_value, "at network", prefix)
            old_value = self.designated_router
            self.designated_router = new_value
            self.event_network_dr_change(old_value, new_value)
        elif (value_name == Interface.BDR) & (new_value != self.backup_designated_router):
            print(self.router_id + ": OSPFv" + str(self.version), value_name, "changed from",
                  self.backup_designated_router, "to", new_value, "at network", prefix)
            self.backup_designated_router = new_value
        else:
            pass

    #  #  #  #  #  #  #  #  #  #  #  #  #
    #  Neighbor event handling methods  #
    #  #  #  #  #  #  #  #  #  #  #  #  #

    #  HelloReceived event
    def event_hello_received(self, incoming_packet, source_ip, neighbor_id):
        neighbor_router = self.neighbors[neighbor_id]
        neighbor_router.reset_inactivity_timer()
        time.sleep(0.1)  # Required to immediately give the CPU to the neighbor timer thread
        if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_DOWN:
            self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_INIT)
        if self.router_id in incoming_packet.body.neighbors:
            #  Neighbor acknowledges this router as neighbor
            self.event_2_way_received(neighbor_router, neighbor_id, source_ip, False)
        else:
            self.event_1_way_received(neighbor_router)  # Neighbor does not, even if it did in the last Hello packets

    #  2-WayReceived event
    def event_2_way_received(self, neighbor_router, neighbor_id, source_ip, adj_ok_event):
        if (neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_INIT) | adj_ok_event:  # If called from event AdjOk
            self.event_neighbor_change()
            #  Neither this router nor neighbor are DR/BDR
            if not self.should_be_fully_adjacent(neighbor_id):
                self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_2_WAY)
            else:  # Routers can become fully adjacent
                self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_EXSTART)
                neighbor_router.generate_dd_sequence_number()
                neighbor_router.master_slave = True
                neighbor_router.last_sent_dd_description_packet = packet.Packet()
                if self.version == conf.VERSION_IPV4:
                    neighbor_router.last_sent_dd_description_packet.create_header_v2(
                        conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id, conf.NULL_AUTHENTICATION,
                        conf.DEFAULT_AUTH)
                    neighbor_router.last_sent_dd_description_packet.create_db_description_packet_body(
                        conf.MTU, conf.OPTIONS, True, True, neighbor_router.master_slave,
                        self.neighbors[neighbor_id].dd_sequence, [], conf.VERSION_IPV4)
                else:
                    neighbor_router.last_sent_dd_description_packet.create_header_v3(
                        conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id, self.instance_id,
                        self.ipv6_address, source_ip)
                    neighbor_router.last_sent_dd_description_packet.create_db_description_packet_body(
                        conf.MTU, conf.OPTIONS, True, True, neighbor_router.master_slave,
                        self.neighbors[neighbor_id].dd_sequence, [], conf.VERSION_IPV6)
                self.send_packet(neighbor_router.last_sent_dd_description_packet, source_ip, neighbor_router)
        else:  # Nothing to do
            pass

    #  NegotiationDone event
    def event_negotiation_done(self, neighbor_router):
        self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_EXCHANGE)
        lsdb_summary = self.lsdb.get_lsa_headers([self], None)
        neighbor_router.db_summary_list = []
        for lsa_header in lsdb_summary:
            if lsa_header.ls_age == conf.MAX_AGE:
                neighbor_router.add_lsa_identifier(
                    neighbor_router.ls_retransmission_list, lsa_header.get_lsa_identifier())
            else:
                neighbor_router.add_lsa_identifier(neighbor_router.db_summary_list, lsa_header.get_lsa_identifier())
        dd_packet = neighbor_router.last_sent_dd_description_packet
        if self.version == conf.VERSION_IPV4:
            dd_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id, conf.DEFAULT_AUTH,
                                       conf.NULL_AUTHENTICATION)
        else:
            dd_packet.create_header_v3(conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id, self.instance_id,
                                       self.ipv6_address, neighbor_router.neighbor_ip_address)
        dd_packet.create_db_description_packet_body(
            self.max_ip_datagram, conf.OPTIONS, False, True, neighbor_router.master_slave,
            neighbor_router.dd_sequence, self.lsdb.get_lsa_headers([self], neighbor_router.db_summary_list),
            self.version)  # TODO: Case where not all LSAs fit in one packet
        self.send_packet(dd_packet, neighbor_router.neighbor_ip_address, neighbor_router)

    #  ExchangeDone event
    def event_exchange_done(self, neighbor_router):
        if len(neighbor_router.ls_request_list) == 0:
            self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_FULL)
        else:
            self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_LOADING)
            ls_request_packet = packet.Packet()
            if self.version == conf.VERSION_IPV4:
                ls_request_packet.create_header_v2(
                    conf.PACKET_TYPE_LS_REQUEST, self.router_id, self.area_id, conf.DEFAULT_AUTH,
                    conf.NULL_AUTHENTICATION)
            else:
                ls_request_packet.create_header_v3(
                    conf.PACKET_TYPE_LS_REQUEST, self.router_id, self.area_id, self.instance_id, self.ipv6_address,
                    neighbor_router.neighbor_ip_address)
            ls_request_packet.create_ls_request_packet_body(self.version)
            for identifier in neighbor_router.ls_request_list:
                ls_request_packet.add_lsa_info(identifier[0], identifier[1], identifier[2])
            self.send_packet(ls_request_packet, neighbor_router.neighbor_ip_address, neighbor_router)

    #  LoadingDone event
    def event_loading_done(self, neighbor_router):
        if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_LOADING:
            self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_FULL)

    #  AdjOK? event
    def event_adj_ok(self, neighbor_router, neighbor_id, source_ip):
        if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_2_WAY:
            if self.should_be_fully_adjacent(neighbor_id):
                self.event_2_way_received(neighbor_router, neighbor_id, source_ip, True)
            else:
                pass  # Neighbor remains at state 2-WAY
        elif neighbor_router.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
            if self.should_be_fully_adjacent(neighbor_id):
                pass  # Neighbor remains at state EXSTART or higher
            else:
                self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_2_WAY)
                neighbor_router.ls_retransmission_list = []
                neighbor_router.db_summary_list = []
                neighbor_router.ls_request_list = []

    #  SeqNumberMismatch event
    def event_seq_number_mismatch(self, neighbor_router, source_ip):
        self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_EXSTART)
        neighbor_router.ls_retransmission_list = []
        neighbor_router.db_summary_list = []
        neighbor_router.ls_request_list = []
        neighbor_router.dd_sequence += 1
        neighbor_router.master_slave = True
        dd_packet = neighbor_router.last_sent_dd_description_packet
        if self.version == conf.VERSION_IPV4:
            dd_packet.create_header_v2(conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id,
                                       conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
            dd_packet.create_db_description_packet_body(
                conf.MTU, conf.OPTIONS, True, True, neighbor_router.master_slave, neighbor_router.dd_sequence, [],
                conf.VERSION_IPV4)
        else:
            dd_packet.create_header_v3(conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id, self.instance_id,
                                       self.ipv6_address, source_ip)
            dd_packet.create_db_description_packet_body(
                conf.MTU, conf.OPTIONS, True, True, neighbor_router.master_slave, neighbor_router.dd_sequence, [],
                conf.VERSION_IPV6)
        self.send_packet(dd_packet, source_ip, neighbor_router)

    #  BadLSReq event
    def event_bad_ls_req(self, neighbor_router, source_ip):
        self.event_seq_number_mismatch(neighbor_router, source_ip)

    #  KillNbr event
    def event_kill_nbr(self, neighbor_id):
        if neighbor_id in self.neighbors:
            self.neighbors[neighbor_id].delete_neighbor()  # Stops neighbor timer threads
            self.neighbors.pop(neighbor_id)
            self.event_neighbor_change()  # A neighbor has left the link - DR election algorithm must be run

    #  InactivityTimer event
    def event_inactivity_timer(self, neighbor_id):
        self.event_kill_nbr(neighbor_id)

    #  1-WayReceived event
    def event_1_way_received(self, neighbor_router):
        if neighbor_router.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
            self.set_neighbor_state(neighbor_router, conf.NEIGHBOR_STATE_INIT)
            neighbor_router.ls_retransmission_list = []
            neighbor_router.db_summary_list = []
            neighbor_router.ls_request_list = []
            self.event_neighbor_change()
        else:
            pass

    #  Given a DB Description packet, stores its LSA headers in the respective neighbor LS Request list if needed
    def dd_packet_to_ls_request_list(self, neighbor_router, incoming_packet):
        #  TODO: Check if this verification is in the right place
        neighbor_router.stop_retransmission_timer(neighbor.DB_DESCRIPTION)
        #  TODO: Implement resending if incoming packet is duplicate
        invalid_ls_type = False
        for lsa_header in incoming_packet.body.lsa_headers:
            if not lsa.Lsa.is_ls_type_valid(lsa_header.ls_type, self.version):
                invalid_ls_type = True
            else:
                local_lsa = self.lsdb.get_lsa(  # None if no LSA found
                    lsa_header.ls_type, lsa_header.link_state_id, lsa_header.advertising_router, [self])
                # Router doesn't have LSA or has older instance
                if local_lsa is None:
                    neighbor_router.add_lsa_identifier(neighbor_router.ls_request_list, lsa_header.get_lsa_identifier())
                elif header.Header.get_fresher_lsa_header(lsa_header, local_lsa.header) == header.FIRST:
                    neighbor_router.add_lsa_identifier(neighbor_router.ls_request_list, lsa_header.get_lsa_identifier())
        return invalid_ls_type

    #  Given a neighbor RID, returns True if this router and the neighbor should become fully adjacent
    def should_be_fully_adjacent(self, neighbor_id):
        if self.type == conf.POINT_TO_POINT_INTERFACE:
            return True
        #  This router is DR/BDR
        if ((self.ipv4_address in [self.designated_router, self.backup_designated_router]) & (
                self.version == conf.VERSION_IPV4)) | ((self.router_id in [
                self.designated_router, self.backup_designated_router]) & (self.version == conf.VERSION_IPV6)):
            return True
        #  Neighbor is DR/BDR
        if ((self.neighbors[neighbor_id].neighbor_ip_address in [self.designated_router, self.backup_designated_router])
            & (self.version == conf.VERSION_IPV4)) | ((neighbor_id in [
                self.designated_router, self.backup_designated_router]) & (self.version == conf.VERSION_IPV6)):
            return True
        return False

    #  #  #  #  #  #  #  #  #  #
    #  LSA origination methods  #
    #  #  #  #  #  #  #  #  #  #

    #  Self-originated LSA reached LS Age of LSRefreshTime
    def event_ls_age_refresh_time(self, lsa_instance):
        self.generate_lsa_instance(lsa_instance, self.router_id)

    #  Interface state changed
    def event_interface_state_change(self, old_state, new_state):
        #  Router-LSA
        if self.version == conf.VERSION_IPV4:
            router_lsa = copy.deepcopy(self.lsdb.get_lsa(conf.LSA_TYPE_ROUTER, self.router_id, self.router_id, [self]))
        else:
            router_lsa = copy.deepcopy(self.lsdb.get_lsa(conf.LSA_TYPE_ROUTER, '0.0.0.0', self.router_id, [self]))
        if new_state == conf.INTERFACE_STATE_DOWN:
            router_lsa.body.delete_interface_link_info(self.ipv4_address, self.network_mask, self.ospf_identifier)
            self.generate_lsa_instance(router_lsa, self.router_id)
        elif self.version == conf.VERSION_IPV4:
            link_id = utils.Utils.get_ipv4_prefix_from_interface_name(self.physical_identifier)[0]
            link_data = self.network_mask
            link_type = conf.LINK_TO_STUB_NETWORK
            tos_number = conf.DEFAULT_TOS
            metric = self.cost
            is_changed = False
            if self.type == conf.POINT_TO_POINT_INTERFACE:
                if new_state == conf.INTERFACE_STATE_POINT_POINT:
                    if not router_lsa.has_link_info_v2(link_id, link_data, link_type, tos_number, metric):
                        router_lsa.body.add_link_info_v2(link_id, link_data, link_type, tos_number, metric)
                        is_changed = True
                elif old_state == conf.INTERFACE_STATE_POINT_POINT:
                    if router_lsa.has_link_info_v2(link_id, link_data, link_type, tos_number, metric):
                        router_lsa.body.delete_link_info_v2(link_id, link_data, link_type, tos_number, metric)
                        is_changed = True
            elif self.type == conf.BROADCAST_INTERFACE:
                if new_state == conf.INTERFACE_STATE_WAITING:
                    if not router_lsa.has_link_info_v2(link_id, link_data, link_type, tos_number, metric):
                        router_lsa.body.add_link_info_v2(link_id, link_data, link_type, tos_number, metric)
                        is_changed = True
            if is_changed:
                self.generate_lsa_instance(router_lsa, self.router_id)

        #  Network-LSA
        if (old_state == conf.INTERFACE_STATE_DR) & (old_state != new_state):
            if self.version == conf.VERSION_IPV4:
                network_lsa = self.lsdb.get_lsa(conf.LSA_TYPE_NETWORK, self.ipv4_address, self.router_id, [self])
            elif self.version == conf.VERSION_IPV6:
                network_lsa = self.lsdb.get_lsa(conf.LSA_TYPE_NETWORK, self.ospf_identifier, self.router_id, [self])
            else:
                raise ValueError("Invalid OSPF version")
            if network_lsa is not None:
                self.flush_lsa(network_lsa)

        #  Link-LSA
        if (old_state != new_state) & (self.version == conf.VERSION_IPV6):
            if len(self.link_local_lsa_list) == 0:
                ls_sequence_number = conf.INITIAL_SEQUENCE_NUMBER
            else:
                ls_sequence_number = self.get_link_local_lsa(
                    conf.LSA_TYPE_LINK, self.ospf_identifier, self.router_id).header.ls_sequence_number
            link_lsa = self.create_link_lsa(ls_sequence_number)
            if new_state == conf.INTERFACE_STATE_WAITING:
                self.install_flood_lsa(link_lsa, self.router_id)
            elif new_state == conf.INTERFACE_STATE_DOWN:
                self.flush_lsa(link_lsa)

        #  Intra-Area-Prefix-LSA
        if (old_state != new_state) & (self.version == conf.VERSION_IPV6):
            intra_area_prefix_lsa = self.lsdb.get_lsa(
                conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.DEFAULT_DESIGNATED_ROUTER, self.router_id, [self])
            if new_state == conf.INTERFACE_STATE_DOWN:
                self.flush_lsa(intra_area_prefix_lsa)

    #  Network DR changed
    def event_network_dr_change(self, old_dr, new_dr):
        if self.type == conf.BROADCAST_INTERFACE:
            #  Router-LSA
            if (old_dr == conf.DEFAULT_DESIGNATED_ROUTER) & (not self.is_transit_network(new_dr)):
                pass  # Interface left Waiting state and is connected to stub link
            elif self.version == conf.VERSION_IPV4:
                router_lsa = copy.deepcopy(
                    self.lsdb.get_lsa(conf.LSA_TYPE_ROUTER, self.router_id, self.router_id, [self]))
                if self.ipv4_address == self.designated_router:
                    link_id = self.ipv4_address
                else:
                    dr_id = self.get_router_id_by_interface_ip(self.designated_router)
                    link_id = self.neighbors[dr_id].neighbor_ip_address
                network_prefix = utils.Utils.get_ipv4_prefix_from_interface_name(self.physical_identifier)[0]
                router_lsa.delete_interface_link_info(self.ipv4_address, network_prefix, self.ospf_identifier)
                if self.is_transit_network(new_dr):
                    router_lsa.add_link_info_v2(
                        link_id, self.ipv4_address, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, self.cost)
                else:
                    router_lsa.add_link_info_v2(
                        network_prefix, self.network_mask, conf.LINK_TO_STUB_NETWORK, conf.DEFAULT_TOS, self.cost)
                self.generate_lsa_instance(router_lsa, self.router_id)
            elif self.version == conf.VERSION_IPV6:
                router_lsa = copy.deepcopy(self.lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, self.router_id, [self]))
                if self.router_id == self.designated_router:
                    neighbor_interface_id = self.ospf_identifier
                    neighbor_router_id = self.router_id
                else:
                    neighbor_interface_id = self.neighbors[self.designated_router].neighbor_interface_id
                    neighbor_router_id = self.neighbors[self.designated_router].neighbor_id
                router_lsa.delete_interface_link_info('', '', self.ospf_identifier)
                if self.is_transit_network(new_dr):
                    router_lsa.add_link_info_v3(conf.LINK_TO_TRANSIT_NETWORK, self.cost, self.ospf_identifier,
                                                neighbor_interface_id, neighbor_router_id)
                self.generate_lsa_instance(router_lsa, self.router_id)
            else:
                raise ValueError("Invalid OSPF version")

            #  Network-LSA
            if ((self.router_id in [old_dr, new_dr]) | (self.ipv4_address in [old_dr, new_dr])) & (old_dr != new_dr):
                if (new_dr in [self.router_id, self.ipv4_address]) & self.is_transit_network(new_dr):
                    network_lsa = self.create_network_lsa(conf.INITIAL_SEQUENCE_NUMBER)
                    self.install_flood_lsa(network_lsa, self.router_id)  # LSA is new in the LSDB
                elif old_dr in [self.router_id, self.ipv4_address]:
                    if self.version == conf.VERSION_IPV4:
                        link_state_id = self.ipv4_address
                    else:
                        link_state_id = self.ospf_identifier
                    network_lsa = self.lsdb.get_lsa(conf.LSA_TYPE_NETWORK, link_state_id, self.router_id, [self])
                    if network_lsa is not None:
                        self.flush_lsa(network_lsa)

            #  Intra-Area-Prefix LSA
            if ((self.router_id in [old_dr, new_dr]) | (self.ipv4_address in [old_dr, new_dr])) & (
                    old_dr != new_dr) & (self.version == conf.VERSION_IPV6):
                prefix_length = utils.Utils.get_ipv6_prefix_from_interface_name(self.physical_identifier)[1]
                prefix_options = conf.PREFIX_OPTIONS
                metric = self.cost
                prefix = utils.Utils.get_ipv6_prefix_from_interface_name(self.physical_identifier)[0]
                #  TODO: Correct?
                if old_dr in [self.router_id, self.ipv4_address]:
                    network_intra_area_prefix_lsa = copy.deepcopy(self.lsdb.get_lsa(
                        conf.LSA_TYPE_INTRA_AREA_PREFIX, self.ospf_identifier, self.router_id, [self]))
                    if network_intra_area_prefix_lsa is not None:
                        self.flush_lsa(network_intra_area_prefix_lsa)
                    router_intra_area_prefix_lsa = self.lsdb.get_lsa(
                        conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.DEFAULT_DESIGNATED_ROUTER, self.router_id, [self])
                    is_new = False
                    if router_intra_area_prefix_lsa is None:  # Router is not connected to other stub links
                        is_new = True
                        router_intra_area_prefix_lsa = self.create_lsa_header(
                            conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.LSA_TYPE_ROUTER, conf.INITIAL_SEQUENCE_NUMBER)
                        router_intra_area_prefix_lsa.create_intra_area_prefix_lsa_body(
                            conf.LSA_TYPE_ROUTER, conf.DEFAULT_DESIGNATED_ROUTER, self.router_id)
                    router_intra_area_prefix_lsa.add_prefix_info(
                        prefix_length, prefix_options, metric, prefix, conf.LSA_TYPE_INTRA_AREA_PREFIX)
                    if is_new:
                        self.install_flood_lsa(router_intra_area_prefix_lsa, self.router_id)
                    else:
                        self.generate_lsa_instance(router_intra_area_prefix_lsa, self.router_id)  # Also floods it

    #  Neighbor reached/left FULL state
    def event_neighbor_full_state(self, old_state, new_state, neighbor_id):
        #  Router-LSA
        if self.type == conf.POINT_TO_POINT_INTERFACE:
            if self.version == conf.VERSION_IPV4:
                router_lsa = copy.deepcopy(
                    self.lsdb.get_lsa(conf.LSA_TYPE_ROUTER, self.router_id, self.router_id, [self]))
                link_id = list(self.neighbors.values())[0].neighbor_id
                link_data = self.ipv4_address
                link_type = conf.POINT_TO_POINT_LINK
                tos_number = conf.DEFAULT_TOS
                metric = self.cost
                if new_state == conf.NEIGHBOR_STATE_FULL:
                    router_lsa.body.add_link_info_v2(link_id, link_data, link_type, tos_number, metric)
                    self.generate_lsa_instance(router_lsa, self.router_id)
                elif old_state == conf.NEIGHBOR_STATE_FULL:
                    router_lsa.body.delete_link_info_v2(link_id, link_data, link_type, tos_number, metric)
                    self.generate_lsa_instance(router_lsa, self.router_id)
            elif self.version == conf.VERSION_IPV6:
                router_lsa = copy.deepcopy(self.lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, self.router_id, [self]))
                link_type = conf.POINT_TO_POINT_LINK
                metric = self.cost
                interface_id = self.ospf_identifier
                neighbor_interface_id = self.neighbors[neighbor_id].neighbor_interface_id
                neighbor_router_id = self.neighbors[neighbor_id].neighbor_id
                if (old_state == conf.NEIGHBOR_STATE_FULL) & (old_state != new_state):
                    router_lsa.add_link_info_v3(
                        self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id)
                    self.generate_lsa_instance(router_lsa, self.router_id)
                elif (new_state == conf.NEIGHBOR_STATE_FULL) & (old_state != new_state):
                    router_lsa.delete_link_info_v3(
                        self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id)
                    self.generate_lsa_instance(router_lsa, self.router_id)
            else:
                raise ValueError("Invalid OSPF version")
        elif self.type == conf.BROADCAST_INTERFACE:
            if self.version == conf.VERSION_IPV4:
                self.event_network_dr_change(self.ipv4_address, self.ipv4_address)
            elif self.version == conf.VERSION_IPV6:
                self.event_network_dr_change(self.router_id, self.router_id)
            else:
                raise ValueError("Invalid OSPF version")

        #  Network-LSA
        if self.designated_router in [self.router_id, self.ipv4_address]:
            if self.version == conf.VERSION_IPV4:
                link_state_id = self.ipv4_address
            else:
                link_state_id = self.ospf_identifier
            network_lsa = copy.deepcopy(
                self.lsdb.get_lsa(conf.LSA_TYPE_NETWORK, link_state_id, self.router_id, [self]))
            if new_state == conf.NEIGHBOR_STATE_FULL:
                if network_lsa is not None:
                    network_lsa.body.add_attached_router(neighbor_id)
                    self.generate_lsa_instance(network_lsa, self.router_id)
                else:
                    network_lsa = self.create_network_lsa(conf.INITIAL_SEQUENCE_NUMBER)
                    self.install_flood_lsa(network_lsa, self.router_id)
            elif old_state == conf.NEIGHBOR_STATE_FULL:
                if self.is_transit_network(self.designated_router):
                    network_lsa.body.delete_attached_router(neighbor_id)
                    self.generate_lsa_instance(network_lsa, self.router_id)
                else:
                    self.flush_lsa(network_lsa)

        #  Intra-Area-Prefix-LSA
        if (self.designated_router in [self.router_id, neighbor_id]) & (self.version == conf.VERSION_IPV6):
            prefix_length = utils.Utils.get_ipv6_prefix_from_interface_name(self.physical_identifier)[1]
            prefix_options = conf.PREFIX_OPTIONS
            metric = self.cost
            prefix = utils.Utils.get_ipv6_prefix_from_interface_name(self.physical_identifier)[0]
            if new_state == conf.NEIGHBOR_STATE_FULL:
                if self.is_transit_network(self.designated_router):
                    router_intra_area_prefix_lsa = copy.deepcopy(self.lsdb.get_lsa(
                        conf.LSA_TYPE_INTRA_AREA_PREFIX, 0, self.router_id, [self]))  # Associated to stub networks
                    #  If first full adjacency has just been created and/or router is connected to stub networks
                    if router_intra_area_prefix_lsa is not None:
                        if len(router_intra_area_prefix_lsa.body.prefixes) == 1:  # This prefix
                            self.flush_lsa(router_intra_area_prefix_lsa)
                        else:
                            router_intra_area_prefix_lsa.delete_prefix_info(
                                prefix_length, prefix_options, metric, prefix, conf.LSA_TYPE_INTRA_AREA_PREFIX)
                            self.generate_lsa_instance(router_intra_area_prefix_lsa, self.router_id)
                        if self.designated_router == self.router_id:
                            network_intra_area_prefix_lsa = self.create_network_intra_area_prefix_lsa(
                                conf.INITIAL_SEQUENCE_NUMBER)
                            network_intra_area_prefix_lsa.add_prefix_info(
                                prefix_length, prefix_options, metric, prefix, conf.LSA_TYPE_INTRA_AREA_PREFIX)
                            self.install_flood_lsa(network_intra_area_prefix_lsa, self.router_id)
            elif (old_state == conf.NEIGHBOR_STATE_FULL) & (self.designated_router == self.router_id):
                if not self.is_transit_network(self.designated_router):  # Last full adjacency was destroyed
                    network_intra_area_prefix_lsa = copy.deepcopy(self.lsdb.get_lsa(
                        conf.LSA_TYPE_INTRA_AREA_PREFIX, self.ospf_identifier, self.router_id, [self]))
                    self.flush_lsa(network_intra_area_prefix_lsa)
                    router_intra_area_prefix_lsa = self.lsdb.get_lsa(
                        conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.DEFAULT_DESIGNATED_ROUTER, self.router_id, [self])
                    if router_intra_area_prefix_lsa is None:  # Router is not connected to other stub links
                        router_intra_area_prefix_lsa = self.create_lsa_header(
                            conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.LSA_TYPE_ROUTER, conf.INITIAL_SEQUENCE_NUMBER)
                        router_intra_area_prefix_lsa.create_intra_area_prefix_lsa_body(
                            conf.LSA_TYPE_ROUTER, conf.DEFAULT_DESIGNATED_ROUTER, self.router_id)
                    router_intra_area_prefix_lsa.add_prefix_info(
                        prefix_length, prefix_options, metric, prefix, conf.LSA_TYPE_INTRA_AREA_PREFIX)
                    self.install_flood_lsa(router_intra_area_prefix_lsa, self.router_id)

    #  New Link-LSA received
    def event_new_link_lsa_received(self):
        #  TODO: Implement case where prefix is installed in only 1 router in the link
        pass

    #  Given LSA instance generates new instance, installs it in LSDB and floods it
    def generate_lsa_instance(self, lsa_instance, neighbor_id):
        lsa_instance.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
            lsa_instance.header.ls_sequence_number)
        lsa_instance.header.ls_age = conf.INITIAL_LS_AGE
        lsa_instance.set_lsa_length()
        lsa_instance.set_lsa_checksum()
        self.install_flood_lsa(lsa_instance, neighbor_id)

    def install_flood_lsa(self, lsa_instance, neighbor_id):
        self.lsdb.add_lsa(lsa_instance, self)
        self.add_lsa_to_flooding_pipeline(lsa_instance, neighbor_id)  # neighbor_id can be this Router ID

    #  Flushes given LSA instance
    def flush_lsa(self, lsa_instance):
        if not lsa_instance.is_lsa_self_originated(self.router_id):
            warnings.warn("Router " + self.router_id + " flushing LSA originated at other router")
        lsa_instance.set_ls_age_max()
        self.lsdb.add_lsa(lsa_instance, self)  # Replace current instance with MaxAge instance
        lsa_identifier = lsa_instance.get_lsa_identifier()
        for neighbor_id in self.neighbors:
            neighbor_router = self.neighbors[neighbor_id]
            if lsa_identifier in neighbor_router.ls_retransmission_list:
                neighbor_router.delete_lsa_identifier(neighbor_router.ls_retransmission_list, lsa_identifier)
        self.add_lsa_to_flooding_pipeline(copy.deepcopy(lsa_instance), self.router_id)
        #  Shortcut to LSA removal from LSDB
        self.lsdb.delete_lsa(lsa_identifier[0], lsa_identifier[1], lsa_identifier[2], [self])

    #  Returns True if interface has at least one neighbor in FULL state (full adjacency)
    def has_full_adjacency(self):
        fully_adjacent = False
        for neighbor_id in self.neighbors:
            if self.neighbors[neighbor_id].neighbor_state == conf.NEIGHBOR_STATE_FULL:
                fully_adjacent = True
        return fully_adjacent

    #  Returns True if interface is, or will be, connected to transit network
    def is_transit_network(self, designated_router):  # Can be current or future Designated Router
        if designated_router in [self.router_id, self.ipv4_address]:
            return self.has_full_adjacency()
        else:
            dr_id = self.get_router_id_by_interface_ip(self.designated_router)
            return self.neighbors[dr_id].neighbor_state == conf.NEIGHBOR_STATE_FULL

    #  Adds LSA to flooding pipeline for router main loop to flood it if required
    def add_lsa_to_flooding_pipeline(self, received_lsa, neighbor_id):
        self.flooding_pipeline.put([received_lsa, neighbor_id])
        time.sleep(0.1)  # Gives CPU to router main loop thread

    #  Creates and returns the link Network-LSA if interface is DR
    def create_network_lsa(self, ls_sequence_number):
        network_lsa = self.create_lsa_header(conf.LSA_TYPE_NETWORK, 0, ls_sequence_number)
        if self.version == conf.VERSION_IPV4:
            network_mask = self.network_mask
        else:
            network_mask = ''
        attached_routers = [self.router_id]
        for neighbor_id in self.neighbors:
            if self.neighbors[neighbor_id].neighbor_state == conf.NEIGHBOR_STATE_FULL:
                attached_routers.append(neighbor_id)
        network_lsa.create_network_lsa_body(network_mask, conf.OPTIONS, attached_routers, self.version)
        return network_lsa

    #  Creates and returns the Link-LSA for this interface
    def create_link_lsa(self, ls_sequence_number):
        link_lsa = self.create_lsa_header(conf.LSA_TYPE_LINK, 0, ls_sequence_number)
        link_lsa.create_link_lsa_body(self.router_priority, conf.OPTIONS, self.ipv6_address)
        #  TODO: Consider the case where there are multiple link prefixes
        prefix_length = utils.Utils.get_ipv6_prefix_from_interface_name(self.physical_identifier)[1]
        prefix_options = conf.PREFIX_OPTIONS
        prefix = utils.Utils.get_ipv6_prefix_from_interface_name(self.physical_identifier)[0]
        link_lsa.add_prefix_info(prefix_length, prefix_options, 0, prefix, conf.LSA_TYPE_LINK)
        return link_lsa

    #  Creates and returns an Intra-Area-Prefix-LSA referencing a Network-LSA for this interface
    def create_network_intra_area_prefix_lsa(self, ls_sequence_number):
        intra_area_prefix_lsa = self.create_lsa_header(
            conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.LSA_TYPE_NETWORK, ls_sequence_number)
        intra_area_prefix_lsa.create_intra_area_prefix_lsa_body(
            conf.LSA_TYPE_NETWORK, self.ospf_identifier, self.router_id)
        for query_lsa in self.get_link_lsa_list():  # Assumes this router is DR
            neighbor_id = query_lsa.header.advertising_router
            if neighbor_id in self.neighbors:
                if (self.neighbors[neighbor_id].neighbor_state == conf.NEIGHBOR_STATE_FULL) & (
                        self.neighbors[neighbor_id].neighbor_interface_id == query_lsa.header.link_state_id):
                    for prefix_info in query_lsa.body.prefixes:
                        intra_area_prefix_lsa.add_prefix_info(prefix_info[0], prefix_info[1], self.cost, prefix_info[2],
                                                              conf.LSA_TYPE_INTRA_AREA_PREFIX)
        return intra_area_prefix_lsa

    #  Returns a LSA with header created and empty body
    def create_lsa_header(self, lsa_type, referenced_ls_type, ls_sequence_number):
        new_lsa = lsa.Lsa()
        link_state_id = ''
        if self.version == conf.VERSION_IPV4:
            if lsa_type == conf.LSA_TYPE_ROUTER:
                link_state_id = self.router_id
            elif lsa_type == conf.LSA_TYPE_NETWORK:
                link_state_id = self.ipv4_address
            new_lsa.create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, lsa_type, link_state_id, self.router_id,
                                  ls_sequence_number, self.version)
        elif self.version == conf.VERSION_IPV6:
            if lsa_type == conf.LSA_TYPE_ROUTER:
                link_state_id = 0
            elif lsa_type == conf.LSA_TYPE_NETWORK:
                link_state_id = self.ospf_identifier
            elif lsa_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
                if header.Header.get_ls_type(referenced_ls_type) == conf.LSA_TYPE_ROUTER:
                    link_state_id = '0.0.0.0'
                elif header.Header.get_ls_type(referenced_ls_type) == conf.LSA_TYPE_NETWORK:
                    link_state_id = self.ospf_identifier  # Can be a random value
                else:
                    raise ValueError("Invalid Referenced LS Type")
            elif lsa_type == conf.LSA_TYPE_LINK:
                link_state_id = self.ospf_identifier
            new_lsa.create_header(
                conf.INITIAL_LS_AGE, 0, lsa_type, link_state_id, self.router_id, ls_sequence_number, self.version)
        else:
            raise ValueError("Invalid OSPF version")
        return new_lsa

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

    #  Returns flooding IP address for LS Update and LS Acknowledgement packets
    def get_flooding_ip_address(self):
        if len(self.neighbors) == 0:
            return ''
        elif self.version == conf.VERSION_IPV4:
            all_ospf_ip = conf.ALL_OSPF_ROUTERS_IPV4
            all_dr_ip = conf.ALL_DR_IPV4
            point_point_neighbor_ip = list(self.neighbors.values())[0].neighbor_ip_address
        else:
            all_ospf_ip = conf.ALL_OSPF_ROUTERS_IPV6
            all_dr_ip = conf.ALL_DR_IPV6
            point_point_neighbor_ip = list(self.neighbors.values())[0].neighbor_ip_address
        if (self.type == conf.BROADCAST_INTERFACE) & (self.state in [
                conf.INTERFACE_STATE_DR, conf.INTERFACE_STATE_BACKUP]):
            return all_ospf_ip
        elif self.type == conf.BROADCAST_INTERFACE:
            return all_dr_ip
        else:  # Point-to-point interface
            return point_point_neighbor_ip

    #  Updates LS Retransmission list of required neighbors with provided flooded LSAs given flooding IP address
    def update_ls_retransmission_lists(self, lsa_identifiers, flooding_address):
        if flooding_address in [conf.ALL_DR_IPV4, conf.ALL_DR_IPV6]:
            for n in self.neighbors:
                if self.neighbors[n].neighbor_id in [self.designated_router, self.backup_designated_router]:
                    for lsa_identifier in lsa_identifiers:
                        self.neighbors[n].add_lsa_identifier(self.neighbors[n].ls_retransmission_list, lsa_identifier)
                    self.neighbors[n].start_retransmission_timer(neighbor.LS_UPDATE)
        elif flooding_address in [conf.ALL_OSPF_ROUTERS_IPV4, conf.ALL_OSPF_ROUTERS_IPV6]:
            for n in self.neighbors:
                for lsa_identifier in lsa_identifiers:
                    self.neighbors[n].add_lsa_identifier(self.neighbors[n].ls_retransmission_list, lsa_identifier)
                self.neighbors[n].start_retransmission_timer(neighbor.LS_UPDATE)
        else:  # LSA flooded to unicast IP address
            for n in self.neighbors:
                if self.neighbors[n].neighbor_ip_address == flooding_address:
                    for lsa_identifier in lsa_identifiers:
                        self.neighbors[n].add_lsa_identifier(self.neighbors[n].ls_retransmission_list, lsa_identifier)
                    self.neighbors[n].start_retransmission_timer(neighbor.LS_UPDATE)

    #  Changes neighbor state
    def set_neighbor_state(self, neighbor_router, new_state):
        old_state = neighbor_router.neighbor_state
        if new_state != old_state:
            old_state = neighbor_router.neighbor_state
            neighbor_router.set_neighbor_state(new_state)
            if conf.NEIGHBOR_STATE_FULL in [old_state, new_state]:
                self.event_neighbor_full_state(old_state, new_state, neighbor_router.neighbor_id)

    #  Given address, returns itself if router ID or corresponding router ID if respective interface IP address
    def get_router_id_by_interface_ip(self, ip_address):
        if (self.router_id == ip_address) | (self.ipv4_address == ip_address):
            return self.router_id
        for neighbor_id in self.neighbors:
            neighbor_router = self.neighbors[neighbor_id]
            if (neighbor_id == ip_address) | (neighbor_router.neighbor_ip_address == ip_address):
                return neighbor_id
        return '0.0.0.0'

    def get_ospf_multicast_destination_address(self):
        #  TODO: Use this method to decide between 224.0.0.5 and 224.0.0.6
        if self.version == conf.VERSION_IPV4:
            if self.is_dr_bdr():
                return conf.ALL_OSPF_ROUTERS_IPV4
            else:
                return conf.ALL_DR_IPV4
        elif self.version == conf.VERSION_IPV6:
            if self.is_dr_bdr():
                return conf.ALL_OSPF_ROUTERS_IPV6
            else:
                return conf.ALL_DR_IPV6
        else:
            raise ValueError("Invalid OSPF version")

    #  Returns True if this router is DR or BDR
    def is_dr_bdr(self):
        return (self.router_id in [self.designated_router, self.backup_designated_router]) | (
                self.ipv4_address in [self.designated_router, self.backup_designated_router])

    #  #  #  #  #  #  #  #  #  #  #  #
    #  Link-local LSA list methods  #
    #  #  #  #  #  #  #  #  #  #  #  #

    #  Atomically gets all link-local LSAs from interface
    def get_link_local_lsa_list(self):
        with self.lsa_lock:
            return self.link_local_lsa_list

    #  Atomically gets all Link-LSAs from interface
    def get_link_lsa_list(self):
        with self.lsa_lock:
            link_lsa_list = []
            for query_lsa in self.link_local_lsa_list:
                if query_lsa.get_lsa_type_from_lsa() == conf.LSA_TYPE_LINK:
                    link_lsa_list.append(query_lsa)
            return link_lsa_list

    #  Atomically gets a link-local LSA from interface
    def get_link_local_lsa(self, ls_type, link_state_id, advertising_router):
        if not utils.Utils.is_ipv4_address(link_state_id):
            link_state_id = utils.Utils.decimal_to_ipv4(link_state_id)
        with self.lsa_lock:
            for local_lsa in self.link_local_lsa_list:
                if local_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    return local_lsa
            return None

    #  Atomically deletes link-local LSA from interface
    def delete_link_local_lsa(self, ls_type, link_state_id, advertising_router):
        if not utils.Utils.is_ipv4_address(link_state_id):
            link_state_id = utils.Utils.decimal_to_ipv4(link_state_id)
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

            new_lsa.installation_time = time.perf_counter()
            self.link_local_lsa_list.append(new_lsa)
