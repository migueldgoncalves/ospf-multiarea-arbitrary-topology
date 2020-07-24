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
    @staticmethod
    def get_shortest_path_tree(directed_graph, source_router_id):
        #  Initialization
        shortest_path_tree = {source_router_id: [0, source_router_id]}
        nodes_to_analyse = {}
        for destination in directed_graph:
            if destination != source_router_id:
                if directed_graph[source_router_id].get(destination) is not None:
                    cost = directed_graph[source_router_id][destination]  # Source directly connected to destination
                else:
                    cost = conf.MAX_VALUE_16_BITS  # Replacement for infinite cost - Infinite has no value in OSPF
                nodes_to_analyse[destination] = [cost, source_router_id]

        while True:
            #  Finding closest node
            if len(nodes_to_analyse) == 0:
                return shortest_path_tree  # No further nodes to analyse - Shortest path tree completed
            shortest_cost = conf.MAX_VALUE_16_BITS
            closest_node = ''
            for node in nodes_to_analyse:
                if nodes_to_analyse[node][0] < shortest_cost:
                    shortest_cost = nodes_to_analyse[node][0]
                    closest_node = node
            shortest_path_tree[closest_node] = nodes_to_analyse[closest_node]
            nodes_to_analyse.pop(closest_node)

            #  Updating labels and parent nodes
            for destination in directed_graph[closest_node]:
                if destination not in shortest_path_tree:
                    potential_new_cost = shortest_path_tree[closest_node][0] + directed_graph[closest_node][destination]
                    if potential_new_cost < nodes_to_analyse[destination][0]:
                        nodes_to_analyse[destination][0] = potential_new_cost
                        nodes_to_analyse[destination][1] = closest_node
