import queue
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
import area.lsdb as lsdb
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
SHUTDOWN_INTERFACE = 5
START_INTERFACE = 6


class Router:

    def set_up(self, router_id, ospf_version, router_shutdown_event, interface_ids, area_ids, localhost,
               command_pipeline, output_event):
        if ospf_version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
            raise ValueError("Invalid OSPF version")
        self.ospf_version = ospf_version

        #  Localhost operation parameters - Only for test purposes

        self.localhost = localhost  # If router is operating on localhost or not - If False router operates normally
        self.interface_ids = interface_ids  # Interfaces in this machine
        self.area_ids = area_ids  # OSPF areas of the interfaces

        #  OSPF top-level parameters

        self.router_id = router_id
        self.areas = {}
        external_routing_capable = False
        for area_id in Router.get_unique_values(self.area_ids):
            area_interfaces = []
            for i in range(len(self.interface_ids)):
                if area_ids[i] == area_id:
                    area_interfaces.append(self.interface_ids[i])
            new_area = area.Area(
                self.router_id, self.ospf_version, area_id, external_routing_capable, area_interfaces, self.localhost,
                Router.is_abr(area_ids))
            self.areas[area_id] = new_area
        self.interfaces = {}
        for area_id in Router.get_unique_values(self.area_ids):
            for interface_id in self.areas[area_id].interfaces:
                self.interfaces[interface_id] = self.areas[area_id].interfaces[interface_id]
        self.max_ip_datagram = conf.MTU
        self.routing_table = routing_table.RoutingTable()

        #  Implementation-specific parameters

        self.packet_sockets = {}
        self.packet_pipelines = {}
        for interface_id in self.interfaces:
            self.packet_sockets[interface_id] = sock.Socket()
            self.packet_pipelines[interface_id] = queue.Queue()
        self.socket_shutdown_events = {}
        for interface_id in self.interfaces:
            self.socket_shutdown_events[interface_id] = threading.Event()
        self.socket_threads = {}
        accept_self_packets = False
        is_dr = threading.Event()  # Event is clear on creation - Router on startup is never DR/BDR
        for interface_id in self.interfaces:
            if self.ospf_version == conf.VERSION_IPV4:
                self.socket_threads[interface_id] = threading.Thread(
                    target=self.packet_sockets[interface_id].receive_ipv4,
                    args=(self.packet_pipelines[interface_id], self.socket_shutdown_events[interface_id], interface_id,
                          accept_self_packets, is_dr, localhost))
            else:
                self.socket_threads[interface_id] = threading.Thread(
                    target=self.packet_sockets[interface_id].receive_ipv6,
                    args=(self.packet_pipelines[interface_id], self.socket_shutdown_events[interface_id], interface_id,
                          accept_self_packets, is_dr, localhost))
            self.socket_threads[interface_id].start()
        self.router_shutdown_event = router_shutdown_event
        self.start_time = datetime.datetime.now()
        self.abr = Router.is_abr(area_ids)
        self.shortest_path_tree_dictionary = {}  # One tree per area
        self.command_pipeline = command_pipeline  # User commands
        self.output_event = output_event  # If has printed desired output, if any
        self.command_thread = threading.Thread(target=self.execute_commands)
        self.command_thread.start()
        self.table_process_running = multiprocessing.Event()

        #  Extension LSDB
        self.extension_database = extension_lsdb.ExtensionLsdb(self.ospf_version)

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
                                ls_update_packet.create_header_v2(conf.PACKET_TYPE_LS_UPDATE, self.router_id, a,
                                                                  conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
                            else:
                                ls_update_packet.create_header_v3(
                                    conf.PACKET_TYPE_LS_UPDATE, self.router_id, a, current_interface.instance_id,
                                    current_interface.ipv6_address, destination_address)
                            ls_update_packet.create_ls_update_packet_body(self.ospf_version)
                            ls_update_packet.add_lsa(lsa_instance)
                            j.send_packet(ls_update_packet, destination_address, None)
                            current_interface.flooded_pipeline.put(True)
                            time.sleep(0.1)

            #  Sets the Linux kernel default routing table if any LSDB was changed and enough time has passed
            if (not self.localhost) & (not self.table_process_running.is_set()):
                lsdb_modified = False
                for area_id in self.areas:
                    query_area = self.areas[area_id]
                    area_lsdb = query_area.database
                    if area_lsdb.is_modified.is_set():  # LSDB was modified
                        if time.perf_counter() - area_lsdb.get_modification_time() > conf.KERNEL_UPDATE_INTERVAL:
                            area_lsdb.is_modified.clear()
                            area_lsdb.reset_modification_time()
                            lsdb_modified = True
                if lsdb_modified:
                    self.table_process_running.set()
                    process = multiprocessing.Process(target=self.set_kernel_routing_table)
                    process.start()  # Separate process is required due to slow execution time

            #  Tells receiving socket whether respective interface is DR/BDR or not, if state changed
            for interface_id in self.interfaces:
                interface_is_dr_bdr = self.interfaces[interface_id][area.INTERFACE_OBJECT].is_dr_bdr()
                socket_is_dr_flag = self.packet_sockets[interface_id].is_dr
                if interface_is_dr_bdr != socket_is_dr_flag.is_set():
                    if interface_is_dr_bdr:
                        socket_is_dr_flag.set()
                    else:
                        socket_is_dr_flag.clear()

            #  Searches for extension LSAs received by the interfaces
            for interface_id in self.interfaces:
                extension_lsa_pipeline = self.interfaces[interface_id][area.INTERFACE_OBJECT].extension_lsa_pipeline
                flooding_pipeline = self.interfaces[interface_id][area.INTERFACE_OBJECT].flooding_pipeline
                while not extension_lsa_pipeline.empty():
                    extension_lsa = extension_lsa_pipeline.get()
                    self.extension_database.add_extension_lsa(extension_lsa)
                    flooding_pipeline.put(extension_lsa)

        #  Router signalled to shutdown
        self.shutdown_router()

    #  #  #  #  #  #  #  #  #  #
    #  Routing table creation  #
    #  #  #  #  #  #  #  #  #  #

    #  Returns a routing table with intra-area routers given a shortest path tree and the corresponding prefixes
    def get_intra_area_routing_table(self, shortest_path_tree_dictionary, prefixes_dictionary):
        table = routing_table.RoutingTable()
        for area_id in self.areas:
            #  Initialization

            query_area = self.areas[area_id]
            area_lsdb = query_area.database
            area_lsdb.lsdb_lock.acquire()
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
                        node_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, node_id, node_id, interface_array)
                        if node_lsa is not None:  # Router node
                            for link_info in node_lsa.body.links:
                                if (link_info[2] == conf.LINK_TO_STUB_NETWORK) & (link_info[0] == prefix):
                                    prefix_length = utils.Utils.get_prefix_length_from_prefix(link_info[1])
                                    options = node_lsa.header.options
                                    table.add_entry(
                                        conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, area_id)
                                    #  Root to router + router to prefix
                                    cost = shortest_path_tree[node_id][0] + link_info[4]
                                    prefixes_with_costs[node_id][prefix] = [cost]
                        else:  # Transit network node
                            for network_lsa in area_lsdb.network_lsa_list:
                                if network_lsa.header.link_state_id == node_id:
                                    prefix_length = utils.Utils.get_prefix_length_from_prefix(
                                        network_lsa.body.network_mask)
                                    options = network_lsa.header.options
                                    table.add_entry(
                                        conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, area_id)
                                    cost = shortest_path_tree[node_id][0]  # Root to network
                                    prefixes_with_costs[node_id][prefix] = [cost]
                    elif self.ospf_version == conf.VERSION_IPV6:
                        node_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, node_id, interface_array)
                        if node_lsa is not None:  # Router node
                            options = node_lsa.body.options
                            intra_area_prefix_lsa = area_lsdb.get_lsa(
                                conf.LSA_TYPE_INTRA_AREA_PREFIX, 0, node_id, interface_array)
                            for prefix_info in intra_area_prefix_lsa.body.prefixes:
                                if prefix_info[3] == prefix:
                                    prefix_length = prefix_info[0]
                                    table.add_entry(
                                        conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, area_id)
                                    #  Root to router + router to prefix
                                    cost = shortest_path_tree[node_id][0] + prefix_info[2]
                                    prefixes_with_costs[node_id][prefix] = [cost]
                        else:  # Transit network node
                            router_id = node_id.split("|")[0]
                            interface_id = node_id.split("|")[1]
                            network_lsa = area_lsdb.get_lsa(
                                conf.LSA_TYPE_NETWORK, interface_id, router_id, interface_array)
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
                                    table.add_entry(
                                        conf.DESTINATION_TYPE_NETWORK, prefix, prefix_length, options, area_id)
                                    cost = shortest_path_tree[node_id][0]  # Root to network
                                    prefixes_with_costs[node_id][prefix] = [cost]
                    else:
                        area_lsdb.lsdb_lock.release()
                        raise ValueError("Invalid OSPF version")

            #  Finding the next hop information to reach nodes in the same links as the root node

            root_id = ''
            for node_id in shortest_path_tree:
                if shortest_path_tree[node_id][1] == node_id:  # Only root node has itself as parent node
                    root_id = node_id
            for node_id in shortest_path_tree:
                if (shortest_path_tree[node_id][1] == root_id) & (node_id != root_id):  # Node with root as parent node
                    if self.ospf_version == conf.VERSION_IPV4:
                        node_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, node_id, node_id, interface_array)
                        if node_lsa is not None:  # Node is a router - Root is connected through point-to-point link
                            root_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, root_id, root_id, interface_array)
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
                                                        conf.LSA_TYPE_ROUTER, destination, destination, interface_array)
                                                    for link_info in destination_lsa.body.links:
                                                        if link_info[0] == node_id:
                                                            next_hop_address = link_info[1]
                                                            next_hop_info[destination] = [
                                                                outgoing_interface, next_hop_address]
                    else:
                        node_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, node_id, interface_array)
                        root_lsa = area_lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, root_id, interface_array)
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
                                                        conf.LSA_TYPE_ROUTER, 0, destination, interface_array)
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
            area_lsdb.lsdb_lock.release()

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
                    routing_table_entry = table.get_entry(conf.DESTINATION_TYPE_NETWORK, prefix, area_id)
                    if len(routing_table_entry.paths) > 0:
                        if cost < routing_table_entry.paths[0].cost:
                            routing_table_entry.delete_all_paths()
                        elif cost > routing_table_entry.paths[0].cost:
                            continue
                    routing_table_entry.add_path(
                        conf.INTRA_AREA_PATH, cost, 0, outgoing_interface, next_hop_address, '')

        return table

    #  Sets the Linux kernel default routing table according to the supplied OSPF routing table
    def set_kernel_routing_table_from_ospf_table(self, ospf_routing_table):
        kernel_table.KernelTable.delete_all_ospf_routes(self.ospf_version)
        for entry in ospf_routing_table.entries:
            prefix = entry.destination_id
            prefix_length = entry.prefix_length
            for path in entry.paths:
                outgoing_interface = path.outgoing_interface
                next_hop_address = path.next_hop_address
                kernel_table.KernelTable.add_ospf_route(
                    prefix, prefix_length, next_hop_address, outgoing_interface, self.interface_ids)

    #  Sets the Linux kernel default routing table according to the LSDBs content
    def set_kernel_routing_table(self):
        shortest_path_tree_dictionary = {}
        prefixes_dictionary = {}
        for area_id in self.areas:
            query_area = self.areas[area_id]
            lsdb_content = query_area.database.get_lsdb([], None)  # Shared resource
            #  Copying LSDB is faster than obtaining OSPF routing table from it, reducing time lock is acquired
            lsdb_copy = lsdb.Lsdb(self.ospf_version, area_id)
            for query_lsa in lsdb_content:
                lsdb_copy.add_lsa(query_lsa, None)
            data = query_area.database.get_directed_graph()
            directed_graph = data[0]
            prefixes = data[1]
            shortest_path_tree = query_area.database.get_shortest_path_tree(directed_graph, self.router_id)
            shortest_path_tree_dictionary[query_area.area_id] = shortest_path_tree
            prefixes_dictionary[query_area.area_id] = prefixes
        self.shortest_path_tree_dictionary = shortest_path_tree_dictionary
        self.routing_table = self.get_intra_area_routing_table(shortest_path_tree_dictionary, prefixes_dictionary)
        if self.router_shutdown_event.is_set():  # Shutdown
            return
        elif self.abr:
            self.update_inter_area_lsa_list()

        with kernel_table.KernelTable.lock:
            self.set_kernel_routing_table_from_ospf_table(self.routing_table)

        self.table_process_running.clear()

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
                elif command == SHUTDOWN_INTERFACE:
                    self.shutdown_interface(arg)
                elif command == START_INTERFACE:
                    self.start_interface(arg)
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
                    ip_address = utils.Utils.get_ipv4_address_from_interface_name(i)
                    prefix_length = str(utils.Utils.get_ipv4_prefix_from_interface_name(i)[1])
                    print("\tInternet Address", ip_address + "/" + prefix_length + ", Area", a)
                    cost = self.interfaces[i][0].cost
                    print("\tProcess ID 1, Router ID", self.router_id + ", Network Type BROADCAST, Cost:", cost)
                else:
                    link_local_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(i)
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
                print("Neighbor ID\tState\t\tDead Time\tAddress\t\tInterface")
            else:
                print("Neighbor ID\tState\t\tDead Time\tInterface ID\tInterface")
            for n in neighbors:
                neighbor_state = neighbors[n].neighbor_state
                dead_time = str(datetime.timedelta(seconds=neighbors[n].inactivity_timer.get_timer_time()))
                neighbor_address = neighbors[n].neighbor_ip_address
                neighbor_interface_id = neighbors[n].neighbor_interface_id
                if self.ospf_version == conf.VERSION_IPV4:
                    print(n + "\t\t" + neighbor_state + "\t\t" + dead_time + "\t\t" + neighbor_address + "\t" + i)
                else:
                    print(n + "\t\t" + neighbor_state + "\t\t" + dead_time + "\t\t" + str(neighbor_interface_id) +
                          "\t\t" + i)

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
        kernel_table.KernelTable.delete_all_ospf_routes(self.ospf_version)
        for s in self.socket_shutdown_events:
            self.socket_shutdown_events[s].set()
        for t in self.socket_threads:
            self.socket_threads[t].join()
        for a in self.areas:
            self.areas[a].shutdown_area()
        self.command_thread.join()

    #  #  #  #  #  #  #  #
    #  Extension methods  #
    #  #  #  #  #  #  #  #

    #  Given OSPF routing table, area ID, router ID, list of existing Network Summary-LSAs / Inter-Area-Prefix-LSAs and
    #  OSPF version, returns Network Summary-LSAs / Inter-Area-Prefix-LSAs to flood in area
    @staticmethod
    def get_inter_area_lsa_list_to_flood(table, area_to_flood, router_id, existing_lsa_list, version):
        lsa_list = []

        #  Removing LSAs pointing to unreachable prefixes
        for lsa_data in existing_lsa_list:
            query_lsa = lsa_data[0]
            lsa_area = lsa_data[1]
            #  Router injected LSA in this area
            if (lsa_area == area_to_flood) & (query_lsa.header.advertising_router == router_id):
                keep_lsa = False
                for entry in table.entries:
                    #  Network Summary-LSA stores prefix in Link State ID
                    if version == conf.VERSION_IPV4:
                        if entry.destination_id == query_lsa.header.link_state_id:
                            keep_lsa = True
                    elif version == conf.VERSION_IPV6:
                        if entry.destination_id == query_lsa.body.address_prefix:
                            keep_lsa = True
                if not keep_lsa:  # Router lost access to area-external prefix
                    query_lsa.set_ls_age_max()
                    lsa_list.append(query_lsa)

        #  Updating costs to reach prefixes in LSAs
        for lsa_data in existing_lsa_list:
            query_lsa = lsa_data[0]
            lsa_area = lsa_data[1]
            if (lsa_area == area_to_flood) & (query_lsa.header.advertising_router == router_id):
                for entry in table.entries:
                    is_advertised = False
                    if version == conf.VERSION_IPV4:
                        if entry.destination_id == query_lsa.header.link_state_id:
                            is_advertised = True
                    elif version == conf.VERSION_IPV6:
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
            for lsa_data in existing_lsa_list:
                query_lsa = lsa_data[0]
                lsa_area = lsa_data[1]
                if query_lsa.header.advertising_router == router_id:  # LSA came from this router
                    if version == conf.VERSION_IPV4:
                        if entry.destination_id == query_lsa.header.link_state_id:
                            is_advertised = True
                    elif version == conf.VERSION_IPV6:
                        if entry.destination_id == query_lsa.body.address_prefix:
                            is_advertised = True
            if (entry.area != area_to_flood) & (not is_advertised):
                prefix = entry.destination_id
                prefix_length = entry.prefix_length
                metric = entry.paths[0].cost
                if version == conf.VERSION_IPV4:
                    network_mask = utils.Utils.prefix_length_to_network_mask(prefix_length, version)
                    summary_lsa = lsa.Lsa()
                    summary_lsa.create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_SUMMARY_TYPE_3, prefix,
                                              router_id, conf.INITIAL_SEQUENCE_NUMBER, version)
                    summary_lsa.create_summary_lsa_body(network_mask, metric)
                    lsa_list.append(summary_lsa)
                elif version == conf.VERSION_IPV6:
                    link_state_id = random.randint(0, conf.MAX_VALUE_16_BITS)
                    prefix_length = entry.prefix_length
                    inter_area_prefix_lsa = lsa.Lsa()
                    inter_area_prefix_lsa.create_header(
                        conf.INITIAL_LS_AGE, 0, conf.LSA_TYPE_INTER_AREA_PREFIX, link_state_id, router_id,
                        conf.INITIAL_SEQUENCE_NUMBER, version)
                    inter_area_prefix_lsa.create_inter_area_prefix_lsa_body(
                        metric, prefix_length, conf.PREFIX_OPTIONS, prefix)
                    lsa_list.append(inter_area_prefix_lsa)
                else:
                    raise ValueError("Invalid OSPF version")

        return lsa_list

    #  Updates inter-area LSA list for all LSDBs and floods required LSAs
    def update_inter_area_lsa_list(self):
        existing_inter_area_lsa_list = []
        for area_id in self.areas:
            if self.ospf_version == conf.VERSION_IPV4:
                for query_lsa in self.areas[area_id].database.summary_lsa_type_3_list:
                    existing_inter_area_lsa_list.append([query_lsa, area_id])
            elif self.ospf_version == conf.VERSION_IPV6:
                for query_lsa in self.areas[area_id].database.inter_area_prefix_lsa_list:
                    existing_inter_area_lsa_list.append([query_lsa, area_id])
        for area_id in self.areas:
            lsa_list = Router.get_inter_area_lsa_list_to_flood(
                self.routing_table, area_id, self.router_id, existing_inter_area_lsa_list, self.ospf_version)
            for query_lsa in lsa_list:
                self.areas[area_id].database.add_lsa(query_lsa, None)
                for interface_id in self.areas[area_id].interfaces:
                    query_interface = self.areas[area_id].interfaces[interface_id][area.INTERFACE_OBJECT]
                    query_interface.flooding_pipeline.put([query_lsa, self.router_id])
                    time.sleep(0.1)

    #  Given OSPF routing table, shortest path trees, router ID, existing extension LSDB, list of ABRs in router areas,
    #  list of prefixes in router areas and OSPF version, returns extension LSAs to flood and updated extension LSDB
    @staticmethod
    def get_extension_lsa_list_to_flood(
            table, shortest_path_tree_dictionary, router_id, extension_database, abr_list, prefix_list, version):
        lsa_list = []
        own_abr_lsa = extension_database.get_extension_lsa(conf.LSA_TYPE_EXTENSION_ABR_LSA, router_id)
        own_prefix_lsa = extension_database.get_extension_lsa(conf.LSA_TYPE_EXTENSION_PREFIX_LSA, router_id)

        #  Removing and updating ABR info
        if own_abr_lsa is not None:
            has_changed = False
            for abr_info in own_abr_lsa.body.abr_list:
                is_present = False
                abr = abr_info[1]
                advertised_metric = abr_info[0]
                new_metric = 0
                for shortest_path_tree in shortest_path_tree_dictionary:
                    for node in shortest_path_tree:
                        if node == abr:
                            is_present = True
                            new_metric = node[0]
                if not is_present:
                    own_abr_lsa.body.delete_abr_info(abr)
                    has_changed = True
                elif advertised_metric != new_metric:
                    own_abr_lsa.body.delete_abr_info(abr)
                    own_abr_lsa.add_abr_info(new_metric, abr)
                    has_changed = True
            if has_changed:
                if len(own_abr_lsa.pack_lsa()) == conf.LSA_HEADER_LENGTH:  # LSA no longer has content
                    own_abr_lsa.header.ls_age = conf.MAX_AGE
                else:
                    own_abr_lsa.header.ls_age = conf.INITIAL_LS_AGE
                    own_abr_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                        own_abr_lsa.header.ls_sequence_number)
                own_abr_lsa.set_lsa_length()
                own_abr_lsa.set_lsa_checksum()
                lsa_list.append(own_abr_lsa)
                extension_database.add_extension_lsa(own_abr_lsa)

        #  Removing and updating prefix info
        if own_prefix_lsa is not None:
            has_changed = False
            if version == conf.VERSION_IPV4:
                for subnet_info in own_prefix_lsa.body.subnet_list:
                    is_present = False
                    subnet_address = subnet_info[2]
                    netmask_length = utils.Utils.get_prefix_length_from_prefix(subnet_info[1])
                    advertised_metric = subnet_info[0]
                    new_metric = 0
                    for entry in table.entries:
                        if (entry.destination_id == subnet_address) & (entry.prefix_length == netmask_length):
                            is_present = True
                            new_metric = entry.paths[0].cost
                    if not is_present:
                        own_prefix_lsa.body.delete_subnet_info(netmask_length, subnet_address)
                        has_changed = True
                    elif advertised_metric != new_metric:
                        own_prefix_lsa.body.delete_subnet_info(netmask_length, subnet_address)
                        own_prefix_lsa.body.add_subnet_info(new_metric, netmask_length, subnet_address)
            elif version == conf.VERSION_IPV6:
                for prefix_info in own_prefix_lsa.body.prefix_list:
                    is_present = False
                    prefix = prefix_info[3]
                    prefix_length = prefix_info[1]
                    advertised_metric = prefix_info[0]
                    new_metric = 0
                    for entry in table.entries:
                        if (entry.destination_id == prefix) & (entry.prefix_length == prefix_length):
                            is_present = True
                            new_metric = entry.paths[0].cost
                    if not is_present:
                        own_prefix_lsa.body.delete_prefix_info(prefix_length, prefix)
                        has_changed = True
                    elif advertised_metric != new_metric:
                        own_prefix_lsa.body.delete_prefix_info(prefix_length, prefix)
                        own_prefix_lsa.body.add_prefix_info(new_metric, prefix_length, prefix)
            else:
                raise ValueError("Invalid OSPF version")
            if has_changed:
                if len(own_prefix_lsa.pack_lsa()) == conf.LSA_HEADER_LENGTH:  # LSA no longer has content
                    own_abr_lsa.header.ls_age = conf.MAX_AGE
                else:
                    own_prefix_lsa.header.ls_age = conf.INITIAL_LS_AGE
                    own_prefix_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                        own_prefix_lsa.header.ls_sequence_number)
                own_prefix_lsa.set_lsa_length()
                own_prefix_lsa.set_lsa_checksum()
                own_prefix_lsa.append(own_prefix_lsa)
                extension_database.add_extension_lsa(own_prefix_lsa)

        #  Adding ABR info
        for shortest_path_tree in shortest_path_tree_dictionary:
            for node in shortest_path_tree:
                if node in abr_list:
                    is_present = False
                    created_now = False
                    if own_abr_lsa is None:
                        own_abr_lsa = lsa.Lsa()
                        if version == conf.VERSION_IPV4:
                            own_abr_lsa.create_extension_header(
                                conf.INITIAL_LS_AGE, conf.OPTIONS, conf.OPAQUE_TYPE_ABR_LSA, conf.LSA_TYPE_OPAQUE_AS,
                                router_id, conf.INITIAL_SEQUENCE_NUMBER, version)
                        else:
                            own_abr_lsa.create_extension_header(
                                conf.INITIAL_LS_AGE, conf.OPTIONS, 0, conf.LSA_TYPE_EXTENSION_ABR_LSA, router_id,
                                conf.INITIAL_SEQUENCE_NUMBER, version)
                        own_abr_lsa.create_extension_abr_lsa_body()
                        created_now = True
                    else:
                        is_present = own_abr_lsa.has_abr_info(node)
                    if not is_present:
                        own_abr_lsa.header.ls_age = conf.INITIAL_LS_AGE
                        if not created_now:
                            own_abr_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                                own_abr_lsa.header.ls_sequence_number)
                        own_abr_lsa.set_lsa_length()
                        own_abr_lsa.set_lsa_checksum()
                        lsa_list.append(own_abr_lsa)
                        extension_database.add_extension_lsa(own_abr_lsa)

        #  Adding prefix info
        for shortest_path_tree in shortest_path_tree_dictionary:
            for node in shortest_path_tree:
                if node in prefix_list:
                    is_present = False
                    created_now = False
                    if own_prefix_lsa is None:
                        own_prefix_lsa = lsa.Lsa()
                        if version == conf.VERSION_IPV4:
                            own_prefix_lsa.create_extension_header(
                                conf.INITIAL_LS_AGE, conf.OPTIONS, conf.OPAQUE_TYPE_PREFIX_LSA, conf.LSA_TYPE_OPAQUE_AS,
                                router_id, conf.INITIAL_SEQUENCE_NUMBER, version)
                        else:
                            own_prefix_lsa.create_extension_header(
                                conf.INITIAL_LS_AGE, conf.OPTIONS, 0, conf.LSA_TYPE_EXTENSION_PREFIX_LSA, router_id,
                                conf.INITIAL_SEQUENCE_NUMBER, version)
                        own_prefix_lsa.create_extension_abr_lsa_body()
                        created_now = True
                    else:
                        is_present = own_prefix_lsa.has_abr_info(node)
                    if not is_present:
                        own_prefix_lsa.header.ls_age = conf.INITIAL_LS_AGE
                        if not created_now:
                            own_prefix_lsa.header.ls_sequence_number = lsa.Lsa.get_next_ls_sequence_number(
                                own_prefix_lsa.header.ls_sequence_number)
                        own_prefix_lsa.set_lsa_length()
                        own_prefix_lsa.set_lsa_checksum()
                        lsa_list.append(own_prefix_lsa)
                        extension_database.add_extension_lsa(own_prefix_lsa)

        return [lsa_list, extension_database]

    #  Updates extension LSA list and floods required LSAs
    def update_extension_lsa_list(self):
        existing_extension_lsa_list = self.extension_database.get_extension_lsdb()

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
