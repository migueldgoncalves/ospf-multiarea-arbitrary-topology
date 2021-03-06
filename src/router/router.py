import threading
import datetime
import time
import copy
import random
import multiprocessing

import general.utils as utils
import general.sock as sock
import conf.conf as conf
import area.area as area
import packet.packet as packet
import lsa.lsa as lsa
import lsa.header as header
import router.routing_table as routing_table
import router.kernel_table as kernel_table
import router.extension_lsdb as extension_lsdb

'''
This class contains the top-level OSPF data structures and operations
'''

SHOW = 1
SHOW_INTERFACE = 2
SHOW_NEIGHBOR = 3
SHOW_LSDB = 4
SHOW_DATABASE_SUMMARY = 5
SHOW_CONVERGENCE = 6
SHUTDOWN_INTERFACE = 7
START_INTERFACE = 8


class Router:

    def __init__(self):
        self.ospf_version = 0

        #  Localhost operation parameters - Only for test purposes

        self.localhost = False
        self.interface_ids = []
        self.area_ids = []

        #  OSPF top-level parameters

        self.router_id = ''
        self.areas = {}
        self.interfaces = {}
        self.max_ip_datagram = 0
        self.routing_table = routing_table.RoutingTable()

        #  Implementation-specific parameters

        self.packet_sockets = {}
        self.packet_pipelines = {}
        self.socket_shutdown_events = {}
        self.socket_processes = {}
        self.router_shutdown_event = None
        self.start_time = datetime.datetime.now()
        self.abr = False
        self.command_pipeline = None
        self.output_event = None
        self.command_thread = threading.Thread(target=self.execute_commands)
        self.kernel_table_thread = None  # Handles LSDB changes
        self.kernel_table_process = None  # Created by previous thread, adds routes to kernel routing table
        self.kernel_thread_operating = threading.Event()
        self.extension_database = None

    #  Allows router instance to be created without starting it
    def set_up(self, router_id, ospf_version, router_shutdown_event, interface_ids, area_ids, localhost,
               command_pipeline, output_event, interface_costs):
        if ospf_version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
            raise ValueError("Invalid OSPF version")
        self.ospf_version = ospf_version

        self.localhost = localhost  # If router is operating on localhost or not - If False router operates normally
        self.interface_ids = interface_ids  # Interfaces in this machine
        self.area_ids = area_ids  # OSPF areas of the interfaces

        self.router_id = router_id
        external_routing_capable = False
        for area_id in Router.get_unique_values(self.area_ids):
            area_interfaces = []
            area_interface_costs = []
            for i in range(len(self.interface_ids)):
                if area_ids[i] == area_id:
                    area_interfaces.append(self.interface_ids[i])
                    area_interface_costs.append(interface_costs[i])
            new_area = area.Area(
                self.router_id, self.ospf_version, area_id, external_routing_capable, area_interfaces, self.localhost,
                Router.is_abr(area_ids), area_interface_costs)
            self.areas[area_id] = new_area
        for area_id in Router.get_unique_values(self.area_ids):
            for interface_id in self.areas[area_id].interfaces:
                self.interfaces[interface_id] = self.areas[area_id].interfaces[interface_id]
        self.max_ip_datagram = conf.MTU

        for interface_id in self.interfaces:
            self.packet_sockets[interface_id] = sock.Socket()
            self.packet_pipelines[interface_id] = multiprocessing.Queue()
        for interface_id in self.interfaces:
            self.socket_shutdown_events[interface_id] = multiprocessing.Event()
        accept_self_packets = False
        is_dr = multiprocessing.Event()  # Event is clear on creation - Router on startup is never DR/BDR
        for interface_id in self.interfaces:
            if self.ospf_version == conf.VERSION_IPV4:
                self.socket_processes[interface_id] = multiprocessing.Process(
                    target=self.packet_sockets[interface_id].receive_ipv4,
                    args=(self.packet_pipelines[interface_id], self.socket_shutdown_events[interface_id], interface_id,
                          accept_self_packets, is_dr, localhost))
            else:
                self.socket_processes[interface_id] = multiprocessing.Process(
                    target=self.packet_sockets[interface_id].receive_ipv6,
                    args=(self.packet_pipelines[interface_id], self.socket_shutdown_events[interface_id], interface_id,
                          accept_self_packets, is_dr, localhost))
            self.socket_processes[interface_id].start()
        self.router_shutdown_event = router_shutdown_event
        self.abr = Router.is_abr(area_ids)
        self.command_pipeline = command_pipeline  # User commands
        self.output_event = output_event  # If has printed desired output, if any
        self.command_thread.start()
        self.extension_database = extension_lsdb.ExtensionLsdb(self.ospf_version)
        for interface_id in self.interfaces:  # Remains None at interface if it is being run as part of unit test
            self.interfaces[interface_id][area.INTERFACE_OBJECT].extension_lsdb = self.extension_database

        self.main_loop()

    #  #  #  #  #  #
    #  Main method  #
    #  #  #  #  #  #

    #  OSPF router main loop
    def main_loop(self):
        while not self.router_shutdown_event.is_set():  # Until router is signalled to shutdown
            #  Sends received packets to receiving interface
            for interface_id in self.packet_pipelines:
                pipeline = self.packet_pipelines[interface_id]
                if not pipeline.empty():
                    packet_data = pipeline.get()
                    packet_bytes = packet_data[0]
                    source_ip = packet_data[1]
                    received_packet = packet.Packet.unpack_packet(packet_bytes)
                    interface_pipeline = self.interfaces[interface_id][area.PIPELINE]
                    interface_pipeline.put([received_packet, source_ip])

            #  Remove extension LSAs with MaxAge
            lsa_list = self.extension_database.get_extension_lsdb(None)
            for query_lsa in lsa_list:
                lsa_identifier = query_lsa.get_lsa_identifier()
                if query_lsa.header.ls_age >= conf.MAX_AGE:
                    self.extension_database.delete_extension_lsa(
                        lsa_identifier[0], lsa_identifier[1], lsa_identifier[2])

            #  For each LSA, increases LS Age field if enough time has passed
            for a in self.areas:
                area_interfaces = self.areas[a].get_interfaces()
                self.areas[a].database.increase_lsa_age(area_interfaces)
            self.extension_database.increase_lsa_age()

            #  Searches for LSAs to flood and floods them through the proper interfaces
            for a in self.areas:
                current_area = self.areas[a]
                for i in current_area.interfaces:
                    current_interface = current_area.interfaces[i][area.INTERFACE_OBJECT]
                    if not current_interface.flooding_pipeline.empty():  # Interface has LSA to flood
                        data = current_interface.flooding_pipeline.get()
                        lsa_instance = data[0]
                        lsa_identifier = lsa_instance.get_lsa_identifier()
                        sending_neighbor_id = data[1]  # Can be this router ID
                        ls_type = lsa_instance.get_lsa_type_from_lsa()

                        eligible_interfaces = []
                        #  Obtains the eligible interfaces for flooding the LSA
                        if self.ospf_version == conf.VERSION_IPV4:
                            if ls_type in [conf.LSA_TYPE_AS_EXTERNAL, conf.LSA_TYPE_OPAQUE_AS]:  # AS-flooding scope
                                #  All router interfaces
                                for j in self.interfaces:
                                    eligible_interfaces.append(self.interfaces[j][area.INTERFACE_OBJECT])
                            else:  # Area or link-flooding scope
                                #  All area interfaces
                                for j in current_area.interfaces:
                                    eligible_interfaces.append(current_area.interfaces[j][area.INTERFACE_OBJECT])
                        elif self.ospf_version == conf.VERSION_IPV6:
                            flooding_scope = header.Header.get_s1_s2_bits(lsa_instance.header.ls_type)
                            u_bit = header.Header.get_u_bit(lsa_instance.header.ls_type)
                            if lsa.Lsa.is_ls_type_valid(ls_type, self.ospf_version) | (u_bit == 1):
                                if flooding_scope == conf.AS_SCOPING:
                                    for j in self.interfaces:
                                        eligible_interfaces.append(self.interfaces[j][area.INTERFACE_OBJECT])
                                elif flooding_scope == conf.AREA_SCOPING:
                                    for j in current_area.interfaces:
                                        eligible_interfaces.append(current_area.interfaces[j][area.INTERFACE_OBJECT])
                                elif flooding_scope == conf.LINK_LOCAL_SCOPING:
                                    eligible_interfaces.append(current_interface)
                                else:
                                    current_interface.flooded_pipeline.put(False)
                                    time.sleep(0.1)  # Give CPU to other threads
                                    continue  # Invalid flooding scope
                            else:  # LSA with unknown LS Type and U-bit set to False has link-local flooding scope
                                eligible_interfaces.append(current_interface)

                        for j in eligible_interfaces:
                            should_retransmit_lsa = False
                            for n in j.neighbors:
                                neighbor = j.neighbors[n]
                                if neighbor.neighbor_state not in [
                                    conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING,
                                        conf.NEIGHBOR_STATE_FULL]:
                                    continue  # Neighbor does not take part in flooding
                                elif neighbor.neighbor_state in [
                                        conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING]:
                                    if lsa_identifier in neighbor.ls_request_list:  # Router sought this LSA
                                        #  Can be None
                                        local_copy = j.lsdb.get_lsa(lsa_identifier[0], lsa_identifier[1],
                                                                    lsa_identifier[2], eligible_interfaces)
                                        if lsa.Lsa.get_fresher_lsa(lsa_instance, local_copy) == header.SECOND:
                                            continue  # Examine next neighbor
                                        elif lsa.Lsa.get_fresher_lsa(lsa_instance, local_copy) == header.BOTH:
                                            neighbor.delete_lsa_identifier(neighbor.ls_request_list, lsa_identifier)
                                            continue
                                        else:  # Sought LSA has been received
                                            neighbor.delete_lsa_identifier(neighbor.ls_request_list, lsa_identifier)
                                if sending_neighbor_id == n:  # This neighbor sent the received LSA
                                    continue
                                neighbor.add_lsa_identifier(neighbor.ls_retransmission_list, lsa_identifier)
                                should_retransmit_lsa = True

                            if not should_retransmit_lsa:
                                current_interface.flooded_pipeline.put(False)
                                time.sleep(0.1)
                                continue  # LSA will not be flooded

                            #  Flood the LSA through the interface
                            lsa_instance.increase_lsa_age()  # Increases LS Age by 1 s
                            destination_address = j.get_flooding_ip_address()
                            ls_update_packet = packet.Packet()
                            if self.ospf_version == conf.VERSION_IPV4:
                                ls_update_packet.create_header_v2(conf.PACKET_TYPE_LS_UPDATE, self.router_id, j.area_id,
                                                                  conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
                            else:
                                ls_update_packet.create_header_v3(
                                    conf.PACKET_TYPE_LS_UPDATE, self.router_id, j.area_id,
                                    current_interface.instance_id, current_interface.ipv6_address, destination_address)
                            ls_update_packet.create_ls_update_packet_body(self.ospf_version)
                            ls_update_packet.add_lsa(lsa_instance)
                            j.send_packet(ls_update_packet, destination_address, None)
                            current_interface.flooded_pipeline.put(True)
                            time.sleep(0.1)

            #  Sets Linux kernel default routing table if LSDB was changed, no thread is running, enough time passed,
            #  and all neighbors are stable
            #  Updates and floods changes to inter-area and extension LSAs
            if (not self.kernel_thread_operating.is_set()) & self.are_neighbors_stable():
                lsdb_modified = False
                for area_id in self.areas:
                    query_area = self.areas[area_id]
                    area_lsdb = query_area.database
                    if area_lsdb.is_modified.is_set():  # LSDB was modified
                        if time.perf_counter() - area_lsdb.get_modification_time() > conf.KERNEL_UPDATE_INTERVAL:
                            area_lsdb.is_modified.clear()  # Database can be modified again while copy is processed
                            area_lsdb.reset_modification_time()
                            lsdb_modified = True
                if self.extension_database.is_modified.is_set() | lsdb_modified:
                    self.extension_database.is_modified.clear()
                    self.extension_database.reset_modification_time()
                    self.create_kernel_table_thread(lsdb_modified)

            #  Tells receiving socket whether respective interface is DR/BDR or not, if state changed
            for interface_id in self.interfaces:
                interface_is_dr_bdr = self.interfaces[interface_id][area.INTERFACE_OBJECT].is_dr_bdr()
                socket_is_dr_flag = self.packet_sockets[interface_id].is_dr
                if interface_is_dr_bdr != socket_is_dr_flag.is_set():
                    if interface_is_dr_bdr:
                        socket_is_dr_flag.set()
                    else:
                        socket_is_dr_flag.clear()

        #  Router signalled to shutdown
        self.shutdown_router()

    #  #  #  #  #  #  #  #  #  #  #  #  #  #  #
    #  LSDB update and routing table creation  #
    #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

    #  Returns OSPF routing table with paths to intra-area prefixes
    #  Receives shortest path trees of directly connected areas, and prefixes and LSDBs of such areas
    def get_intra_area_ospf_routing_table(self, shortest_path_tree_dictionary, prefixes_dictionary, lsdb_dict):
        intra_area_table = routing_table.RoutingTable()
        for area_id in lsdb_dict:
            #  Initialization

            query_area = self.areas[area_id]
            area_lsdb = lsdb_dict[area_id]  # Cache
            shortest_path_tree = shortest_path_tree_dictionary[area_id]
            prefixes = prefixes_dictionary[area_id]
            for node_id in copy.deepcopy(prefixes):
                if node_id not in shortest_path_tree:  # Deleting prefixes associated with unreachable nodes
                    prefixes.pop(node_id)
            interface_array = []
            for interface_id in query_area.interfaces:
                interface_array.append(query_area.interfaces[interface_id][area.INTERFACE_OBJECT])
            prefixes_with_costs = {}
            for node_id in prefixes:
                prefixes_with_costs[node_id] = {}
            next_hop_info = {}

            #  Associating prefixes with nodes and costs

            for node_id in prefixes:
                for prefix in prefixes[node_id]:
                    if self.ospf_version == conf.VERSION_IPV4:
                        node_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, node_id, node_id, [])
                        if node_lsa is not None:  # Router node
                            for link_info in node_lsa.body.links:
                                if (link_info[2] == conf.LINK_TO_STUB_NETWORK) & (link_info[0] == prefix):
                                    prefix_length = utils.Utils.prefix_to_prefix_length(link_info[1])
                                    options = node_lsa.header.options
                                    intra_area_table.add_entry(
                                        conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, area_id)
                                    #  Root to router + router to prefix
                                    cost = shortest_path_tree[node_id][0] + link_info[4]
                                    prefixes_with_costs[node_id][prefix] = [cost]
                        else:  # Transit network node
                            for network_lsa in area_lsdb.network_lsa_list:
                                if network_lsa.header.link_state_id == node_id:
                                    prefix_length = utils.Utils.prefix_to_prefix_length(
                                        network_lsa.body.network_mask)
                                    options = network_lsa.header.options
                                    intra_area_table.add_entry(
                                        conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, area_id)
                                    cost = shortest_path_tree[node_id][0]  # Root to network
                                    prefixes_with_costs[node_id][prefix] = [cost]
                    elif self.ospf_version == conf.VERSION_IPV6:
                        node_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, node_id, [])
                        if node_lsa is not None:  # Router node
                            options = node_lsa.body.options
                            intra_area_prefix_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_INTRA_AREA_PREFIX, 0, node_id, [])
                            for prefix_info in intra_area_prefix_lsa.body.prefixes:
                                if prefix_info[3] == prefix:
                                    prefix_length = prefix_info[0]
                                    intra_area_table.add_entry(
                                        conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, area_id)
                                    #  Root to router + router to prefix
                                    cost = shortest_path_tree[node_id][0] + prefix_info[2]
                                    prefixes_with_costs[node_id][prefix] = [cost]
                        else:  # Transit network node
                            router_id = node_id.split("|")[0]
                            interface_id = node_id.split("|")[1]
                            network_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_NETWORK, interface_id, router_id, [])
                            options = network_lsa.body.options
                            intra_area_prefix_lsa = None
                            for query_lsa in area_lsdb.intra_area_prefix_lsa_list:
                                if (query_lsa.header.advertising_router == router_id) & (
                                        query_lsa.body.referenced_link_state_id == utils.Utils.decimal_to_ipv4(
                                        interface_id)):
                                    intra_area_prefix_lsa = query_lsa
                            for prefix_info in intra_area_prefix_lsa.body.prefixes:
                                if prefix_info[3] == prefix:
                                    prefix_length = prefix_info[0]
                                    intra_area_table.add_entry(
                                        conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, area_id)
                                    cost = shortest_path_tree[node_id][0]  # Root to network
                                    prefixes_with_costs[node_id][prefix] = [cost]
                    else:
                        raise ValueError("Invalid OSPF version")

            #  Finding the next hop information to reach nodes in the same links as the root node

            root_id = ''
            for node_id in shortest_path_tree:
                if shortest_path_tree[node_id][1] == node_id:  # Only root node has itself as parent node
                    root_id = node_id
            for node_id in shortest_path_tree:
                if (shortest_path_tree[node_id][1] == root_id) & (node_id != root_id):  # Node with root as parent node
                    if self.ospf_version == conf.VERSION_IPV4:
                        node_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, node_id, node_id, [])
                        if node_lsa is not None:  # Node is a router - Root is connected through point-to-point link
                            root_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, root_id, root_id, [])
                            for link_info in root_lsa.body.links:
                                if link_info[0] == node_id:
                                    outgoing_interface_ip = link_info[1]
                                    for query_interface in interface_array:
                                        if outgoing_interface_ip == query_interface.ipv4_address:
                                            outgoing_interface = query_interface.physical_identifier
                                            next_hop_address = ''
                                            next_hop_info[node_id] = [outgoing_interface, next_hop_address]
                        else:  # Node is a transit network directly connected to root
                            for network_lsa in area_lsdb.network_lsa_list:
                                if node_id == network_lsa.header.link_state_id:
                                    network_prefix = utils.Utils.ip_address_to_prefix(
                                        network_lsa.header.link_state_id, network_lsa.body.network_mask)
                                    for query_interface in interface_array:
                                        interface_prefix = utils.Utils.ip_address_to_prefix(
                                            query_interface.ipv4_address, query_interface.network_mask)
                                        if network_prefix == interface_prefix:
                                            outgoing_interface = query_interface.physical_identifier
                                            next_hop_address = ''
                                            next_hop_info[node_id] = [outgoing_interface, next_hop_address]
                                            #  Routers in the shortest path tree having this network as parent node
                                            for destination in shortest_path_tree:
                                                if shortest_path_tree[destination][1] == node_id:
                                                    destination_lsa = area_lsdb.get_lsa(
                                                        conf.LSA_TYPE_ROUTER, destination, destination, [])
                                                    for link_info in destination_lsa.body.links:
                                                        if link_info[0] == node_id:
                                                            next_hop_address = link_info[1]
                                                            next_hop_info[destination] = [
                                                                outgoing_interface, next_hop_address]
                    else:
                        node_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, node_id, [])
                        root_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, root_id, [])
                        if node_lsa is not None:  # Node is a router - Root is connected through point-to-point link
                            for link_info in root_lsa.body.links:
                                if link_info[4] == node_id:
                                    outgoing_interface_id = link_info[2]
                                    for query_interface in interface_array:
                                        if outgoing_interface_id == query_interface.ospf_identifier:
                                            outgoing_interface = query_interface.physical_identifier
                                            next_hop_address = ''
                                            next_hop_info[node_id] = [outgoing_interface, next_hop_address]
                        else:  # Node is a transit network directly connected to root
                            dr_id = node_id.split("|")[0]
                            dr_interface_id = int(node_id.split("|")[1])
                            for link_info in root_lsa.body.links:
                                if (link_info[4] == dr_id) & (link_info[3] == dr_interface_id):
                                    outgoing_interface_id = link_info[2]
                                    for query_interface in interface_array:
                                        if outgoing_interface_id == query_interface.ospf_identifier:
                                            outgoing_interface = query_interface.physical_identifier
                                            next_hop_address = ''
                                            next_hop_info[node_id] = [outgoing_interface, next_hop_address]
                                            #  Routers in the shortest path tree having this network as parent node
                                            for destination in shortest_path_tree:
                                                if shortest_path_tree[destination][1] == node_id:
                                                    destination_lsa = area_lsdb.get_lsa(
                                                        conf.LSA_TYPE_ROUTER, 0, destination, [])
                                                    for destination_link_info in destination_lsa.body.links:
                                                        if (destination_link_info[3] == dr_interface_id) & (
                                                                destination_link_info[4] == dr_id):
                                                            destination_interface_id = destination_link_info[2]
                                                            destination_lsa = area_lsdb.get_lsa(
                                                                conf.LSA_TYPE_LINK, destination_interface_id,
                                                                destination, interface_array)
                                                            next_hop_address = destination_lsa.body.link_local_address
                                                            next_hop_info[destination] = [
                                                                outgoing_interface, next_hop_address]

            #  Finding the next hop information to reach the remaining nodes

            for node_id in shortest_path_tree:
                if (node_id not in next_hop_info) & (node_id != root_id):
                    parent_node = shortest_path_tree[node_id][1]
                    while True:
                        if self.router_shutdown_event.is_set():  # Shutdown
                            return
                        if parent_node in next_hop_info:
                            next_hop_info[node_id] = next_hop_info[parent_node]
                            break
                        parent_node = shortest_path_tree[parent_node][1]

            #  Associating prefixes with next hop information

            for node_id in prefixes_with_costs:
                if node_id == root_id:  # Prefixes in stub and point-to-point links connected to root router
                    for prefix in prefixes_with_costs[root_id]:
                        for query_interface in interface_array:
                            if self.ospf_version == conf.VERSION_IPV4:
                                if prefix == utils.Utils.ip_address_to_prefix(
                                        query_interface.ipv4_address, query_interface.network_mask):
                                    outgoing_interface = query_interface.physical_identifier
                                    next_hop_address = ''
                                    prefixes_with_costs[node_id][prefix].append(outgoing_interface)
                                    prefixes_with_costs[node_id][prefix].append(next_hop_address)
                            else:
                                for prefix_info in query_interface.link_prefixes:  # Includes prefix and prefix length
                                    if prefix_info[0] == prefix:
                                        outgoing_interface = query_interface.physical_identifier
                                        next_hop_address = ''
                                        prefixes_with_costs[node_id][prefix].append(outgoing_interface)
                                        prefixes_with_costs[node_id][prefix].append(next_hop_address)
                else:
                    for prefix in prefixes_with_costs[node_id]:
                        outgoing_interface = next_hop_info[node_id][0]
                        next_hop_address = next_hop_info[node_id][1]
                        prefixes_with_costs[node_id][prefix].append(outgoing_interface)
                        prefixes_with_costs[node_id][prefix].append(next_hop_address)

            #  Creating the routing table

            for node_id in prefixes_with_costs:
                for prefix in prefixes_with_costs[node_id]:
                    cost = prefixes_with_costs[node_id][prefix][0]
                    outgoing_interface = prefixes_with_costs[node_id][prefix][1]
                    next_hop_address = prefixes_with_costs[node_id][prefix][2]
                    routing_table_entry = intra_area_table.get_entry(conf.DESTINATION_TYPE_NETWORK, prefix, area_id)
                    if len(routing_table_entry.paths) > 0:
                        if cost < routing_table_entry.paths[0].cost:
                            routing_table_entry.delete_all_paths()
                        elif cost > routing_table_entry.paths[0].cost:
                            continue
                    routing_table_entry.add_path(
                        conf.INTRA_AREA_PATH, cost, 0, outgoing_interface, next_hop_address, '')

        return intra_area_table

    #  Returns Network Summary-LSAs / Inter-Area-Prefix-LSAs to flood in provided area
    #  Receives OSPF routing table with paths to intra-area and inter-area prefixes, area to analyze, and current
    #  Summary-LSAs / Inter-Area-Prefix-LSAs in that area
    def get_inter_area_lsa_list_to_flood(self, table, area_to_flood, existing_inter_area_lsa_list):
        lsa_list = []

        #  Removing LSAs pointing to unreachable prefixes
        for lsa_data in existing_inter_area_lsa_list:
            query_lsa = lsa_data[0]
            lsa_area = lsa_data[1]
            #  Router injected LSA in this area
            if (lsa_area == area_to_flood) & (query_lsa.header.advertising_router == self.router_id):
                keep_lsa = False
                for entry in table.entries:
                    #  Network Summary-LSA stores prefix in Link State ID
                    if self.ospf_version == conf.VERSION_IPV4:
                        if entry.destination_id == query_lsa.header.link_state_id:
                            keep_lsa = True
                    elif self.ospf_version == conf.VERSION_IPV6:
                        if entry.destination_id == query_lsa.body.address_prefix:
                            keep_lsa = True
                if not keep_lsa:  # Router lost access to area-external prefix
                    query_lsa.set_ls_age_max()
                    lsa_list.append(query_lsa)

        #  Updating costs to reach prefixes in LSAs
        for lsa_data in existing_inter_area_lsa_list:
            query_lsa = lsa_data[0]
            lsa_area = lsa_data[1]
            if (lsa_area == area_to_flood) & (query_lsa.header.advertising_router == self.router_id):
                for entry in table.entries:
                    is_advertised = False
                    if self.ospf_version == conf.VERSION_IPV4:
                        if entry.destination_id == query_lsa.header.link_state_id:
                            is_advertised = True
                    elif self.ospf_version == conf.VERSION_IPV6:
                        if entry.destination_id == query_lsa.body.address_prefix:
                            is_advertised = True
                    #  Cost to reach prefix has changed
                    if (entry.paths[0].cost != query_lsa.body.metric) & is_advertised:
                        query_lsa.header.ls_age = conf.INITIAL_LS_AGE
                        query_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                            query_lsa.header.ls_sequence_number)
                        query_lsa.body.metric = entry.paths[0].cost
                        query_lsa.set_lsa_length()
                        query_lsa.set_lsa_checksum()
                        lsa_list.append(query_lsa)

        #  Creating LSAs that advertise new area-external prefixes
        for entry in table.entries:
            is_advertised = False
            for lsa_data in existing_inter_area_lsa_list:
                query_lsa = lsa_data[0]
                lsa_area = lsa_data[1]
                if query_lsa.header.advertising_router == self.router_id:  # LSA came from this router
                    if self.ospf_version == conf.VERSION_IPV4:
                        if entry.destination_id == query_lsa.header.link_state_id:
                            is_advertised = True
                    elif self.ospf_version == conf.VERSION_IPV6:
                        if entry.destination_id == query_lsa.body.address_prefix:
                            is_advertised = True
            if (entry.area != area_to_flood) & (not is_advertised):
                prefix = entry.destination_id
                prefix_length = entry.prefix_length
                metric = entry.paths[0].cost
                if self.ospf_version == conf.VERSION_IPV4:
                    network_mask = utils.Utils.prefix_length_to_network_mask(prefix_length, self.ospf_version)
                    summary_lsa = lsa.Lsa()
                    summary_lsa.create_header(conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.LSA_TYPE_SUMMARY_TYPE_3,
                                              prefix, self.router_id, conf.INITIAL_SEQUENCE_NUMBER, self.ospf_version)
                    summary_lsa.create_summary_lsa_body(network_mask, metric)
                    lsa_list.append(summary_lsa)
                elif self.ospf_version == conf.VERSION_IPV6:
                    link_state_id = random.randint(0, conf.MAX_VALUE_16_BITS)
                    prefix_length = entry.prefix_length
                    inter_area_prefix_lsa = lsa.Lsa()
                    inter_area_prefix_lsa.create_header(
                        conf.INITIAL_LS_AGE, 0, conf.LSA_TYPE_INTER_AREA_PREFIX, link_state_id, self.router_id,
                        conf.INITIAL_SEQUENCE_NUMBER, self.ospf_version)
                    inter_area_prefix_lsa.create_inter_area_prefix_lsa_body(
                        metric, prefix_length, conf.PREFIX_OPTIONS, prefix)
                    lsa_list.append(inter_area_prefix_lsa)
                else:
                    raise ValueError("Invalid OSPF version")

        return lsa_list

    #  Updates Network Summary-LSAs / Inter-Area-Prefix-LSAs for all area LSDBs and floods required LSAs
    #  Receives LSDBs of directly connected areas
    def update_inter_area_lsa_list(self, lsdb_dict):
        existing_inter_area_lsa_list = []
        for area_id in lsdb_dict:
            database = lsdb_dict[area_id]
            if self.ospf_version == conf.VERSION_IPV4:
                for query_lsa in database.summary_lsa_type_3_list:
                    existing_inter_area_lsa_list.append([query_lsa, area_id])
            elif self.ospf_version == conf.VERSION_IPV6:
                for query_lsa in database.inter_area_prefix_lsa_list:
                    existing_inter_area_lsa_list.append([query_lsa, area_id])
        for area_id in lsdb_dict:
            lsa_list = self.get_inter_area_lsa_list_to_flood(self.routing_table, area_id, existing_inter_area_lsa_list)
            for query_lsa in lsa_list:
                self.areas[area_id].database.add_lsa(query_lsa, None)
                for interface_id in self.areas[area_id].interfaces:
                    query_interface = self.areas[area_id].interfaces[interface_id][area.INTERFACE_OBJECT]
                    query_interface.flooding_pipeline.put([query_lsa, self.router_id])
                    time.sleep(0.1)

    #  Updates own extension LSA instances, and floods updates if any (at most router has one instance of each type)
    #  Receives OSPF routing table with paths to intra-area prefixes, shortest path trees and LSDBs for each directly
    #  connected area, copy of extension LSDB which is updated and returned, and copy of area LSDBs
    def update_own_extension_lsa_list(
            self, intra_area_table, shortest_path_tree_dictionary, extension_lsdb_copy, lsdb_dict_copy):
        updated_lsa_list = []  # Empty if no LSA is created of updated
        same_areas_abr_list = self.get_abr_list_in_directly_connected_areas(lsdb_dict_copy, extension_lsdb_copy)
        if self.ospf_version == conf.VERSION_IPV4:
            own_abr_lsa = extension_lsdb_copy.get_extension_lsa(
                conf.LSA_TYPE_OPAQUE_AS, conf.OPAQUE_TYPE_ABR_LSA, self.router_id)
            own_prefix_lsa = extension_lsdb_copy.get_extension_lsa(
                conf.LSA_TYPE_OPAQUE_AS, conf.OPAQUE_TYPE_PREFIX_LSA, self.router_id)
        else:
            own_abr_lsa = extension_lsdb_copy.get_extension_lsa(conf.LSA_TYPE_EXTENSION_ABR_LSA, 0, self.router_id)
            own_prefix_lsa = extension_lsdb_copy.get_extension_lsa(
                conf.LSA_TYPE_EXTENSION_PREFIX_LSA, 0, self.router_id)

        #  Removing and updating ABR info
        if own_abr_lsa is not None:
            has_changed = False
            to_flush = False
            for abr_info in own_abr_lsa.body.abr_list:
                is_present = False
                abr = abr_info[1]
                advertised_metric = abr_info[0]
                new_metric = conf.INFINITE_COST
                for area_id in shortest_path_tree_dictionary:
                    shortest_path_tree = shortest_path_tree_dictionary[area_id]
                    for node in shortest_path_tree:
                        if node == abr:
                            is_present = True
                            if shortest_path_tree[node][0] < new_metric:
                                new_metric = shortest_path_tree[node][0]
                if not is_present:
                    if len(own_abr_lsa.body.abr_list) > 1:
                        own_abr_lsa.body.delete_abr_info(abr)
                    else:
                        to_flush = True
                    has_changed = True
                elif advertised_metric != new_metric:
                    own_abr_lsa.body.delete_abr_info(abr)
                    own_abr_lsa.add_abr_info(new_metric, abr)
                    has_changed = True
            if has_changed:
                if to_flush:  # No other ABR is known
                    own_abr_lsa.header.ls_age = conf.MAX_AGE
                else:
                    own_abr_lsa.header.ls_age = conf.INITIAL_LS_AGE
                    own_abr_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                        own_abr_lsa.header.ls_sequence_number)
                own_abr_lsa.set_lsa_length()
                own_abr_lsa.set_lsa_checksum()
                updated_lsa_list.append(own_abr_lsa)
                self.extension_database.add_extension_lsa(own_abr_lsa)
                extension_lsdb_copy.add_extension_lsa(own_abr_lsa)

        #  Removing and updating prefix info
        if own_prefix_lsa is not None:
            has_changed = False
            if self.ospf_version == conf.VERSION_IPV4:
                for subnet_info in own_prefix_lsa.body.subnet_list:
                    is_present = False
                    subnet_address = subnet_info[2]
                    netmask_length = utils.Utils.prefix_to_prefix_length(subnet_info[1])
                    advertised_metric = subnet_info[0]
                    new_metric = 0
                    for entry in intra_area_table.entries:
                        if (entry.destination_id == subnet_address) & (entry.prefix_length == netmask_length):
                            is_present = True
                            new_metric = entry.paths[0].cost
                    if not is_present:
                        own_prefix_lsa.body.delete_subnet_info(netmask_length, subnet_address)
                        has_changed = True
                    elif advertised_metric != new_metric:
                        own_prefix_lsa.body.delete_subnet_info(netmask_length, subnet_address)
                        own_prefix_lsa.body.add_subnet_info(new_metric, netmask_length, subnet_address)
            elif self.ospf_version == conf.VERSION_IPV6:
                for prefix_info in own_prefix_lsa.body.prefix_list:
                    is_present = False
                    prefix = prefix_info[3]
                    prefix_length = prefix_info[1]
                    advertised_metric = prefix_info[0]
                    new_metric = 0
                    for entry in intra_area_table.entries:
                        if (entry.destination_id == prefix) & (entry.prefix_length == prefix_length):
                            is_present = True
                            new_metric = entry.paths[0].cost
                    if not is_present:
                        own_prefix_lsa.body.delete_prefix_info(prefix_length, prefix)
                        has_changed = True
                    elif advertised_metric != new_metric:
                        own_prefix_lsa.body.delete_prefix_info(prefix_length, prefix)
                        own_prefix_lsa.body.add_prefix_info(new_metric, prefix_length, conf.PREFIX_OPTIONS, prefix)
            else:
                raise ValueError("Invalid OSPF version")
            if has_changed:
                if len(own_prefix_lsa.pack_lsa()) == conf.LSA_HEADER_LENGTH:  # LSA no longer has content
                    own_prefix_lsa.header.ls_age = conf.MAX_AGE
                else:
                    own_prefix_lsa.header.ls_age = conf.INITIAL_LS_AGE
                    own_prefix_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                        own_prefix_lsa.header.ls_sequence_number)
                own_prefix_lsa.set_lsa_length()
                own_prefix_lsa.set_lsa_checksum()
                updated_lsa_list.append(own_prefix_lsa)
                self.extension_database.add_extension_lsa(own_prefix_lsa)
                extension_lsdb_copy.add_extension_lsa(own_prefix_lsa)

        #  Adding ABR info
        for area_id in shortest_path_tree_dictionary:
            shortest_path_tree = shortest_path_tree_dictionary[area_id]
            for node in shortest_path_tree:
                if (node in same_areas_abr_list) & (node != self.router_id):
                    is_present = False
                    created_now = False
                    if own_abr_lsa is None:
                        own_abr_lsa = lsa.Lsa()
                        if self.ospf_version == conf.VERSION_IPV4:
                            own_abr_lsa.create_extension_header(
                                conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.OPAQUE_TYPE_ABR_LSA, conf.LSA_TYPE_OPAQUE_AS,
                                self.router_id, conf.INITIAL_SEQUENCE_NUMBER, self.ospf_version)
                        else:
                            own_abr_lsa.create_extension_header(
                                conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, conf.LSA_TYPE_EXTENSION_ABR_LSA,
                                self.router_id, conf.INITIAL_SEQUENCE_NUMBER, self.ospf_version)
                        own_abr_lsa.create_extension_abr_lsa_body()
                        created_now = True
                    else:
                        is_present = own_abr_lsa.has_abr_info(node)
                    if not is_present:
                        cost = self.get_cost_to_neighbor_abr(node, True, lsdb_dict_copy, extension_lsdb_copy)
                        own_abr_lsa.add_abr_info(cost, node)
                        own_abr_lsa.header.ls_age = conf.INITIAL_LS_AGE
                        if not created_now:
                            own_abr_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                                own_abr_lsa.header.ls_sequence_number)
                        own_abr_lsa.set_lsa_length()
                        own_abr_lsa.set_lsa_checksum()
                        updated_lsa_list.append(own_abr_lsa)
                        self.extension_database.add_extension_lsa(own_abr_lsa)
                        extension_lsdb_copy.add_extension_lsa(own_abr_lsa)

        #  Adding prefix info
        for entry in intra_area_table.entries:
            prefix = entry.destination_id
            prefix_length = entry.prefix_length
            cost = entry.paths[0].cost
            options = entry.options
            is_present = False
            created_now = False

            if own_prefix_lsa is None:
                own_prefix_lsa = lsa.Lsa()
                if self.ospf_version == conf.VERSION_IPV4:
                    own_prefix_lsa.create_extension_header(
                        conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.OPAQUE_TYPE_PREFIX_LSA, conf.LSA_TYPE_OPAQUE_AS,
                        self.router_id, conf.INITIAL_SEQUENCE_NUMBER, self.ospf_version)
                else:
                    own_prefix_lsa.create_extension_header(
                        conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, conf.LSA_TYPE_EXTENSION_PREFIX_LSA, self.router_id,
                        conf.INITIAL_SEQUENCE_NUMBER, self.ospf_version)
                own_prefix_lsa.create_extension_prefix_lsa_body(self.ospf_version)
                created_now = True
            else:
                if self.ospf_version == conf.VERSION_IPV4:
                    network_mask = utils.Utils.prefix_length_to_network_mask(prefix_length, self.ospf_version)
                    is_present = own_prefix_lsa.has_subnet_info(network_mask, prefix)
                else:
                    is_present = own_prefix_lsa.has_prefix_info_extension(prefix_length, prefix)

            if not is_present:
                if self.ospf_version == conf.VERSION_IPV4:
                    network_mask = utils.Utils.prefix_length_to_network_mask(prefix_length, self.ospf_version)
                    own_prefix_lsa.add_subnet_info(cost, network_mask, prefix)
                else:
                    own_prefix_lsa.add_prefix_info_extension(cost, prefix_length, options, prefix)
                own_prefix_lsa.header.ls_age = conf.INITIAL_LS_AGE
                if not created_now:
                    own_prefix_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                        own_prefix_lsa.header.ls_sequence_number)
                own_prefix_lsa.set_lsa_length()
                own_prefix_lsa.set_lsa_checksum()
                updated_lsa_list.append(own_prefix_lsa)
                self.extension_database.add_extension_lsa(own_prefix_lsa)

        #  Updating LSA instances and flooding them
        for area_id in self.areas:
            for query_lsa in updated_lsa_list:
                self.extension_database.add_extension_lsa(query_lsa)
                extension_lsdb_copy.add_extension_lsa(query_lsa)
                for interface_id in self.areas[area_id].interfaces:
                    query_interface = self.areas[area_id].interfaces[interface_id][area.INTERFACE_OBJECT]
                    query_interface.flooding_pipeline.put([query_lsa, self.router_id])
                    time.sleep(0.001)

        return extension_lsdb_copy

    #  Returns OSPF routing table with paths to intra-area and inter-area prefixes
    #  Receives OSPF routing table with paths to intra-area prefixes, shortest path tree of ABR overlay, prefixes
    #  reachable by network ABRs, copy of extension LSDB, and copy of area LSDBs
    def get_complete_ospf_routing_table(self, intra_area_table, extension_lsdb_copy, lsdb_dict_copy):
        #  Get ABR overlay shortest path tree
        directed_graph = extension_lsdb_copy.get_overlay_directed_graph()[0]
        overlay_shortest_path_tree = extension_lsdb_copy.get_shortest_path_tree(directed_graph, self.router_id)

        #  For each network prefix, get parent node (always an ABR - Can be router itself)
        abr_prefixes_dictionary = {}
        for prefix_lsa in extension_lsdb_copy.prefix_lsa_list:
            parent_node = prefix_lsa.header.advertising_router
            if self.ospf_version == conf.VERSION_IPV4:
                for subnet_info in prefix_lsa.body.subnet_list:
                    metric = subnet_info[0]
                    if overlay_shortest_path_tree is not None:  # Router knows at least another ABR
                        metric += overlay_shortest_path_tree[parent_node][0]
                    netmask = subnet_info[1]
                    subnet_address = subnet_info[2]
                    if subnet_address not in abr_prefixes_dictionary:
                        abr_prefixes_dictionary[subnet_address] = [metric, netmask, parent_node]
                    elif metric < abr_prefixes_dictionary[subnet_address][0]:
                        abr_prefixes_dictionary[subnet_address] = [metric, netmask, parent_node]
            elif self.ospf_version == conf.VERSION_IPV6:
                for prefix_info in prefix_lsa.body.prefix_list:
                    metric = prefix_info[0]
                    if overlay_shortest_path_tree is not None:
                        metric += overlay_shortest_path_tree[parent_node][0]
                    prefix_length = prefix_info[1]
                    prefix = prefix_info[3]
                    if prefix not in abr_prefixes_dictionary:
                        abr_prefixes_dictionary[prefix] = [metric, prefix_length, parent_node]
                    elif metric < abr_prefixes_dictionary[prefix][0]:
                        abr_prefixes_dictionary[prefix] = [metric, prefix_length, parent_node]
            else:
                raise ValueError("Invalid OSPF version")

        #  Replace prefix parent node for respective next hop ABR from this router
        same_areas_abr_list = self.get_abr_list_in_directly_connected_areas(
            lsdb_dict_copy, extension_lsdb_copy)  # Next hops OR router
        for prefix in abr_prefixes_dictionary:
            parent_node = abr_prefixes_dictionary[prefix][2]
            while parent_node not in same_areas_abr_list:
                parent_node = overlay_shortest_path_tree[parent_node][1]  # Parent node
            abr_prefixes_dictionary[prefix][2] = parent_node

        #  For each next hop ABR, get outgoing interface and next hop address to reach it - Ignore if router itself
        routing_info = {self.router_id: []}
        for next_hop_abr in same_areas_abr_list:
            if next_hop_abr != self.router_id:
                if self.ospf_version == conf.VERSION_IPV4:
                    cost = extension_lsdb_copy.get_extension_lsa(  # Already measured, other info needs to be fetched
                        conf.LSA_TYPE_OPAQUE_AS, conf.OPAQUE_TYPE_ABR_LSA, self.router_id).get_abr_info(next_hop_abr)[0]
                    next_hop_prefix_lsa = extension_lsdb_copy.get_extension_lsa(
                        conf.LSA_TYPE_OPAQUE_AS, conf.OPAQUE_TYPE_PREFIX_LSA, next_hop_abr)
                    for entry in intra_area_table.entries:
                        for subnet_info in next_hop_prefix_lsa.body.subnet_list:
                            if (subnet_info[2] == entry.destination_id) & (cost == entry.paths[0].cost):
                                outgoing_interface = entry.paths[0].outgoing_interface
                                if len(entry.paths[0].next_hop_address) > 0:  # Next hop ABR is not directly connected
                                    next_hop_address = entry.paths[0].next_hop_address
                                else:  # ABR is directly connected - No next hop address available
                                    for area_id in lsdb_dict_copy:
                                        next_hop_router_lsa = lsdb_dict_copy[area_id].get_lsa(
                                            conf.LSA_TYPE_ROUTER, next_hop_abr, next_hop_abr, [])
                                        if next_hop_router_lsa is None:
                                            continue  # ABR is not present in queried area
                                        network_mask = self.interfaces[
                                            self.interface_ids[0]][area.INTERFACE_OBJECT].network_mask
                                        for link_info in next_hop_router_lsa.body.links:
                                            if subnet_info[2] == utils.Utils.ip_address_to_prefix(
                                                    link_info[0], network_mask):
                                                next_hop_address = link_info[1]
                                routing_info[next_hop_abr] = [outgoing_interface, next_hop_address, entry.area]
                                break
                else:
                    cost = extension_lsdb_copy.get_extension_lsa(
                        conf.LSA_TYPE_EXTENSION_ABR_LSA, 0, self.router_id).get_abr_info(next_hop_abr)[0]
                    next_hop_prefix_lsa = extension_lsdb_copy.get_extension_lsa(
                        conf.LSA_TYPE_EXTENSION_PREFIX_LSA, 0, next_hop_abr)
                    for entry in intra_area_table.entries:
                        for prefix_info in next_hop_prefix_lsa.body.subnet_list:
                            if (prefix_info[3] == entry.destination_id) & (cost == entry.paths[0].cost):
                                outgoing_interface = entry.paths[0].outgoing_interface
                                if len(entry.paths[0].next_hop_address) > 0:  # Next hop ABR is not directly connected
                                    next_hop_address = entry.paths[0].next_hop_address
                                else:
                                    for interface_id in self.interfaces:
                                        for link_lsa in self.interfaces[interface_id][area.INTERFACE_OBJECT].\
                                                get_link_lsa_list():
                                            for prefix_data in link_lsa.body.prefixes:
                                                if (link_lsa.header.advertising_router == next_hop_abr) & (
                                                        prefix_data[2] == entry.destination_id):
                                                    next_hop_address = link_lsa.body.link_local_address
                                routing_info[next_hop_abr] = [outgoing_interface, next_hop_address, entry.area]
                                break

        #  Combines all information in one dictionary
        for next_hop_abr in routing_info:
            for prefix in abr_prefixes_dictionary:
                if abr_prefixes_dictionary[prefix][2] == next_hop_abr:
                    if next_hop_abr == self.router_id:
                        for entry in intra_area_table.entries:
                            if entry.destination_id == prefix:
                                abr_prefixes_dictionary[prefix] += [
                                    entry.paths[0].outgoing_interface, entry.paths[0].next_hop_address, entry.area]
                    else:
                        abr_prefixes_dictionary[prefix] += routing_info[next_hop_abr]

        #  Creates complete routing table
        complete_routing_table = routing_table.RoutingTable()
        for prefix in abr_prefixes_dictionary:
            if self.ospf_version == conf.VERSION_IPV4:
                prefix_length = utils.Utils.prefix_to_prefix_length(abr_prefixes_dictionary[prefix][1])
                options = conf.OPTIONS_V2
            else:
                prefix_length = abr_prefixes_dictionary[prefix][1]
                options = conf.OPTIONS_V3
            prefix_area = abr_prefixes_dictionary[prefix][5]
            complete_routing_table.add_entry(
                conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, prefix_area)
            if prefix_area in self.area_ids:
                path_type = conf.INTRA_AREA_PATH
            else:
                path_type = conf.INTER_AREA_PATH
            cost = abr_prefixes_dictionary[prefix][0]
            outgoing_interface = abr_prefixes_dictionary[prefix][3]
            next_hop_address = abr_prefixes_dictionary[prefix][4]
            complete_routing_table.get_entry(conf.DESTINATION_TYPE_NETWORK, prefix, prefix_area).add_path(
                path_type, cost, 0, outgoing_interface, next_hop_address, '')

        return complete_routing_table

    #  Runs in separate process
    @staticmethod
    def set_kernel_routing_table_from_ospf_table(ospf_version, ospf_routing_table, interface_ids):
        kernel_table.KernelTable.delete_all_ospf_routes(ospf_version)
        for entry in ospf_routing_table.entries:
            prefix = entry.destination_id
            prefix_length = entry.prefix_length
            for path in entry.paths:
                outgoing_interface = path.outgoing_interface
                next_hop_address = path.next_hop_address
                kernel_table.KernelTable.add_ospf_route(
                    prefix, prefix_length, next_hop_address, outgoing_interface, interface_ids)

    #  Creates paths in kernel routing table to all known prefixes in network
    #  Updates own extension LSAs and inter-area LSAs and floods changes as required
    #  Sets kernel routing table according to area LSDBs and extension LSDB
    def lsdb_modification_handler(self, area_lsdb_modified):
        while True:  # Code will be run until no errors are raised
            try:
                #  Required data
                shortest_path_tree_dict = {}
                prefixes_dict = {}
                #lsdb_dict = Router.clean_unconnected_routers(self.get_lsdb_copy_dict(), None, self.ospf_version)  # Deep copy - Can be reused
                lsdb_dict = self.get_lsdb_copy_dict()  # Deep copy - Can be reused
                extension_lsdb_copy = self.extension_database.__deepcopy__()
                for area_id in lsdb_dict:
                    lsdb_copy = lsdb_dict[area_id]
                    data = lsdb_copy.get_directed_graph()
                    directed_graph = data[0]
                    prefixes = data[1]
                    shortest_path_tree = lsdb_copy.get_shortest_path_tree(directed_graph, self.router_id)
                    shortest_path_tree_dict[area_id] = shortest_path_tree
                    prefixes_dict[area_id] = prefixes
                if self.router_shutdown_event.is_set():  # Shutdown
                    return

                #  Intra-area LSAs and prefixes
                if area_lsdb_modified:
                    self.routing_table = self.get_intra_area_ospf_routing_table(
                        shortest_path_tree_dict, prefixes_dict, lsdb_dict)
                    if self.abr:
                        extension_lsdb_copy = self.update_own_extension_lsa_list(
                            self.routing_table, shortest_path_tree_dict, extension_lsdb_copy, lsdb_dict)
                    if self.router_shutdown_event.is_set():
                        return

                #  Extension LSAs
                if self.abr:
                    if len(extension_lsdb_copy.prefix_lsa_list) > 1:  # Network has more than 1 ABR
                        #  Insufficient information - With more than 1 ABR, number of Prefix-LSAs must match ABR-LSAs
                        if len(extension_lsdb_copy.prefix_lsa_list) != len(extension_lsdb_copy.abr_lsa_list):
                            for query_lsa in extension_lsdb_copy.get_extension_lsdb(None):
                                if query_lsa.header.advertising_router == self.router_id:
                                    for interface_id in self.interfaces:
                                        sending_interface = self.interfaces[interface_id][area.INTERFACE_OBJECT]
                                        ls_update_packet = packet.Packet()
                                        if self.ospf_version == conf.VERSION_IPV4:
                                            ls_update_packet.create_header_v2(
                                                conf.PACKET_TYPE_LS_UPDATE, self.router_id, sending_interface.area_id,
                                                0, 0)
                                            ls_update_packet.create_ls_update_packet_body(conf.VERSION_IPV4)
                                            ls_update_packet.add_lsa(query_lsa)
                                            sending_interface.send_packet(
                                                ls_update_packet, conf.ALL_OSPF_ROUTERS_IPV4, '')
                                        else:
                                            ls_update_packet.create_header_v3(
                                                conf.PACKET_TYPE_LS_UPDATE, self.router_id, sending_interface.area_id,
                                                sending_interface.instance_id, sending_interface.ipv6_address,
                                                conf.ALL_OSPF_ROUTERS_IPV6)
                                            ls_update_packet.create_ls_update_packet_body(conf.VERSION_IPV6)
                                            ls_update_packet.add_lsa(query_lsa)
                                            sending_interface.send_packet(
                                                ls_update_packet, conf.ALL_OSPF_ROUTERS_IPV6, '')
                                area_lsdb_modified = True  # Forces recreation of self-originated extension LSAs
                            for area_id in lsdb_dict:  # Flooding of regular LSAs - Overcomes previous flooding failures
                                ls_update_packet = packet.Packet()
                                if self.ospf_version == conf.VERSION_IPV4:
                                    ls_update_packet.create_header_v2(
                                        conf.PACKET_TYPE_LS_UPDATE, self.router_id, area_id, 0, 0)
                                    ls_update_packet.create_ls_update_packet_body(conf.VERSION_IPV4)
                                    for query_lsa in lsdb_dict[area_id].get_lsdb([], None):
                                        if query_lsa.header.advertising_router == self.router_id:
                                            ls_update_packet.add_lsa(query_lsa)
                                    for interface_id in self.areas[area_id].interfaces:
                                        self.areas[area_id].interfaces[interface_id][area.INTERFACE_OBJECT].send_packet(
                                            ls_update_packet, conf.ALL_OSPF_ROUTERS_IPV4, '')
                                else:
                                    for interface_id in self.areas[area_id].interfaces:
                                        source_address = self.areas[area_id].\
                                            interfaces[interface_id][area.INTERFACE_OBJECT].ipv6_address
                                        ls_update_packet.create_header_v3(
                                            conf.PACKET_TYPE_LS_UPDATE, self.router_id, area_id, 0, source_address,
                                            conf.ALL_OSPF_ROUTERS_IPV6)
                                        ls_update_packet.create_ls_update_packet_body(conf.VERSION_IPV6)
                                        for query_lsa in lsdb_dict[area_id].get_lsdb([], None):
                                            if query_lsa.header.advertising_router == self.router_id:
                                                ls_update_packet.add_lsa(query_lsa)
                                        self.areas[area_id].interfaces[interface_id][area.INTERFACE_OBJECT].send_packet(
                                            ls_update_packet, conf.ALL_OSPF_ROUTERS_IPV6, '')
                            time.sleep(10)
                            continue  # Every ABR creates 1 Prefix-LSA and 1 ABR-LSA - Restart handler
                    if len(self.extension_database.abr_lsa_list) > 0:  # If network has more than 1 ABR
                        self.routing_table = self.get_complete_ospf_routing_table(
                            self.routing_table, extension_lsdb_copy, lsdb_dict)
                        if self.router_shutdown_event.is_set():
                            return
                if self.router_shutdown_event.is_set():
                    return

                #  Kernel routing table
                if not self.localhost:  # Integration tests cannot set kernel routing table
                    if self.kernel_table_process is not None:
                        if self.kernel_table_process.is_alive():
                            self.kernel_table_process.join()
                    self.set_kernel_routing_table_from_ospf_table(
                        self.ospf_version, self.routing_table, self.interface_ids)

                #  Inter-area LSAs and prefixes
                if self.abr:
                    self.update_inter_area_lsa_list(lsdb_dict)

                self.kernel_thread_operating.clear()
                break  # No errors raised - Kernel table and LSDBs successfully updated

            except (KeyError, TypeError, IndexError, AttributeError):
                time.sleep(5)  # Possibly LSDBs have yet to stabilize, new execution may find LSDBs stabilized

    #  Creates new thread to update kernel routing table
    def create_kernel_table_thread(self, area_lsdb_modified):
        self.kernel_thread_operating.set()
        self.kernel_table_thread = threading.Thread(target=self.lsdb_modification_handler, args=(area_lsdb_modified,))
        self.kernel_table_thread.start()

    #  #  #  #  #  #  #  #  #  #  #  #  #
    #  Command-line interface methods  #
    #  #  #  #  #  #  #  #  #  #  #  #  #

    #  Executes commands from user
    def execute_commands(self):
        while not self.router_shutdown_event.is_set():
            if not self.command_pipeline.empty():
                command_data = self.command_pipeline.get()
                command = command_data[0]
                arg = command_data[1]

                if command == SHOW:
                    self.show_general_data()
                elif command == SHOW_INTERFACE:
                    self.show_interface_data()
                elif command == SHOW_NEIGHBOR:
                    self.show_neighbor_data()
                elif command == SHOW_LSDB:
                    self.show_lsdb_content()
                elif command == SHOW_DATABASE_SUMMARY:
                    self.show_lsdb_database_summary()
                elif command == SHUTDOWN_INTERFACE:
                    self.shutdown_interface(arg)
                elif command == START_INTERFACE:
                    self.start_interface(arg)
                elif command == SHOW_CONVERGENCE:
                    self.show_convergence_time()
                else:
                    continue
                self.output_event.set()

    #  Prints general protocol information
    def show_general_data(self):
        time_elapsed = datetime.datetime.now() - self.start_time
        print("RID", self.router_id)
        print("Start time:", str(datetime.time(self.start_time.hour, self.start_time.minute, self.start_time.second)) +
              ", Time elapsed:", str(datetime.timedelta(seconds=int(time_elapsed.total_seconds()))))
        for a in self.areas:
            if a == '0.0.0.0':
                print("Area BACKBONE")
            else:
                print("Area", a)
            print("\tNumber of interfaces in this area is", len(self.areas[a].interfaces))
            for i in self.areas[a].interfaces:
                print("\t\t" + i)

    #  Prints interface information
    def show_interface_data(self):
        for a in self.areas:
            for i in self.areas[a].interfaces:
                if self.areas[a].is_interface_operating(i):
                    print("Interface", i, "is up, line protocol is up")
                else:
                    print("Interface", i, "is up, line protocol is down")

                if self.ospf_version == conf.VERSION_IPV4:
                    ip_address = utils.Utils.interface_name_to_ipv4_address(i)
                    prefix_length = str(utils.Utils.interface_name_to_ipv4_prefix_and_length(i)[1])
                    print("\tInternet Address", ip_address + "/" + prefix_length + ", Area", a)
                    cost = self.interfaces[i][0].cost
                    print("\tProcess ID 1, Router ID", self.router_id + ", Network Type BROADCAST, Cost:", cost)
                else:
                    link_local_address = utils.Utils.interface_name_to_ipv6_link_local_address(i)
                    interface_id = self.interfaces[i][0].ospf_identifier
                    print("\tLink Local Address", link_local_address + ", Interface ID", interface_id)
                    print("\tArea", a + ", Process ID 1, Instance ID 0, Router ID", self.router_id)
                    cost = self.interfaces[i][0].cost
                    print("\tNetwork Type BROADCAST, Cost:", cost)

                print("\tTimer intervals configured, Hello " + str(conf.HELLO_INTERVAL) + ", Dead",
                      conf.ROUTER_DEAD_INTERVAL)
                if self.areas[a].is_interface_operating(i):
                    time_to_hello = self.interfaces[i][0].hello_timer.get_timer_time()
                    print("\t\tHello due in", str(datetime.timedelta(seconds=time_to_hello)))
                    neighbor_count = self.interfaces[i][0].get_neighbor_count()
                    adjacent_neighbor_count = self.interfaces[i][0].get_adjacent_neighbor_count()
                    print("\tNeighbor Count is", str(neighbor_count) + ", Adjacent neighbor count is",
                          adjacent_neighbor_count)
                    for n in self.interfaces[i][0].neighbors:
                        print("\t\tAdjacent with neighbor", n)

    #  Prints neighbor information
    def show_neighbor_data(self):
        for i in self.interfaces:
            neighbors = self.interfaces[i][0].neighbors
            print(self.interfaces[i][0].physical_identifier)
            if self.ospf_version == conf.VERSION_IPV4:
                print("Neighbor ID\tState\t\tDR/BDR\t\tDead Time\tAddress\t\tInterface")
            else:
                print("Neighbor ID\tState\t\tDR/BDR\t\tDead Time\tInterface ID\tInterface")
            for n in neighbors:
                neighbor_state = neighbors[n].neighbor_state
                dead_time = str(datetime.timedelta(seconds=neighbors[n].inactivity_timer.get_timer_time()))
                neighbor_address = neighbors[n].neighbor_ip_address
                neighbor_interface_id = neighbors[n].neighbor_interface_id
                if self.interfaces[i][area.INTERFACE_OBJECT].designated_router in [n, neighbor_address]:
                    dr_bdr = "DR"
                elif self.interfaces[i][area.INTERFACE_OBJECT].backup_designated_router in [n, neighbor_address]:
                    dr_bdr = "BDR"
                else:
                    dr_bdr = "DROTHER"

                if self.ospf_version == conf.VERSION_IPV4:
                    print(n + "\t\t" + neighbor_state + "\t\t" + dr_bdr + "\t\t" + dead_time + "\t\t" +
                          neighbor_address + "\t" + i)
                else:
                    print(n + "\t\t" + neighbor_state + "\t\t" + dr_bdr + "\t\t" + dead_time + "\t\t" +
                          str(neighbor_interface_id) + "\t\t" + i)

    #  Prints LSDB content
    def show_lsdb_content(self):
        for a in self.areas:
            query_area = self.areas[a]
            if query_area.area_id == conf.BACKBONE_AREA:
                print("Area BACKBONE")
            else:
                print("Area", query_area.area_id)
            for query_lsa in query_area.database.get_lsdb([], None):
                print(query_lsa)
            for i in query_area.interfaces:
                query_interface = query_area.interfaces[i][area.INTERFACE_OBJECT]
                for query_lsa in query_interface.link_local_lsa_list:
                    print(query_lsa)
        if self.abr:
            lsdb_content = self.extension_database.get_extension_lsdb(None)
            print("Extension LSDB - OSPFv" + str(self.ospf_version))
            if len(lsdb_content) == 0:
                print("Router does not have extension LSAs")
            else:
                for query_lsa in lsdb_content:
                    print(query_lsa)

    #  Prints LSDB content summary
    def show_lsdb_database_summary(self):
        for a in self.areas:
            query_area = self.areas[a]
            if query_area.area_id == conf.BACKBONE_AREA:
                print("Area BACKBONE")
            else:
                print("Area", query_area.area_id)
            print("Type\tLink ID\t\tADV Router\tAge\tSeq#\t\tChecksum")
            for query_lsa in query_area.database.get_lsdb([], None):
                ls_type = header.Header.get_ls_type(query_lsa.header.ls_type)
                ls_id = query_lsa.header.link_state_id
                advertising_router = query_lsa.header.advertising_router
                ls_age = query_lsa.header.ls_age
                sequence_number = query_lsa.header.ls_sequence_number
                checksum = query_lsa.header.ls_checksum
                if len(ls_id) >= 8:
                    variable_tab = '\t'
                else:
                    variable_tab = '\t\t'
                print(str(ls_type) + '\t' + ls_id + variable_tab + advertising_router + '\t\t' + str(ls_age) + '\t' +
                      str(hex(sequence_number)) + '\t' + str(hex(checksum)))
            for i in query_area.interfaces:
                query_interface = query_area.interfaces[i][area.INTERFACE_OBJECT]
                for query_lsa in query_interface.link_local_lsa_list:
                    ls_type = header.Header.get_ls_type(query_lsa.header.ls_type)
                    ls_id = query_lsa.header.link_state_id
                    advertising_router = query_lsa.header.advertising_router
                    ls_age = query_lsa.header.ls_age
                    sequence_number = query_lsa.header.ls_sequence_number
                    checksum = query_lsa.header.ls_checksum
                    if len(ls_id) >= 8:
                        variable_tab = '\t'
                    else:
                        variable_tab = '\t\t'
                    print(str(ls_type) + '\t' + ls_id + variable_tab + advertising_router + '\t\t' + str(ls_age) +
                          '\t' + str(hex(sequence_number)) + '\t' + str(hex(checksum)))
        if self.abr:
            lsdb_content = self.extension_database.get_extension_lsdb(None)
            print("Extension LSDB - OSPFv" + str(self.ospf_version))
            if len(lsdb_content) == 0:
                print("Router does not have extension LSAs")
            else:
                for query_lsa in lsdb_content:
                    ls_type = header.Header.get_ls_type(query_lsa.header.ls_type)
                    ls_id = query_lsa.header.link_state_id
                    advertising_router = query_lsa.header.advertising_router
                    ls_age = query_lsa.header.ls_age
                    sequence_number = query_lsa.header.ls_sequence_number
                    checksum = query_lsa.header.ls_checksum
                    if len(ls_id) >= 8:
                        variable_tab = '\t'
                    else:
                        variable_tab = '\t\t'
                    print(str(ls_type) + '\t' + ls_id + variable_tab + advertising_router + '\t' + str(ls_age) +
                          '\t\t' + str(hex(sequence_number)) + '\t' + str(hex(checksum)))

    #  Shows convergence time from router start to kernel routing table stabilization
    def show_convergence_time(self):
        kernel_modification_time = kernel_table.KernelTable.get_modification_time().time()
        convergence_time = (kernel_table.KernelTable.get_modification_time() - self.start_time).total_seconds()
        print("Router start time:", self.start_time.time())
        if convergence_time > 0:
            print("Last kernel routing table update:", kernel_modification_time)
            print("Convergence time:", convergence_time, "seconds")
        else:
            print("No update to the kernel routing table has been made")

    #  Performs shutdown of specified interface
    def shutdown_interface(self, physical_identifier):
        if physical_identifier not in self.interfaces:
            print("OSPFv" + str(self.ospf_version), "interface not found")
        for a in self.areas:
            if physical_identifier in self.areas[a].interfaces:
                self.areas[a].shutdown_interface(physical_identifier)

    #  Starts specified interface
    def start_interface(self, physical_identifier):
        if physical_identifier not in self.interfaces:
            print("OSPFv" + str(self.ospf_version), "interface not found")
        for a in self.areas:
            if physical_identifier in self.areas[a].interfaces:
                self.areas[a].start_interface(physical_identifier)

    #  Ensures router is down, and with it all of its area data structures and interfaces
    def shutdown_router(self):
        if self.kernel_table_process is not None:
            if self.kernel_table_process.is_alive():
                self.kernel_table_process.join()
                try:
                    kernel_table.KernelTable.lock.release()
                except AssertionError:
                    pass  # As lock is recursive, releasing it with other thread will raise error
        if self.kernel_table_thread is not None:
            if self.kernel_table_thread.is_alive():
                self.kernel_table_thread.join()

        for s in self.socket_shutdown_events:
            self.socket_shutdown_events[s].set()
        for t in self.socket_processes:
            self.socket_processes[t].join()
        kernel_table.KernelTable.delete_all_ospf_routes(self.ospf_version)

        try:
            self.extension_database.release_all_locks()
        except RuntimeError:
            pass  # Lock was not acquired - Nothing to do

        for a in self.areas:
            try:
                self.areas[a].database.release_all_locks()
            except RuntimeError:
                pass
            self.areas[a].shutdown_area()
        self.command_thread.join()

    #  #  #  #  #  #  #  #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #  #

    #  Given a list, returns its unique values
    @staticmethod
    def get_unique_values(input_list):
        return list(set(input_list))

    #  Given list of interface areas, returns True if router is ABR, returns False otherwise
    @staticmethod
    def is_abr(area_list):
        if len(Router.get_unique_values(area_list)) > 1:  # Router connected to multiple areas
            return True
        else:
            return False

    #  Returns list of all ABRs in directly connected areas
    def get_abr_list_in_directly_connected_areas(self, lsdb_dict_copy, extension_lsdb_copy):
        if self.abr:
            routers = [self.router_id]
        else:
            routers = []
        for prefix_lsa in extension_lsdb_copy.prefix_lsa_list:  # Routers are associated with 1 or + network prefixes
            abr_id = prefix_lsa.header.advertising_router
            if (abr_id != self.router_id) & (  # ABR is reachable
                    self.get_cost_to_neighbor_abr(
                        abr_id, True, lsdb_dict_copy, extension_lsdb_copy) < conf.INFINITE_COST):
                routers.append(abr_id)
        return routers

    #  Given neighbor ABR ID, returns either intra-area shortest path cost or overall shortest path cost
    #  To ensure atomicity of operation, it is necessary to supply copy of area LSDBs and copy of extension LSDB
    def get_cost_to_neighbor_abr(self, abr_id, intra_area_only, lsdb_dict_copy, extension_lsdb_copy):
        if abr_id == self.router_id:
            return 0  # Itself
        if intra_area_only:  # Only intra-area paths to ABR allowed
            shortest_cost = conf.INFINITE_COST
            prefix_list = []  # Prefixes directly connected to target ABR
            if self.ospf_version == conf.VERSION_IPV4:
                for area_id in lsdb_dict_copy:
                    router_lsa = lsdb_dict_copy[area_id].get_lsa(conf.LSA_TYPE_ROUTER, abr_id, abr_id, [])
                    if router_lsa is not None:
                        for link_info in router_lsa.body.links:  # In transit networks, only contains IP addresses
                            if link_info[2] == conf.LINK_TO_TRANSIT_NETWORK:
                                for network_lsa in lsdb_dict_copy[area_id].network_lsa_list:  # Netmask is here
                                    if network_lsa.header.link_state_id == link_info[0]:  # DR interface IP
                                        network_mask = network_lsa.body.network_mask
                                        network_prefix = utils.Utils.ip_address_to_prefix(link_info[0], network_mask)
                                        prefix_list.append(network_prefix)
            else:
                for area_id in lsdb_dict_copy:
                    for query_lsa in lsdb_dict_copy[area_id].intra_area_prefix_lsa_list:
                        if header.Header.get_ls_type(query_lsa.body.referenced_ls_type) == conf.LSA_TYPE_NETWORK:
                            for prefix_info in query_lsa.body.prefixes:
                                prefix_list.append(prefix_info[3])
            for prefix in prefix_list:  # Finding the closest prefix to this router
                for entry in self.routing_table.entries:
                    if (entry.destination_id == prefix) & (entry.paths[0].cost < shortest_cost):
                        shortest_cost = entry.paths[0].cost
            return shortest_cost
        else:
            abr_overlay_shortest_path_tree = extension_lsdb_copy.get_shortest_path_tree(
                extension_lsdb_copy.get_overlay_directed_graph(), self.router_id)
            for query_abr in abr_overlay_shortest_path_tree:
                if abr_id == query_abr:
                    return abr_overlay_shortest_path_tree[query_abr][0]

    #  Returns True if all neighbors are adjacent and stable i.e. are in 2-WAY or FULL states
    def are_neighbors_stable(self):
        neighbors_stable = True
        for interface_id in self.interfaces:
            neighbors = self.interfaces[interface_id][area.INTERFACE_OBJECT].neighbors
            for neighbor_id in neighbors:
                if neighbors[neighbor_id].neighbor_state not in [conf.NEIGHBOR_STATE_2_WAY, conf.NEIGHBOR_STATE_FULL]:
                    neighbors_stable = False
        return neighbors_stable

    #  Returns dictionary with deep copy of all router LSDBs
    def get_lsdb_copy_dict(self):
        lsdb_copy_dict = {}
        for area_id in self.areas:
            lsdb_copy_dict[area_id] = copy.deepcopy(self.areas[area_id].database)
        return lsdb_copy_dict

    #  Returns True if provided router is connected to network - If it appears in any current Network-LSA
    #  Assumes router either has all interfaces connected or is fully disconnected/down - No partial shutdown supported
    @staticmethod
    def is_router_connected(router_id, lsdb_dict_copy, ospf_version):
        for area_id in lsdb_dict_copy:
            query_lsdb = lsdb_dict_copy[area_id]

            router_in_network_lsa = False
            for network_lsa in query_lsdb.network_lsa_list:
                if router_id in network_lsa.body.attached_routers:
                    if network_lsa.header.advertising_router != router_id:
                        return True  # Router is in Network-LSA from another router
                    else:
                        router_in_network_lsa = True
            if not router_in_network_lsa:
                continue  # Router is not in any Network-LSA of this area

            for network_lsa in query_lsdb.network_lsa_list:
                if network_lsa.header.advertising_router == router_id:
                    routers_accepting_this_as_dr = [router_id]
                    #  Routers that this router says are connected to same subnets
                    for query_router_id in network_lsa.body.attached_routers:
                        router_lsa = query_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, query_router_id, query_router_id, [])
                        for link_info in router_lsa.body.links:
                            if ospf_version == conf.VERSION_IPV4:
                                if link_info[0] == network_lsa.header.link_state_id:
                                    routers_accepting_this_as_dr.append(router_lsa.header.advertising_router)
                            else:
                                if link_info[4] == router_id:
                                    routers_accepting_this_as_dr.append(router_lsa.header.advertising_router)

                    if Router.get_unique_values(routers_accepting_this_as_dr) == Router.get_unique_values(
                            network_lsa.body.attached_routers):
                        return True  # Every router in link recognizes router as DR - No discrepancies

        return False

    #  Cleans LSDBs of LSAs from unconnected/down routers - Should only be run in LSDB copies
    @staticmethod
    def clean_unconnected_routers(lsdb_dict_copy, extension_lsdb_copy, ospf_version):
        unconnected_routers = []
        for area_id in lsdb_dict_copy:
            query_lsdb = lsdb_dict_copy[area_id]
            for query_lsa in query_lsdb.router_lsa_list:
                if not Router.is_router_connected(query_lsa.header.advertising_router, lsdb_dict_copy, ospf_version):
                    unconnected_routers.append(query_lsa.header.advertising_router)

        lsa_list_to_delete = []
        extension_lsa_list_to_delete = []
        for area_id in lsdb_dict_copy:
            query_lsdb = lsdb_dict_copy[area_id]
            for query_lsa in query_lsdb.get_lsdb([], None):
                if query_lsa.header.advertising_router in unconnected_routers:
                    lsa_list_to_delete.append(query_lsa.get_lsa_identifier())
        if extension_lsdb_copy is not None:
            for query_lsa in extension_lsdb_copy.get_extension_lsdb(None):
                if query_lsa.header.advertising_router in unconnected_routers:
                    extension_lsa_list_to_delete.append(query_lsa.get_lsa_identifier())

        for area_id in lsdb_dict_copy:
            query_lsdb = lsdb_dict_copy[area_id]
            for lsa_to_delete in lsa_list_to_delete:
                query_lsdb.delete_lsa(lsa_to_delete[0], lsa_to_delete[1], lsa_to_delete[2], [])
        if extension_lsdb_copy is not None:
            for lsa_to_delete in extension_lsa_list_to_delete:
                extension_lsdb_copy.delete_lsa(lsa_to_delete[0], lsa_to_delete[1], lsa_to_delete[2], [])

        if extension_lsdb_copy is None:
            return lsdb_dict_copy
        return lsdb_dict_copy, extension_lsdb_copy
