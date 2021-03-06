import threading
import time
import copy

import conf.conf as conf
import lsa.lsa as lsa
import lsa.header as header
import general.utils as utils

'''
This class represents the OSPF Link State Database and contains its data and operations
'''


class Lsdb:

    def __init__(self, version, area_id):
        self.router_lsa_list = []
        self.network_lsa_list = []
        self.summary_lsa_type_3_list = []  # Only for OSPFv2
        self.inter_area_prefix_lsa_list = []  # Only for OSPFv3
        self.intra_area_prefix_lsa_list = []  # Only for OSPFv3
        #  Link-LSAs are stored in the appropriate interface instance

        self.router_lock = threading.RLock()
        self.network_lock = threading.RLock()
        self.summary_lock = threading.RLock()
        self.inter_area_lock = threading.RLock()
        self.intra_area_lock = threading.RLock()
        self.time_lock = threading.RLock()
        self.version = version
        self.area_id = area_id
        self.is_modified = threading.Event()  # Set if LSDB was changed and change has not yet been processed
        self.modification_time = time.perf_counter()  # Current system time

        self.clean_lsdb([])
        self.is_modified.clear()

    #  Atomically returns full LSDB or part of it as a single list
    def get_lsdb(self, interfaces, identifiers):
        self.acquire_all_locks()
        lsa_list = []
        lsa_list.extend(self.router_lsa_list)
        lsa_list.extend(self.network_lsa_list)
        lsa_list.extend(self.summary_lsa_type_3_list)
        lsa_list.extend(self.inter_area_prefix_lsa_list)
        lsa_list.extend(self.intra_area_prefix_lsa_list)
        list_copy = copy.deepcopy(lsa_list)
        self.release_all_locks()
        for i in interfaces:
            list_copy.extend(i.get_link_local_lsa_list())
        requested_lsa_list = []
        for query_lsa in list_copy:
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
        flooding_scope = header.Header.get_s1_s2_bits(ls_type)
        u_bit = header.Header.get_u_bit(ls_type)
        ls_type = header.Header.get_ls_type(ls_type)  # Removes S1, S2 and U bits in OSPFv3 LS Type
        list_to_search = []
        if ls_type == conf.LSA_TYPE_ROUTER:
            self.router_lock.acquire()
            list_to_search = copy.deepcopy(self.router_lsa_list)
            self.router_lock.release()
        elif ls_type == conf.LSA_TYPE_NETWORK:
            self.network_lock.acquire()
            list_to_search = copy.deepcopy(self.network_lsa_list)
            self.network_lock.release()
        elif (ls_type == conf.LSA_TYPE_SUMMARY_TYPE_3) & (self.version == conf.VERSION_IPV4):
            self.summary_lock.acquire()
            list_to_search = copy.deepcopy(self.summary_lsa_type_3_list)
            self.summary_lock.release()
        elif (ls_type == conf.LSA_TYPE_INTER_AREA_PREFIX) & (self.version == conf.VERSION_IPV6):
            self.inter_area_lock.acquire()
            list_to_search = copy.deepcopy(self.inter_area_prefix_lsa_list)
            self.inter_area_lock.release()
        elif ls_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
            self.intra_area_lock.acquire()
            list_to_search = copy.deepcopy(self.intra_area_prefix_lsa_list)
            self.intra_area_lock.release()
        #  Link-local scope or unknown LSA types
        elif (flooding_scope == conf.LINK_LOCAL_SCOPING) | (
                (not lsa.Lsa.is_ls_type_valid(ls_type, self.version)) & (not u_bit)):
            for query_interface in interfaces:
                requested_lsa = query_interface.get_link_local_lsa(ls_type, link_state_id, advertising_router)
                if requested_lsa is not None:
                    return requested_lsa
        else:
            pass
        for query_lsa in list_to_search:
            if query_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                return query_lsa
        return None

    #  Atomically returns headers of full LSDB or part of it as a single list
    def get_lsa_headers(self, interfaces, identifiers):
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
        query_lsa = self.get_lsa(ls_type, link_state_id, advertising_router, interfaces)
        if query_lsa is not None:
            return query_lsa.header
        return None

    #  Atomically deletes a LSA from the LSDB, if present
    def delete_lsa(self, ls_type, link_state_id, advertising_router, interfaces):
        if not utils.Utils.is_ipv4_address(link_state_id):
            link_state_id = utils.Utils.decimal_to_ipv4(int(link_state_id))
        flooding_scope = header.Header.get_s1_s2_bits(ls_type)
        u_bit = header.Header.get_u_bit(ls_type)
        ls_type = header.Header.get_ls_type(ls_type)  # Removes S1, S2 and U bits in OSPFv3 LS Type
        list_to_search = []
        lock = None
        if ls_type == conf.LSA_TYPE_ROUTER:
            lock = self.router_lock
            lock.acquire()
            list_to_search = self.router_lsa_list
        elif ls_type == conf.LSA_TYPE_NETWORK:
            lock = self.network_lock
            lock.acquire()
            list_to_search = self.network_lsa_list
        elif (ls_type == conf.LSA_TYPE_SUMMARY_TYPE_3) & (self.version == conf.VERSION_IPV4):
            lock = self.summary_lock
            lock.acquire()
            list_to_search = self.summary_lsa_type_3_list
        elif (ls_type == conf.LSA_TYPE_INTER_AREA_PREFIX) & (self.version == conf.VERSION_IPV6):
            lock = self.inter_area_lock
            lock.acquire()
            list_to_search = self.inter_area_prefix_lsa_list
        elif ls_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
            lock = self.intra_area_lock
            lock.acquire()
            list_to_search = self.intra_area_prefix_lsa_list
        #  Link-local scope or unknown LSA types
        elif (flooding_scope == conf.LINK_LOCAL_SCOPING) | (
                (not lsa.Lsa.is_ls_type_valid(ls_type, self.version)) & (not u_bit)):
            for query_interface in interfaces:
                query_interface.delete_link_local_lsa(ls_type, link_state_id, advertising_router)
                self.lsdb_modified()
                return
        else:
            return
        for query_lsa in list_to_search:
            if query_lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                list_to_search.remove(query_lsa)
                self.lsdb_modified()
        lock.release()

    #  Atomically adds a LSA to the adequate list according to its type
    def add_lsa(self, lsa_to_add, interface):
        if interface is None:
            interfaces = []
        else:
            interfaces = [interface]

        lsa_to_add.installation_time = time.perf_counter()
        flooding_scope = header.Header.get_s1_s2_bits(lsa_to_add.header.ls_type)
        u_bit = header.Header.get_u_bit(lsa_to_add.header.ls_type)
        ls_type = lsa_to_add.get_lsa_type_from_lsa()
        list_to_search = []
        lock = None
        if ls_type == conf.LSA_TYPE_ROUTER:
            lock = self.router_lock
            lock.acquire()
            list_to_search = self.router_lsa_list
        elif ls_type == conf.LSA_TYPE_NETWORK:
            lock = self.network_lock
            lock.acquire()
            list_to_search = self.network_lsa_list
        elif (ls_type == conf.LSA_TYPE_SUMMARY_TYPE_3) & (self.version == conf.VERSION_IPV4):
            lock = self.summary_lock
            lock.acquire()
            list_to_search = self.summary_lsa_type_3_list
        elif (ls_type == conf.LSA_TYPE_INTER_AREA_PREFIX) & (self.version == conf.VERSION_IPV6):
            lock = self.inter_area_lock
            lock.acquire()
            list_to_search = self.inter_area_prefix_lsa_list
        elif ls_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
            lock = self.intra_area_lock
            lock.acquire()
            list_to_search = self.intra_area_prefix_lsa_list
        #  Link-local scope or unknown LSA types
        elif (flooding_scope == conf.LINK_LOCAL_SCOPING) | (
                (not lsa.Lsa.is_ls_type_valid(ls_type, self.version)) & (not u_bit)):
            for query_interface in interfaces:
                query_interface.add_link_local_lsa(lsa_to_add)
                self.lsdb_modified()
                return
        else:
            return

        #  Deletes previous instance of LSA, if present
        lsa_identifier = lsa_to_add.get_lsa_identifier()
        self.delete_lsa(lsa_identifier[0], lsa_identifier[1], lsa_identifier[2], interfaces)

        list_to_search.append(lsa_to_add)
        self.lsdb_modified()
        lock.release()

    def clean_lsdb(self, interfaces):
        self.acquire_all_locks()
        self.router_lsa_list = []
        self.network_lsa_list = []
        self.summary_lsa_type_3_list = []
        self.inter_area_prefix_lsa_list = []
        self.intra_area_prefix_lsa_list = []
        self.release_all_locks()
        for i in interfaces:
            i.clean_link_local_lsa_list()
        self.lsdb_modified()

    #  For each LSA, increases LS Age field if enough time has passed
    def increase_lsa_age(self, interfaces):
        with self.router_lock:
            for query_lsa in self.router_lsa_list:
                query_lsa.increase_lsa_age()
        with self.network_lock:
            for query_lsa in self.network_lsa_list:
                query_lsa.increase_lsa_age()
        with self.summary_lock:
            for query_lsa in self.summary_lsa_type_3_list:
                query_lsa.increase_lsa_age()
        with self.inter_area_lock:
            for query_lsa in self.inter_area_prefix_lsa_list:
                query_lsa.increase_lsa_age()
        with self.intra_area_lock:
            for query_lsa in self.intra_area_prefix_lsa_list:
                query_lsa.increase_lsa_age()
        for i in interfaces:
            i.increase_link_local_lsa_age()

    #  Signals router main thread of new LSDB modification
    def lsdb_modified(self):
        self.is_modified.set()
        self.reset_modification_time()

    #  Atomically resets modification time to current time
    def reset_modification_time(self):
        with self.time_lock:
            self.modification_time = time.perf_counter()

    #  Atomically returns value of modification time
    def get_modification_time(self):
        with self.time_lock:
            return self.modification_time

    #  Returns the area directed graph as a table
    def get_directed_graph(self):
        self.acquire_all_locks()
        database = copy.deepcopy(self)  # Ensures atomicity of operation
        self.release_all_locks()

        #  Graph initialization
        directed_graph = {}  # Dictionary of dictionaries - Each dictionary contains destinations for one graph node
        area_routers = []
        area_transit_networks = []
        for router_lsa in database.router_lsa_list:
            router_id = router_lsa.header.advertising_router
            area_routers.append(router_id)
            directed_graph[router_id] = {}
        for network_lsa in database.network_lsa_list:
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
                router_lsa_1 = database.get_lsa(conf.LSA_TYPE_ROUTER, router_id_1, router_id_1, [])
            else:
                router_lsa_1 = database.get_lsa(conf.LSA_TYPE_ROUTER, 0, router_id_1, [])
            for router_id_2 in area_routers:
                if router_id_1 == router_id_2:
                    continue
                elif self.version == conf.VERSION_IPV4:
                    router_lsa_2 = database.get_lsa(conf.LSA_TYPE_ROUTER, router_id_2, router_id_2, [])
                elif self.version == conf.VERSION_IPV6:
                    router_lsa_2 = database.get_lsa(conf.LSA_TYPE_ROUTER, 0, router_id_2, [])
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
                router_lsa = database.get_lsa(conf.LSA_TYPE_ROUTER, router_id, router_id, [])
            else:
                router_lsa = database.get_lsa(conf.LSA_TYPE_ROUTER, 0, router_id, [])
            for link_info in router_lsa.body.links:
                if self.version == conf.VERSION_IPV4:
                    if link_info[2] == conf.LINK_TO_TRANSIT_NETWORK:
                        for network_lsa in database.network_lsa_list:
                            dr_ip_address = network_lsa.header.link_state_id
                            if (link_info[0] == dr_ip_address) & (router_id in network_lsa.body.attached_routers):
                                network_id = network_lsa.header.link_state_id
                                directed_graph[router_id][network_id] = link_info[4]
                                directed_graph[network_id][router_id] = 0  # No cost going from network to router
                else:
                    if link_info[0] == conf.LINK_TO_TRANSIT_NETWORK:
                        neighbor_id = link_info[4]
                        for network_lsa in database.network_lsa_list:
                            if (network_lsa.header.advertising_router == neighbor_id) & (
                                    router_id in network_lsa.body.attached_routers):
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
                router_lsa = database.get_lsa(conf.LSA_TYPE_ROUTER, router_id, router_id, [])
                for link_info in router_lsa.body.links:
                    if link_info[2] in [conf.LINK_TO_STUB_NETWORK]:
                        if link_info[0] not in prefixes[router_id]:
                            prefixes[router_id].append(link_info[0])
            else:
                intra_area_prefix_lsa = database.get_lsa(conf.LSA_TYPE_INTRA_AREA_PREFIX, 0, router_id, [])
                if intra_area_prefix_lsa is not None:  # Prefixes associated to point-to-point or stub links
                    for prefix_info in intra_area_prefix_lsa.body.prefixes:
                        if prefix_info[3] not in prefixes[router_id]:
                            prefixes[router_id].append(prefix_info[3])
        for network_id in area_transit_networks:
            if self.version == conf.VERSION_IPV4:
                for network_lsa in database.network_lsa_list:
                    if network_lsa.header.link_state_id == network_id:
                        network_prefix = utils.Utils.ip_address_to_prefix(network_id, network_lsa.body.network_mask)
                        prefixes[network_id].append(network_prefix)
            else:
                dr_id = network_id.split("|")[0]
                dr_interface_id = network_id.split("|")[1]
                intra_area_prefix_lsa = None
                for query_lsa in database.intra_area_prefix_lsa_list:
                    if (query_lsa.header.advertising_router == dr_id) & (
                            query_lsa.body.referenced_link_state_id == utils.Utils.decimal_to_ipv4(dr_interface_id)):
                        intra_area_prefix_lsa = query_lsa
                if intra_area_prefix_lsa is not None:
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
                    cost = conf.INFINITE_COST  # Value larger than possible to store in 3 bytes
                nodes_to_analyse[destination] = [cost, source_router_id]

        while True:
            #  Finding closest node
            if len(nodes_to_analyse) == 0:
                return shortest_path_tree  # No further nodes to analyse - Shortest path tree completed
            shortest_cost = conf.INFINITE_COST
            closest_node = ''
            for node in nodes_to_analyse:
                if nodes_to_analyse[node][0] < shortest_cost:
                    shortest_cost = nodes_to_analyse[node][0]
                    closest_node = node
            if closest_node == '':  # All remaining nodes to analyse are in isolated network islands
                return shortest_path_tree
            shortest_path_tree[closest_node] = nodes_to_analyse[closest_node]
            nodes_to_analyse.pop(closest_node)

            #  Updating labels and parent nodes
            for destination in directed_graph[closest_node]:
                if destination not in shortest_path_tree:
                    potential_new_cost = shortest_path_tree[closest_node][0] + directed_graph[closest_node][destination]
                    if potential_new_cost < nodes_to_analyse[destination][0]:
                        nodes_to_analyse[destination][0] = potential_new_cost
                        nodes_to_analyse[destination][1] = closest_node

    def acquire_all_locks(self):
        self.router_lock.acquire()
        self.network_lock.acquire()
        self.summary_lock.acquire()
        self.intra_area_lock.acquire()
        self.inter_area_lock.acquire()

    def release_all_locks(self):
        self.router_lock.release()
        self.network_lock.release()
        self.summary_lock.release()
        self.intra_area_lock.release()
        self.inter_area_lock.release()

    def __deepcopy__(self, memodict=None):
        if memodict is None:
            memodict = {}
        lsdb_copy = Lsdb(self.version, self.area_id)
        self.acquire_all_locks()
        lsdb_copy.router_lsa_list = copy.deepcopy(self.router_lsa_list)
        lsdb_copy.network_lsa_list = copy.deepcopy(self.network_lsa_list)
        lsdb_copy.summary_lsa_type_3_list = copy.deepcopy(self.summary_lsa_type_3_list)
        lsdb_copy.inter_area_prefix_lsa_list = copy.deepcopy(self.inter_area_prefix_lsa_list)
        lsdb_copy.intra_area_prefix_lsa_list = copy.deepcopy(self.intra_area_prefix_lsa_list)
        self.release_all_locks()
        return lsdb_copy
