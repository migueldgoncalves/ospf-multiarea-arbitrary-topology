import threading
import time
import copy

import conf.conf as conf
import area.lsdb as lsdb
import lsa.header as header

'''
This class represents the Link State Database for the OSPF extension and contains its data and operations
'''


class ExtensionLsdb:

    def __init__(self, version):
        self.abr_lsa_list = []
        self.prefix_lsa_list = []
        self.asbr_lsa_list = []

        self.lsdb_lock = threading.RLock()
        self.abr_lock = threading.RLock()
        self.prefix_lock = threading.RLock()
        self.asbr_lock = threading.RLock()
        self.time_lock = threading.RLock()
        if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
            raise ValueError("Invalid OSPF version")
        self.version = version
        self.is_modified = threading.Event()  # Set if LSDB was changed and change has not yet been processed
        self.modification_time = time.perf_counter()  # Current system time

        self.clean_extension_lsdb()
        self.is_modified.clear()

    #  Atomically returns full extension LSDB or part of it as a list
    def get_extension_lsdb(self, identifiers):
        self.acquire_all_locks()
        lsa_list = []
        lsa_list.extend(self.abr_lsa_list)
        lsa_list.extend(self.prefix_lsa_list)
        lsa_list.extend(self.asbr_lsa_list)
        list_copy = copy.deepcopy(lsa_list)
        self.release_all_locks()
        requested_lsa_list = []
        for query_lsa in list_copy:
            #  If no identifier list is provided, all LSAs are returned
            if identifiers is None:
                requested_lsa_list.append(query_lsa)
            elif query_lsa.get_lsa_identifier() in identifiers:
                requested_lsa_list.append(query_lsa)
        return requested_lsa_list

    #  Atomically returns an extension LSA given its identifier, if present
    def get_extension_lsa(self, ls_type, opaque_type, advertising_router):
        if self.version == conf.VERSION_IPV4:
            ls_type = conf.LSA_TYPE_OPAQUE_AS
        else:
            ls_type = header.Header.get_ls_type(ls_type)  # Removes S1, S2 and U bits
        list_to_search = []
        if ((self.version == conf.VERSION_IPV4) & (opaque_type == conf.OPAQUE_TYPE_ABR_LSA)) | (
                (self.version == conf.VERSION_IPV6) & (ls_type == conf.LSA_TYPE_EXTENSION_ABR_LSA)):
            self.abr_lock.acquire()
            list_to_search = copy.deepcopy(self.abr_lsa_list)
            self.abr_lock.release()
        elif ((self.version == conf.VERSION_IPV4) & (opaque_type == conf.OPAQUE_TYPE_PREFIX_LSA)) | (
                (self.version == conf.VERSION_IPV6) & (ls_type == conf.LSA_TYPE_EXTENSION_PREFIX_LSA)):
            self.abr_lock.acquire()
            list_to_search = copy.deepcopy(self.prefix_lsa_list)
            self.abr_lock.release()
        elif ((self.version == conf.VERSION_IPV4) & (opaque_type == conf.OPAQUE_TYPE_ASBR_LSA)) | (
                (self.version == conf.VERSION_IPV6) & (ls_type == conf.LSA_TYPE_EXTENSION_ASBR_LSA)):
            self.abr_lock.acquire()
            list_to_search = copy.deepcopy(self.asbr_lsa_list)
            self.abr_lock.release()
        else:
            pass
        for query_lsa in list_to_search:
            if query_lsa.is_extension_lsa_identifier_equal(ls_type, opaque_type, advertising_router):
                return query_lsa
        return None

    #  Atomically returns headers of full extension LSDB
    def get_extension_lsa_headers(self, identifiers):
        lsa_list = self.get_extension_lsdb(identifiers)
        lsa_headers = []
        for query_lsa in lsa_list:
            #  If no identifier list is provided, all LSA headers are returned
            if identifiers is None:
                lsa_headers.append(query_lsa.header)
            elif query_lsa.get_lsa_identifier() in identifiers:
                lsa_headers.append(query_lsa.header)
        return lsa_headers

    #  Atomically returns an extension LSA header given its identifier, if present
    def get_extension_lsa_header(self, ls_type, opaque_type, advertising_router):
        query_lsa = self.get_extension_lsa(ls_type, opaque_type, advertising_router)
        if query_lsa is not None:
            return query_lsa.header
        return None

    #  Atomically deletes an extension LSA from the LSDB, if present
    def delete_extension_lsa(self, ls_type, opaque_type, advertising_router):
        if self.version == conf.VERSION_IPV4:
            ls_type = conf.LSA_TYPE_OPAQUE_AS
        else:
            ls_type = header.Header.get_ls_type(ls_type)  # Removes S1, S2 and U bits
        if ((self.version == conf.VERSION_IPV4) & (opaque_type == conf.OPAQUE_TYPE_ABR_LSA)) | (
                (self.version == conf.VERSION_IPV6) & (ls_type == conf.LSA_TYPE_EXTENSION_ABR_LSA)):
            lock = self.abr_lock
            lock.acquire()
            list_to_search = self.abr_lsa_list
        elif ((self.version == conf.VERSION_IPV4) & (opaque_type == conf.OPAQUE_TYPE_PREFIX_LSA)) | (
                (self.version == conf.VERSION_IPV6) & (ls_type == conf.LSA_TYPE_EXTENSION_PREFIX_LSA)):
            lock = self.prefix_lock
            lock.acquire()
            list_to_search = self.prefix_lsa_list
        elif ((self.version == conf.VERSION_IPV4) & (opaque_type == conf.OPAQUE_TYPE_ASBR_LSA)) | (
                (self.version == conf.VERSION_IPV6) & (ls_type == conf.LSA_TYPE_EXTENSION_ASBR_LSA)):
            lock = self.asbr_lock
            lock.acquire()
            list_to_search = self.asbr_lsa_list
        else:
            return
        for query_lsa in list_to_search:
            if query_lsa.is_extension_lsa_identifier_equal(ls_type, opaque_type, advertising_router):
                list_to_search.remove(query_lsa)
                self.extension_lsdb_modified()
        lock.release()

    #  Atomically adds an extension LSA to the adequate list according to its type
    def add_extension_lsa(self, lsa_to_add):
        lsa_to_add.installation_time = time.perf_counter()
        ls_type = lsa_to_add.get_lsa_type_from_lsa()
        opaque_type = lsa_to_add.header.get_opaque_type(lsa_to_add.header.link_state_id)
        if ((self.version == conf.VERSION_IPV4) & (ls_type == conf.LSA_TYPE_OPAQUE_AS) & (
                opaque_type == conf.OPAQUE_TYPE_ABR_LSA)) | ((self.version == conf.VERSION_IPV6) & (
                ls_type == conf.LSA_TYPE_EXTENSION_ABR_LSA)):
            lock = self.abr_lock
            lock.acquire()
            list_to_search = self.abr_lsa_list
        elif ((self.version == conf.VERSION_IPV4) & (ls_type == conf.LSA_TYPE_OPAQUE_AS) & (
                opaque_type == conf.OPAQUE_TYPE_PREFIX_LSA)) | ((self.version == conf.VERSION_IPV6) & (
                ls_type == conf.LSA_TYPE_EXTENSION_PREFIX_LSA)):
            lock = self.prefix_lock
            lock.acquire()
            list_to_search = self.prefix_lsa_list
        elif ((self.version == conf.VERSION_IPV4) & (ls_type == conf.LSA_TYPE_OPAQUE_AS) & (
                opaque_type == conf.OPAQUE_TYPE_ASBR_LSA)) | ((self.version == conf.VERSION_IPV6) & (
                ls_type == conf.LSA_TYPE_EXTENSION_ASBR_LSA)):
            lock = self.asbr_lock
            lock.acquire()
            list_to_search = self.asbr_lsa_list
        else:
            return

        #  Deletes previous instance of LSA, if present
        self.delete_extension_lsa(ls_type, opaque_type, lsa_to_add.header.advertising_router)

        list_to_search.append(lsa_to_add)
        self.extension_lsdb_modified()
        lock.release()

    def clean_extension_lsdb(self):
        self.acquire_all_locks()
        self.abr_lsa_list = []
        self.prefix_lsa_list = []
        self.asbr_lsa_list = []
        self.release_all_locks()
        self.extension_lsdb_modified()

    #  For each extension LSA, increases LS Age field if enough time has passed
    def increase_lsa_age(self):
        with self.abr_lock:
            for query_lsa in self.abr_lsa_list:
                query_lsa.increase_lsa_age()
        with self.prefix_lock:
            for query_lsa in self.prefix_lsa_list:
                query_lsa.increase_lsa_age()
        with self.asbr_lock:
            for query_lsa in self.asbr_lsa_list:
                query_lsa.increase_lsa_age()

    #  Signals router main thread of new extension LSDB modification
    def extension_lsdb_modified(self):
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

    #  Returns the overlay directed graph as a table
    def get_overlay_directed_graph(self):
        self.abr_lock.acquire()
        abr_lsa_list = copy.deepcopy(self.abr_lsa_list)
        self.abr_lock.release()
        self.prefix_lock.acquire()
        prefix_lsa_list = copy.deepcopy(self.prefix_lsa_list)
        self.prefix_lock.release()

        #  Graph initialization
        directed_graph = {}  # Dictionary of dictionaries - Each dictionary contains destinations for one graph node
        for query_lsa in abr_lsa_list:  # Each ABR creates one extension LSA of each type, at most
            directed_graph[query_lsa.header.advertising_router] = {}
            for neighbor_abr in query_lsa.body.abr_list:
                metric = neighbor_abr[0]
                neighbor_id = neighbor_abr[1]
                directed_graph[query_lsa.header.advertising_router][neighbor_id] = metric

        #  Address prefixes
        prefixes = {}
        for query_lsa in prefix_lsa_list:
            prefixes[query_lsa.header.advertising_router] = []
            if self.version == conf.VERSION_IPV4:
                for subnet_info in query_lsa.body.subnet_list:
                    subnet_address = subnet_info[2]
                    prefixes[query_lsa.header.advertising_router].append(subnet_address)
            elif self.version == conf.VERSION_IPV6:
                for prefix_info in query_lsa.body.prefix_list:
                    address_prefix = prefix_info[3]
                    prefixes[query_lsa.header.advertising_router].append(address_prefix)

        return [directed_graph, prefixes]

    #  Returns the shortest path tree for the overlay by running the Dijkstra algorithm
    @staticmethod
    def get_shortest_path_tree(directed_graph, source_router_id):
        lsdb.Lsdb.get_shortest_path_tree(directed_graph, source_router_id)

    def acquire_all_locks(self):
        self.abr_lock.acquire()
        self.prefix_lock.acquire()
        self.asbr_lock.acquire()

    def release_all_locks(self):
        self.abr_lock.release()
        self.prefix_lock.release()
        self.asbr_lock.release()

    def __deepcopy__(self, memodict=None):
        if memodict is None:
            memodict = {}
        lsdb_copy = ExtensionLsdb(self.version)
        self.acquire_all_locks()
        lsdb_copy.abr_lsa_list = copy.deepcopy(self.abr_lsa_list)
        lsdb_copy.prefix_lsa_list = copy.deepcopy(self.prefix_lsa_list)
        lsdb_copy.asbr_lsa_type_3_list = copy.deepcopy(self.asbr_lsa_list)
        self.release_all_locks()
        return lsdb_copy
