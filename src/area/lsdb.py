import threading
import time
import copy

import conf.conf as conf
import lsa.lsa as lsa
import general.utils as utils
import router.routing_table as routing_table

'''
This class represents the OSPF Link State Database and contains its data and operations
'''


class Lsdb:

    def __init__(self, version, area_id):
        self.router_lsa_list = []
        self.network_lsa_list = []
        self.intra_area_prefix_lsa_list = []  # Only for OSPFv3
        #  Link-LSAs are stored in the appropriate interface instance

        self.lsdb_lock = threading.RLock()
        self.version = version
        self.area_id = area_id

        self.clean_lsdb([])

    #  Atomically returns full LSDB or part of it as a single list
    def get_lsdb(self, interfaces, identifiers):
        with self.lsdb_lock:
            lsa_list = []
            lsa_list.extend(self.router_lsa_list)
            lsa_list.extend(self.network_lsa_list)
            lsa_list.extend(self.intra_area_prefix_lsa_list)
            for i in interfaces:
                lsa_list.extend(i.get_link_local_lsa_list())
            requested_lsa_list = []
            for query_lsa in lsa_list:
                #  If no identifier list is provided, all LSAs are returned
                if identifiers is None:
                    requested_lsa_list.append(query_lsa)
                elif query_lsa.get_lsa_identifier() in identifiers:
                    requested_lsa_list.append(query_lsa)
            return requested_lsa_list

    #  Atomically returns a LSA given its identifier, if present
    def get_lsa(self, ls_type, link_state_id, advertising_router, interfaces):
        if not utils.Utils.is_ipv4_address(link_state_id):
            link_state_id = utils.Utils.decimal_to_ipv4(int(link_state_id))
        with self.lsdb_lock:
            lsa_list = self.get_lsdb(interfaces, None)
            for query_lsa in lsa_list:
                if query_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    return query_lsa
            return None

    #  Atomically returns headers of full LSDB or part of it as a single list
    def get_lsa_headers(self, interfaces, identifiers):
        with self.lsdb_lock:
            lsa_list = self.get_lsdb(interfaces, None)
            lsa_headers = []
            for query_lsa in lsa_list:
                #  If no identifier list is provided, all LSA headers are returned
                if identifiers is None:
                    lsa_headers.append(query_lsa.header)
                elif query_lsa.get_lsa_identifier() in identifiers:
                    lsa_headers.append(query_lsa.header)
            return lsa_headers

    #  Atomically returns a LSA header given its identifier, if present
    def get_lsa_header(self, ls_type, link_state_id, advertising_router, interfaces):
        with self.lsdb_lock:
            query_lsa = self.get_lsa(ls_type, link_state_id, advertising_router, interfaces)
            if query_lsa is not None:
                return query_lsa.header
            return None

    #  Atomically deletes a LSA from the LSDB, if present
    def delete_lsa(self, ls_type, link_state_id, advertising_router, interfaces):
        if not utils.Utils.is_ipv4_address(link_state_id):
            link_state_id = utils.Utils.decimal_to_ipv4(int(link_state_id))
        with self.lsdb_lock:
            for query_lsa in self.router_lsa_list:
                if query_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    self.router_lsa_list.remove(query_lsa)
                    return
            for query_lsa in self.network_lsa_list:
                if query_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    self.network_lsa_list.remove(query_lsa)
                    return
            for query_lsa in self.intra_area_prefix_lsa_list:
                if query_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    self.intra_area_prefix_lsa_list.remove(query_lsa)
                    return
            for i in interfaces:
                i.delete_link_local_lsa(ls_type, link_state_id, advertising_router)

    #  Atomically adds a LSA to the adequate list according to its type
    def add_lsa(self, lsa_to_add, interface):
        with self.lsdb_lock:
            if interface is None:
                interfaces = []
            else:
                interfaces = [interface]
            #  Deletes previous instance of LSA, if present
            lsa_identifier = lsa_to_add.get_lsa_identifier()
            self.delete_lsa(lsa_identifier[0], lsa_identifier[1], lsa_identifier[2], interfaces)

            lsa_to_add.installation_time = time.perf_counter()
            flooding_scope = lsa_to_add.header.get_s1_s2_bits(lsa_to_add.header.ls_type)
            u_bit = lsa_to_add.header.get_u_bit(lsa_to_add.header.ls_type)
            ls_type = lsa_to_add.get_lsa_type_from_lsa()
            #  Known LSA types without link-local scope
            if ls_type == conf.LSA_TYPE_ROUTER:
                self.router_lsa_list.append(lsa_to_add)
            elif ls_type == conf.LSA_TYPE_NETWORK:
                self.network_lsa_list.append(lsa_to_add)
            elif ls_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
                self.intra_area_prefix_lsa_list.append(lsa_to_add)
            #  Link-local scope or unknown LSA types
            elif (flooding_scope == conf.LINK_LOCAL_SCOPING) | (
                    (not lsa.Lsa.is_ls_type_valid(ls_type, self.version)) & (not u_bit)):
                interface.add_link_local_lsa(lsa_to_add)
            else:
                pass

    def clean_lsdb(self, interfaces):
        with self.lsdb_lock:
            self.router_lsa_list = []
            self.network_lsa_list = []
            self.intra_area_prefix_lsa_list = []
            for i in interfaces:
                i.clean_link_local_lsa_list()

    #  For each LSA, increases LS Age field if enough time has passed
    def increase_lsa_age(self, interfaces):
        with self.lsdb_lock:
            lsa_list = self.get_lsdb(interfaces, None)
            for query_lsa in lsa_list:
                query_lsa.increase_lsa_age()

    #  Returns the area directed graph as a table
    def get_directed_graph(self, interfaces):
        #  Graph initialization
        directed_graph = {}  # Dictionary of dictionaries - Each dictionary contains destinations for one graph node
        area_routers = []
        area_transit_networks = []
        for router_lsa in self.router_lsa_list:
            router_id = router_lsa.header.advertising_router
            area_routers.append(router_id)
            directed_graph[router_id] = {}
        for network_lsa in self.network_lsa_list:
            if self.version == conf.VERSION_IPV4:
                network_id = network_lsa.header.link_state_id
            else:
                interface_id = utils.Utils.ipv4_to_decimal(network_lsa.header.link_state_id)
                network_id = network_lsa.header.advertising_router + "|" + str(interface_id)
            area_transit_networks.append(network_id)
            directed_graph[network_id] = {}

        #  Point-to-point links
        for router_id_1 in area_routers:
            if self.version == conf.VERSION_IPV4:
                router_lsa_1 = self.get_lsa(conf.LSA_TYPE_ROUTER, router_id_1, router_id_1, interfaces)
            else:
                router_lsa_1 = self.get_lsa(conf.LSA_TYPE_ROUTER, 0, router_id_1, interfaces)
            for router_id_2 in area_routers:
                if router_id_1 == router_id_2:
                    continue
                elif self.version == conf.VERSION_IPV4:
                    router_lsa_2 = self.get_lsa(conf.LSA_TYPE_ROUTER, router_id_2, router_id_2, interfaces)
                elif self.version == conf.VERSION_IPV6:
                    router_lsa_2 = self.get_lsa(conf.LSA_TYPE_ROUTER, 0, router_id_2, interfaces)
                else:
                    raise ValueError("Invalid OSPF version")
                for link_info_1 in router_lsa_1.body.links:
                    if self.version == conf.VERSION_IPV4:
                        if link_info_1[2] == conf.POINT_TO_POINT_LINK:
                            neighbor_router_id_1 = link_info_1[0]
                            for link_info_2 in router_lsa_2.body.links:
                                if link_info_2[2] == conf.POINT_TO_POINT_LINK:
                                    neighbor_router_id_2 = link_info_2[0]
                                    if (neighbor_router_id_1 == router_id_2) & (neighbor_router_id_2 == router_id_1):
                                        directed_graph[router_id_1][router_id_2] = link_info_1[4]
                                        directed_graph[router_id_2][router_id_1] = link_info_2[4]
                    else:
                        if link_info_1[0] == conf.POINT_TO_POINT_LINK:
                            neighbor_id_1 = link_info_1[4]
                            for link_info_2 in router_lsa_2.body.links:
                                if link_info_2[0] == conf.POINT_TO_POINT_LINK:
                                    neighbor_id_2 = link_info_2[4]
                                    if (neighbor_id_1 == router_lsa_2.header.advertising_router) & (
                                            neighbor_id_2 == router_lsa_1.header.advertising_router):
                                        directed_graph[router_id_1][router_id_2] = link_info_1[1]
                                        directed_graph[router_id_2][router_id_1] = link_info_2[1]

        #  Transit shared links
        for router_id in area_routers:
            if self.version == conf.VERSION_IPV4:
                router_lsa = self.get_lsa(conf.LSA_TYPE_ROUTER, router_id, router_id, interfaces)
            else:
                router_lsa = self.get_lsa(conf.LSA_TYPE_ROUTER, 0, router_id, interfaces)
            for link_info in router_lsa.body.links:
                if self.version == conf.VERSION_IPV4:
                    if link_info[2] == conf.LINK_TO_TRANSIT_NETWORK:
                        for network_lsa in self.network_lsa_list:
                            dr_ip_address = network_lsa.header.link_state_id
                            if link_info[0] == dr_ip_address:
                                network_id = network_lsa.header.link_state_id
                                directed_graph[router_id][network_id] = link_info[4]
                                directed_graph[network_id][router_id] = 0  # No cost going from network to router
                else:
                    if link_info[0] == conf.LINK_TO_TRANSIT_NETWORK:
                        neighbor_id = link_info[4]
                        for network_lsa in self.network_lsa_list:
                            if network_lsa.header.advertising_router == neighbor_id:
                                network_id = neighbor_id + "|" + str(utils.Utils.ipv4_to_decimal(
                                    network_lsa.header.link_state_id))
                                directed_graph[router_id][network_id] = link_info[1]
                                directed_graph[network_id][router_id] = 0

        #  Address prefixes
        prefixes = {}
        for router_id in area_routers:
            prefixes[router_id] = []
        for network_id in area_transit_networks:
            prefixes[network_id] = []
        for router_id in area_routers:
            if self.version == conf.VERSION_IPV4:
                router_lsa = self.get_lsa(conf.LSA_TYPE_ROUTER, router_id, router_id, interfaces)
                for link_info in router_lsa.body.links:
                    if link_info[2] in [conf.LINK_TO_STUB_NETWORK]:
                        if link_info[0] not in prefixes[router_id]:
                            prefixes[router_id].append(link_info[0])
            else:
                intra_area_prefix_lsa = self.get_lsa(conf.LSA_TYPE_INTRA_AREA_PREFIX, 0, router_id, interfaces)
                if intra_area_prefix_lsa is not None:  # Prefixes associated to point-to-point or stub links
                    for prefix_info in intra_area_prefix_lsa.body.prefixes:
                        if prefix_info[3] not in prefixes[router_id]:
                            prefixes[router_id].append(prefix_info[3])
        for network_id in area_transit_networks:
            if self.version == conf.VERSION_IPV4:
                for network_lsa in self.network_lsa_list:
                    if network_lsa.header.link_state_id == network_id:
                        network_prefix = utils.Utils.ip_address_to_prefix(
                            network_id, network_lsa.body.network_mask)
                        prefixes[network_id].append(network_prefix)
            else:
                dr_id = network_id.split("|")[0]
                dr_interface_id = network_id.split("|")[1]
                intra_area_prefix_lsa = self.get_lsa(
                    conf.LSA_TYPE_INTRA_AREA_PREFIX, dr_interface_id, dr_id, interfaces)
                for prefix_info in intra_area_prefix_lsa.body.prefixes:
                    prefixes[network_id].append(prefix_info[3])

        return [directed_graph, prefixes]

    #  Returns the shortest path tree for the area by running the Dijkstra algorithm
    def get_shortest_path_tree(self, directed_graph, root_router_id, prefixes, interfaces):
        #  1st step - Dijkstra algorithm

        new_routing_table = routing_table.RoutingTable()
        root_router_lsa = self.get_lsa(conf.LSA_TYPE_ROUTER, root_router_id, root_router_id, interfaces)
        shortest_path_tree = {root_router_id: [0, root_router_lsa, []]}
        newest_vertex = root_router_id  # Last vertex added to shortest path tree
        candidate_list = {}
        first_iteration = True
        while (len(candidate_list) > 0) | first_iteration:
            first_iteration = False
            newest_vertex_lsa = self.get_lsa(conf.LSA_TYPE_ROUTER, newest_vertex, newest_vertex, interfaces)
            if newest_vertex_lsa is None:  # Newest vertex in shortest path tree is transit network
                for network_lsa in self.network_lsa_list:
                    if network_lsa.header.link_state_id == newest_vertex:
                        newest_vertex_lsa = network_lsa
            for next_vertex in directed_graph[newest_vertex]:
                if next_vertex in shortest_path_tree:
                    continue
                cost = shortest_path_tree[newest_vertex][0] + directed_graph[newest_vertex][next_vertex]
                next_hop = self.get_next_hop(next_vertex, newest_vertex, root_router_id, directed_graph,
                                             shortest_path_tree, prefixes, interfaces)
                if next_vertex in candidate_list:
                    if cost > candidate_list[next_vertex][0]:
                        continue  # Not the shortest path
                    elif cost == candidate_list[next_vertex]:
                        candidate_list[next_vertex][2].append(next_hop)
                    else:
                        candidate_list[newest_vertex] = [cost, newest_vertex_lsa, next_hop]
                if next_vertex not in candidate_list:
                    candidate_list[newest_vertex] = [cost, newest_vertex_lsa, next_hop]

            if len(candidate_list) == 0:
                break  # First stage completed
            else:
                min_cost = conf.MAX_VALUE_32_BITS
                for candidate_node in candidate_list:
                    if candidate_node[0] < min_cost:
                        min_cost = candidate_node[0]
                min_cost_network_node = False
                for candidate_node in candidate_list:
                    #  Network nodes must be chosen before router nodes if having minimal cost
                    if (type(candidate_list[candidate_node][1].body).__name__ == 'Network') & (
                            candidate_list[candidate_node][0] == min_cost):
                        shortest_path_tree[candidate_node] = candidate_list[candidate_node]
                        candidate_list.pop(candidate_node)
                        min_cost_network_node = True
                        break
                if not min_cost_network_node:
                    for candidate_node in candidate_list:
                        if candidate_list[candidate_node][0] == min_cost:
                            shortest_path_tree[candidate_node] = candidate_list[candidate_node]
                            candidate_list.pop(candidate_node)
                            break

            if type(newest_vertex_lsa.body).__name__ == 'Network':  # Vertex is a transit network
                subnet_address = utils.Utils.ip_address_to_prefix(
                    newest_vertex_lsa.header.link_state_id, newest_vertex_lsa.body.network_mask)
                routing_table_entry = new_routing_table.get_entry(
                    conf.DESTINATION_TYPE_NETWORK, subnet_address, self.area_id)
                if routing_table_entry is not None:
                    if shortest_path_tree[newest_vertex][0] <= routing_table_entry.paths[0].cost:
                        new_routing_table.delete_entry(conf.DESTINATION_TYPE_NETWORK, subnet_address, self.area_id)
                new_routing_table.add_entry(conf.DESTINATION_TYPE_NETWORK, subnet_address,
                                            newest_vertex_lsa.body.network_mask, 0, self.area_id)
                routing_table_entry = new_routing_table.get_entry(
                    conf.DESTINATION_TYPE_NETWORK, subnet_address, self.area_id)
                next_hop_list = shortest_path_tree[newest_vertex][2]
                for next_hop in next_hop_list:
                    routing_table_entry.add_path(
                        conf.INTRA_AREA_PATH, shortest_path_tree[newest_vertex][0], 0, next_hop, '')

        #  2nd step - Adding stub networks to the shortest path tree

        for vertex in shortest_path_tree:
            if type(shortest_path_tree[vertex][1].body).__name__ == 'Router':  # Vertex is a router
                router_lsa = self.get_lsa(conf.LSA_TYPE_ROUTER, vertex, vertex, interfaces)
                for link_info in router_lsa.body.links:  # Point-to-point links and stub networks
                    if link_info[2] == conf.LINK_TO_STUB_NETWORK:
                        cost = shortest_path_tree[vertex][0] + link_info[4]
                        subnet_address = link_info[0]
                        routing_table_entry = new_routing_table.get_entry(
                            conf.DESTINATION_TYPE_NETWORK, subnet_address, self.area_id)
                        next_hop_list = self.get_next_hop(vertex, subnet_address, root_router_id, directed_graph,
                                                          shortest_path_tree, prefixes, interfaces)
                        if routing_table_entry is not None:
                            if cost > routing_table_entry.paths[0].cost:
                                continue  # New cost is higher than already known cost
                            elif cost == routing_table_entry.paths[0].cost:
                                #  New next hops are added to the already known next hops
                                for next_hop in next_hop_list:
                                    #  Next hop contains outgoing IP address and, if any, next hop IP address
                                    routing_table_entry.add_path(conf.INTRA_AREA_PATH, cost, 0, next_hop, '')
                                continue
                            else:
                                new_routing_table.delete_entry(
                                    conf.DESTINATION_TYPE_NETWORK, subnet_address, self.area_id)
                        new_routing_table.add_entry(conf.DESTINATION_TYPE_NETWORK, subnet_address, link_info[1], 0,
                                                    self.area_id)
                        routing_table_entry = new_routing_table.get_entry(
                            conf.DESTINATION_TYPE_NETWORK, subnet_address, self.area_id)
                        for next_hop in next_hop_list:
                            routing_table_entry.add_path(conf.INTRA_AREA_PATH, cost, 0, next_hop, '')

        return new_routing_table

    #  Returns outgoing interface and next hop IP address to reach a destination in the network from this router (root)
    #  Parent node and destination node must be in the same link
    def get_next_hop(self, parent_node_id, destination_node_id, root_router_id, directed_graph, shortest_path_tree,
                     prefixes, interfaces):
        next_hop_list = []
        #  Root connected by point-to-point link OR destination is network connected to root
        if (destination_node_id in directed_graph[root_router_id]) | (destination_node_id in prefixes[root_router_id]):
            for link_info in self.get_lsa(conf.LSA_TYPE_ROUTER, root_router_id, root_router_id, interfaces).body.links:
                link_id = link_info[0]
                outgoing_interface = ''
                if link_info[2] in [conf.POINT_TO_POINT_LINK, conf.LINK_TO_TRANSIT_NETWORK]:
                    outgoing_interface = link_info[1]
                else:  # Stub network
                    for interface in interfaces:
                        if utils.Utils.ip_address_to_prefix(interface.ipv4_address, interface.network_mask) == link_id:
                            outgoing_interface = interface.ipv4_address
                if link_id == destination_node_id:
                    next_hop_list.append([outgoing_interface, ''])
        #  Root and destination in same transit link
        elif (root_router_id in directed_graph[parent_node_id]) & (
                destination_node_id in directed_graph[parent_node_id]):
            for network_lsa in self.network_lsa_list:
                if parent_node_id == network_lsa.header.link_state_id:  # Parent node is transit link
                    for link_info in self.get_lsa(
                            conf.LSA_TYPE_ROUTER, destination_node_id, destination_node_id, interfaces).body.links:
                        link_id = link_info[0]
                        link_data = link_info[1]
                        if link_id == parent_node_id:
                            destination_ip_address = link_data
                            for next_hop in copy.deepcopy(shortest_path_tree[parent_node_id][2]):
                                next_hop[1] = destination_ip_address
                                next_hop_list.append(next_hop)
        #  Root and destination in different links
        else:
            for next_hop in shortest_path_tree[parent_node_id][2]:
                next_hop_list.append(next_hop)
        return next_hop_list
