import threading

import conf.conf as conf

'''
This class represents the OSPF Link State Database and contains its data and operations
'''


class Lsdb:

    def __init__(self):
        self.router_lsa_list = []
        self.network_lsa_list = []
        self.intra_area_prefix_lsa_list = []  # Only for OSPFv3
        #  Link-LSAs are stored in the appropriate interface instance

        self.lsdb_lock = threading.RLock()

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
            for lsa in lsa_list:
                #  If no identifier list is provided, all LSAs are returned
                if identifiers is None:
                    requested_lsa_list.append(lsa)
                elif lsa.get_lsa_identifier() in identifiers:
                    requested_lsa_list.append(lsa)
            return requested_lsa_list

    #  Atomically returns a LSA given its identifier, if present
    def get_lsa(self, ls_type, link_state_id, advertising_router, interfaces):
        with self.lsdb_lock:
            lsa_list = self.get_lsdb(interfaces, None)
            for lsa in lsa_list:
                if lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    return lsa
            return None

    #  Atomically returns headers of full LSDB or part of it as a single list
    def get_lsa_headers(self, interfaces, identifiers):
        with self.lsdb_lock:
            lsa_list = self.get_lsdb(interfaces, None)
            lsa_headers = []
            for lsa in lsa_list:
                #  If no identifier list is provided, all LSA headers are returned
                if identifiers is None:
                    lsa_headers.append(lsa.header)
                elif lsa.get_lsa_identifier() in identifiers:
                    lsa_headers.append(lsa.header)
            return lsa_headers

    #  Atomically returns a LSA header given its identifier, if present
    def get_lsa_header(self, ls_type, link_state_id, advertising_router, interfaces):
        with self.lsdb_lock:
            lsa = self.get_lsa(ls_type, link_state_id, advertising_router, interfaces)
            if lsa is not None:
                return lsa.header
            return None

    #  Atomically deletes a LSA from the LSDB, if present
    def delete_lsa(self, ls_type, link_state_id, advertising_router, interfaces):
        with self.lsdb_lock:
            for lsa in self.router_lsa_list:
                if lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    self.router_lsa_list.remove(lsa)
                    return
            for lsa in self.network_lsa_list:
                if lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    self.network_lsa_list.remove(lsa)
                    return
            for lsa in self.intra_area_prefix_lsa_list:
                if lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                    self.intra_area_prefix_lsa_list.remove(lsa)
                    return
            for i in interfaces:
                i.delete_link_local_lsa(ls_type, link_state_id, advertising_router)

    #  Atomically adds a LSA to the adequate list according to its type
    def add_lsa(self, lsa):
        with self.lsdb_lock:
            #  Deletes previous instance of LSA, if present
            lsa_identifier = lsa.get_lsa_identifier()
            self.delete_lsa(lsa_identifier[0], lsa_identifier[1], lsa_identifier[2], [])

            ls_type = lsa.get_lsa_type_from_lsa()
            if ls_type == conf.LSA_TYPE_ROUTER:
                self.router_lsa_list.append(lsa)
            elif ls_type == conf.LSA_TYPE_NETWORK:
                self.network_lsa_list.append(lsa)
            elif ls_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
                self.intra_area_prefix_lsa_list.append(lsa)
            #  Link-LSAs are added by the interface instance directly to itself
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
            for lsa in lsa_list:
                lsa.increase_lsa_age()
