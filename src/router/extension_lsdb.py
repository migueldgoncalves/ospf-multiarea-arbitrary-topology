import threading
import time

import conf.conf as conf

'''
This class represents the Link State Database for the OSPF extension and contains its data and operations
'''


class ExtensionLsdb:

    def __init__(self, version):
        self.abr_lsa_list = []
        self.prefix_lsa_list = []
        self.asbr_lsa_list = []

        self.lsdb_lock = threading.RLock()
        self.version = version
        self.is_modified = threading.Event()  # Set if LSDB was changed and change has not yet been processed
        self.modification_time = time.perf_counter()  # Current system time

        self.clean_extension_lsdb()
        self.is_modified.clear()

    #  Atomically returns full extension LSDB or part of it as a single list
    def get_extension_lsdb(self):
        with self.lsdb_lock:
            lsa_list = []
            lsa_list.extend(self.abr_lsa_list)
            lsa_list.extend(self.prefix_lsa_list)
            lsa_list.extend(self.asbr_lsa_list)
            return lsa_list

    #  Atomically returns an extension LSA given its identifier, if present
    def get_extension_lsa(self, ls_type, advertising_router):
        with self.lsdb_lock:
            lsa_list = self.get_extension_lsdb()
            for query_lsa in lsa_list:
                if query_lsa.is_lsa_identifier_equal(ls_type, '0.0.0.0', advertising_router):
                    return query_lsa
            return None

    #  Atomically returns headers of full extension LSDB or part of it as a single list
    def get_extension_lsa_headers(self):
        with self.lsdb_lock:
            lsa_list = self.get_extension_lsdb()
            lsa_headers = []
            for query_lsa in lsa_list:
                lsa_headers.append(query_lsa.header)
            return lsa_headers

    #  Atomically returns an extension LSA header given its identifier, if present
    def get_extension_lsa_header(self, ls_type, advertising_router):
        with self.lsdb_lock:
            query_lsa = self.get_extension_lsa(ls_type, advertising_router)
            if query_lsa is not None:
                return query_lsa.header
            return None

    #  Atomically deletes an extension LSA from the LSDB, if present
    def delete_extension_lsa(self, ls_type, advertising_router):
        with self.lsdb_lock:
            for lsa_list in [self.abr_lsa_list, self.prefix_lsa_list, self.asbr_lsa_list]:
                for query_lsa in lsa_list:
                    if query_lsa.is_lsa_identifier_equal(ls_type, '0.0.0.0', advertising_router):
                        lsa_list.remove(query_lsa)
                        self.extension_lsdb_modified()
                        return

    #  Atomically adds an extension LSA to the adequate list according to its type
    def add_extension_lsa(self, lsa_to_add):
        with self.lsdb_lock:
            #  Deletes previous instance of LSA, if present
            lsa_identifier = lsa_to_add.get_lsa_identifier()
            self.delete_extension_lsa(lsa_identifier[0], lsa_identifier[2])

            lsa_to_add.installation_time = time.perf_counter()
            ls_type = lsa_to_add.get_lsa_type_from_lsa()
            if ls_type == conf.LSA_TYPE_EXTENSION_ABR_LSA:
                self.abr_lsa_list.append(lsa_to_add)
                self.extension_lsdb_modified()
            elif ls_type == conf.LSA_TYPE_EXTENSION_PREFIX_LSA:
                self.prefix_lsa_list.append(lsa_to_add)
                self.extension_lsdb_modified()
            elif ls_type == conf.LSA_TYPE_EXTENSION_ASBR_LSA:
                self.asbr_lsa_list.append(lsa_to_add)
                self.extension_lsdb_modified()
            else:
                pass

    def clean_extension_lsdb(self):
        with self.lsdb_lock:
            self.abr_lsa_list = []
            self.prefix_lsa_list = []
            self.asbr_lsa_list = []
            self.is_modified.set()

    #  For each extension LSA, increases LS Age field if enough time has passed
    def increase_lsa_age(self):
        with self.lsdb_lock:
            lsa_list = self.get_extension_lsdb()
            for query_lsa in lsa_list:
                query_lsa.increase_lsa_age()

    #  Signals router main thread of new extension LSDB modification
    def extension_lsdb_modified(self):
        self.is_modified.set()
        self.reset_modification_time()

    #  Atomically resets modification time to current time
    def reset_modification_time(self):
        with self.lsdb_lock:
            self.modification_time = time.perf_counter()

    #  Atomically returns value of modification time
    def get_modification_time(self):
        with self.lsdb_lock:
            return self.modification_time

    #  Returns the overlay directed graph as a table
    def get_overlay_directed_graph(self):
        #  Graph initialization
        directed_graph = {}  # Dictionary of dictionaries - Each dictionary contains destinations for one graph node
        for query_lsa in self.abr_lsa_list:  # Each ABR creates one extension LSA of each type, at most
            directed_graph[query_lsa.advertising_router] = {}
            for neighbor_abr in query_lsa.abr_list:
                metric = neighbor_abr[0]
                neighbor_id = neighbor_abr[1]
                directed_graph[query_lsa.advertising_router][neighbor_id] = metric

        #  Address prefixes
        prefixes = {}
        for query_lsa in self.prefix_lsa_list:
            prefixes[query_lsa.advertising_router] = []
            if self.version == conf.VERSION_IPV4:
                for subnet_info in query_lsa.subnet_list:
                    subnet_address = subnet_info[2]
                    prefixes[query_lsa.advertising_router].append(subnet_address)
            elif self.version == conf.VERSION_IPV6:
                for prefix_info in query_lsa.prefix_list:
                    address_prefix = prefix_info[3]
                    prefixes[query_lsa.advertising_router].append(address_prefix)

        return [directed_graph, prefixes]

    #  Returns the shortest path tree for the overlay by running the Dijkstra algorithm
    @staticmethod
    def get_shortest_path_tree(directed_graph, source_router_id):
        #  Initialization
        infinite = conf.MAX_VALUE_24_BITS + 1  # Replacement for infinite cost - Infinite has no value in OSPF
        shortest_path_tree = {source_router_id: [0, source_router_id]}
        nodes_to_analyse = {}
        for destination in directed_graph:
            if destination != source_router_id:
                if directed_graph[source_router_id].get(destination) is not None:
                    cost = directed_graph[source_router_id][destination]  # Source directly connected to destination
                else:
                    cost = infinite
                nodes_to_analyse[destination] = [cost, source_router_id]

        while True:
            #  Finding closest node
            if len(nodes_to_analyse) == 0:
                return shortest_path_tree  # No further nodes to analyse - Shortest path tree completed
            shortest_cost = infinite
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
