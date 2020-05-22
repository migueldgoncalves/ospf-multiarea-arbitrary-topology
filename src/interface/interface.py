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

    DR = 'DR'
    BDR = 'BDR'

    def __init__(self, physical_identifier, ipv4_address, ipv6_address, network_mask, link_prefixes, area_id, pipeline,
                 interface_shutdown, version, lsdb):

        #  OSPF interface parameters

        self.type = conf.BROADCAST_INTERFACE  # TODO: Create point-to-point interface
        self.state = conf.INTERFACE_STATE_DOWN
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
        self.lsa_lock = threading.RLock()  # For controlling access to interface LSA list
        self.lsdb = lsdb  # Reference to the area LSDB

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
                            neighbor_dr, neighbor_bdr)
                        self.neighbors[neighbor_id] = new_neighbor

                    #  Existing neighbor
                    neighbor_data_changed = False
                    if neighbor_priority != self.neighbors[neighbor_id].neighbor_priority:  # Neighbor priority changed
                        neighbor_data_changed = True
                    self.neighbors[neighbor_id].neighbor_priority = neighbor_priority
                    #  Neighbor now declared itself as DR, or stops declaring itself as DR
                    if (neighbor_dr == neighbor_id) & (self.neighbors[neighbor_id].neighbor_dr != neighbor_id):
                        neighbor_data_changed = True
                    if (neighbor_dr != neighbor_id) & (self.neighbors[neighbor_id].neighbor_dr == neighbor_id):
                        neighbor_data_changed = True
                    self.neighbors[neighbor_id].neighbor_dr = neighbor_dr
                    #  Neighbor now declared itself as BDR, or stops declaring itself as BDR
                    if (neighbor_bdr == neighbor_id) & (self.neighbors[neighbor_id].neighbor_bdr != neighbor_id):
                        neighbor_data_changed = True
                    if (neighbor_bdr != neighbor_id) & (self.neighbors[neighbor_id].neighbor_bdr == neighbor_id):
                        neighbor_data_changed = True
                    self.neighbors[neighbor_id].neighbor_bdr = neighbor_bdr
                    if self.neighbors[neighbor_id] not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
                        if neighbor_data_changed:
                            self.event_neighbor_change()  # This router must reevaluate who is DR and BDR
                        elif (neighbor_id in [neighbor_dr, neighbor_bdr]) & (
                                self.state == conf.INTERFACE_STATE_WAITING):
                            self.event_backup_seen()

                    self.event_hello_received(incoming_packet, source_ip, neighbor_id)

                elif packet_type == conf.PACKET_TYPE_DB_DESCRIPTION:
                    neighbor_router = self.neighbors[neighbor_id]
                    neighbor_options = incoming_packet.body.options
                    neighbor_i_bit = incoming_packet.body.i_bit
                    neighbor_m_bit = incoming_packet.body.m_bit
                    neighbor_ms_bit = incoming_packet.body.ms_bit
                    neighbor_lsa_headers = incoming_packet.body.lsa_headers

                    if incoming_packet.body.interface_mtu > self.max_ip_datagram:
                        continue  # Neighbor MTU too large

                    if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_DOWN:
                        continue

                    elif neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_INIT:
                        self.event_2_way_received(neighbor_router, neighbor_id, source_ip)

                    elif neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_2_WAY:
                        continue

                    elif neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_EXSTART:
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
                                    self.event_negotiation_done(neighbor_router)
                                    self.update_ls_request_list(neighbor_router, incoming_packet)
                        else:
                            continue

                    elif neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_EXCHANGE:
                        #  Stores new LSA headers in the LS Request list of the neighbor
                        invalid_ls_type = self.update_ls_request_list(neighbor_router, incoming_packet)
                        if invalid_ls_type:  # At least one LSA with invalid type was detected
                            self.event_seq_number_mismatch(neighbor_router, source_ip)
                            continue
                        #  Removes acknowledged LSAs from DB Summary list
                        for header in incoming_packet.body.lsa_headers:
                            lsa_identifier = header.get_lsa_identifier()
                            neighbor_router.delete_lsa_identifier(neighbor_router.db_summary_list, lsa_identifier)
                        m_bit = (len(neighbor_router.db_summary_list) == 0)

                        if neighbor_router.master_slave:  # This router is the master
                            if incoming_packet.body.dd_sequence_number != neighbor_router.dd_sequence:
                                self.event_seq_number_mismatch(neighbor_router, source_ip)
                                continue
                            neighbor_router.dd_sequence += 1
                            #  This router and neighbor acknowledged that they have no more LSA headers to send
                            if (not incoming_packet.body.m_bit) & (not self.dd_packet.body.m_bit):
                                self.event_exchange_done(neighbor_router)
                            else:
                                #  Sends DB Description packet with either M-bit clear or more LSA headers
                                self.dd_packet.create_db_description_packet_body(
                                    self.max_ip_datagram, conf.OPTIONS, False, m_bit, True, neighbor_router.dd_sequence,
                                    self.lsdb.get_lsa_headers([self], neighbor_router.db_summary_list), self.version)
                                self.send_packet(self.dd_packet, neighbor_router.neighbor_ip_address)
                            #  TODO: Implement case where LSA headers are sent in more than 1 DB Description packet
                        else:  # This router is the slave
                            if incoming_packet.body.dd_sequence_number != (neighbor_router.dd_sequence + 1):
                                self.event_seq_number_mismatch(neighbor_router, source_ip)
                                continue
                            neighbor_router.dd_sequence = incoming_packet.body.dd_sequence_number
                            #  Sends DB Description packet as response to master
                            self.dd_packet.create_db_description_packet_body(
                                self.max_ip_datagram, conf.OPTIONS, False, m_bit, False, neighbor_router.dd_sequence,
                                self.lsdb.get_lsa_headers([self], neighbor_router.db_summary_list), self.version)
                            self.send_packet(self.dd_packet, neighbor_router.neighbor_ip_address)
                            if (not m_bit) & (not incoming_packet.body.m_bit):
                                self.event_exchange_done(neighbor_router)

                    elif neighbor_router.neighbor_state in [conf.NEIGHBOR_STATE_LOADING, conf.NEIGHBOR_STATE_FULL]:
                        #  TODO: Implement reception of duplicate packets both as master and as slave
                        self.event_seq_number_mismatch(neighbor_router, source_ip)

                    else:
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
            if self.hello_timeout.is_set():
                self.create_hello_packet()
                if self.version == conf.VERSION_IPV4:
                    self.send_packet(self.hello_packet_to_send, conf.ALL_OSPF_ROUTERS_IPV4)
                else:
                    self.send_packet(self.hello_packet_to_send, conf.ALL_OSPF_ROUTERS_IPV6)
                self.hello_timeout.clear()

        #  Interface signalled to shutdown
        self.event_interface_down()

    #  Sends an OSPF packet through the interface
    def send_packet(self, packet_to_send, destination_address):
        packet_bytes = packet_to_send.pack_packet()
        if self.version == conf.VERSION_IPV4:
            self.socket.send_ipv4(packet_bytes, destination_address, self.physical_identifier)
        else:
            self.socket.send_ipv6(packet_bytes, destination_address, self.physical_identifier)

    #  Performs shutdown operations on the interface
    def shutdown_interface(self):
        for n in list(self.neighbors):  # Stops timer thread in all neighbors
            self.event_kill_nbr(n)
        self.hello_timer_shutdown.set()
        self.waiting_timer_shutdown.set()
        self.hello_thread.join()
        self.waiting_thread.join()
        #  Reset interface values
        self.__init__(self.physical_identifier, self.ipv4_address, self.ipv6_address, self.network_mask,
                      self.link_prefixes, self.area_id, self.pipeline, self.interface_shutdown, self.version, self.lsdb)

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

    #  TODO: Implement loopback events?

    #  InterfaceDown event
    def event_interface_down(self):
        self.shutdown_interface()

    #  Full election algorithm
    def election_algorithm(self):
        known_routers = self.election_algorithm_step_1()
        determined_bdr = self.election_algorithm_step_2(known_routers)
        determined_dr = self.election_algorithm_step_3(known_routers, determined_bdr)
        rerun_algorithm = self.election_algorithm_step_4(determined_dr, determined_bdr, True)
        if rerun_algorithm:
            self.set_dr_bdr(Interface.BDR, determined_bdr)
            self.set_dr_bdr(Interface.DR, determined_dr)
            determined_bdr = self.election_algorithm_step_2(known_routers)
            determined_dr = self.election_algorithm_step_3(known_routers, determined_bdr)
        self.election_algorithm_step_5(determined_dr, determined_bdr)
        self.election_algorithm_step_6(determined_dr, determined_bdr)
        self.set_dr_bdr(Interface.BDR, determined_bdr)
        self.set_dr_bdr(Interface.DR, determined_dr)

    #  Election algorithm - Step 1
    def election_algorithm_step_1(self):
        known_routers = [[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.designated_router, self.backup_designated_router]]
        for neighbor_id in self.neighbors:
            if self.neighbors[neighbor_id] not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
                neighbor_structure = self.neighbors[neighbor_id]
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
        #  Steps 2 and 3 can only be rerun eventually if it is the algorithm first run
        if first_run:
            #  This router has become DR or BDR
            if (conf.ROUTER_ID not in [self.designated_router, self.backup_designated_router]) & (
                    conf.ROUTER_ID in [determined_dr, determined_bdr]):
                return True
            #  This router is no longer the DR
            elif (conf.ROUTER_ID == self.designated_router) & (conf.ROUTER_ID != determined_dr):
                return True
            #  This router is no longer the BDR
            elif (conf.ROUTER_ID == self.backup_designated_router) & (conf.ROUTER_ID != determined_bdr):
                return True
        return False  # This router maintains its status - Step 5 will be run next

    #  Election algorithm - Step 5
    def election_algorithm_step_5(self, determined_dr, determined_bdr):
        if conf.ROUTER_ID == determined_dr:
            self.set_interface_state(conf.INTERFACE_STATE_DR)  # Nothing is done if state is already the desired one
        elif conf.ROUTER_ID == determined_bdr:
            self.set_interface_state(conf.INTERFACE_STATE_BACKUP)
        else:
            self.set_interface_state(conf.INTERFACE_STATE_DROTHER)

    #  Election algorithm - Step 6
    def election_algorithm_step_6(self, determined_dr, determined_bdr):
        #  Either DR or BDR have changed
        if (self.designated_router != determined_dr) | (self.backup_designated_router != determined_bdr):
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
            print("OSPFv" + str(self.version), "interface", self.physical_identifier,
                  "changed state from", old_state, "to", new_state)
            self.state = new_state

    #  Changes DR or BDR value and prints a message
    def set_dr_bdr(self, value_name, new_value):
        if (value_name == Interface.DR) & (new_value != self.designated_router):
            print("OSPFv" + str(self.version), value_name, "changed from", self.designated_router, "to", new_value)
            self.designated_router = new_value
        elif (value_name == Interface.BDR) & (new_value != self.backup_designated_router):
            print(
                "OSPFv" + str(self.version), value_name, "changed from", self.backup_designated_router, "to", new_value)
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
            neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_INIT)
        if conf.ROUTER_ID in incoming_packet.body.neighbors:
            #  Neighbor acknowledges this router as neighbor
            self.event_2_way_received(neighbor_router, neighbor_id, source_ip)
        else:
            self.event_1_way_received(neighbor_router)  # Neighbor does not, even if it did in the last Hello packets

    #  2-WayReceived event
    def event_2_way_received(self, neighbor_router, neighbor_id, source_ip):
        if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_INIT:
            self.event_neighbor_change()
            #  Neither this router nor neighbor are DR/BDR
            if not self.should_be_fully_adjacent(neighbor_id):
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
    @staticmethod
    def event_loading_done(neighbor_router):
        neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)

    #  AdjOK? event
    def event_adj_ok(self, neighbor_router, neighbor_id, source_ip):
        if neighbor_router.neighbor_state == conf.NEIGHBOR_STATE_2_WAY:
            if self.should_be_fully_adjacent(neighbor_router.neighbor_id):
                neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_INIT)
                self.event_2_way_received(neighbor_router, neighbor_id, source_ip)
            else:
                pass  # Neighbor remains at state 2-WAY
        elif neighbor_router.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT]:
            if self.should_be_fully_adjacent(neighbor_router.neighbor_id):
                pass  # Neighbor remains at state Exchange or higher
            else:
                neighbor_router.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
                neighbor_router.ls_retransmission_list = []
                neighbor_router.db_summary_list = []
                neighbor_router.ls_request_list = []

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
            self.neighbors[neighbor_id].delete_neighbor()  # Stops neighbor timer threads
            self.neighbors.pop(neighbor_id)
            self.event_neighbor_change()  # A neighbor has left the link - DR election algorithm must be run

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
            self.event_neighbor_change()
        else:
            pass

    #  Given a DB Description packet, stores its LSA headers in the respective neighbor LS Request list if needed
    def update_ls_request_list(self, neighbor_router, incoming_packet):
        #  TODO: Check if this verification is in the right place
        neighbor_router.stop_retransmission_timer()
        #  TODO: Implement resending if incoming packet is duplicate
        invalid_ls_type = False
        for header in incoming_packet.body.lsa_headers:
            #  TODO: Consider other types of LSAs
            if ((self.version == conf.VERSION_IPV4) & (header.get_ls_type(header.ls_type) not in [
                conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK])) | ((self.version == conf.VERSION_IPV6) & (
                    header.get_ls_type(header.ls_type) not in [
                    conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK, conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.LSA_TYPE_LINK])):
                invalid_ls_type = True
            else:  # LSA with valid type
                local_lsa = self.lsdb.get_lsa(header.ls_type, header.link_state_id,
                                              header.advertising_router, [self])
                #  TODO: Implement LSA instance comparison
                if local_lsa is None:  # This router does not have the LSA
                    neighbor_router.add_lsa_identifier(
                        neighbor_router.ls_request_list, header.get_lsa_identifier())
        return invalid_ls_type

    #  Given a neighbor RID, returns True if this router and the neighbor should become fully adjacent
    def should_be_fully_adjacent(self, neighbor_id):
        if self.type == conf.POINT_TO_POINT_INTERFACE:
            return True
        if conf.ROUTER_ID in [self.designated_router, self.backup_designated_router]:  # This router is DR/BDR
            return True
        if neighbor_id in [self.designated_router, self.backup_designated_router]:  # Neighbor is DR/BDR
            return True
        return False

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
