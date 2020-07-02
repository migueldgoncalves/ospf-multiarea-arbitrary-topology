import threading
import time

import conf.conf as conf
import lsa.lsa as lsa
import general.utils as utils

'''
This class represents the OSPF Link State Database and contains its data and operations
'''


class Lsdb:

    def __init__(self, version):
        self.router_lsa_list = []
        self.network_lsa_list = []
        self.intra_area_prefix_lsa_list = []  # Only for OSPFv3
        #  Link-LSAs are stored in the appropriate interface instance

        self.lsdb_lock = threading.RLock()
        self.version = version

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
            link_state_id = utils.Utils.decimal_to_ipv4(link_state_id)
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
            link_state_id = utils.Utils.decimal_to_ipv4(link_state_id)
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
