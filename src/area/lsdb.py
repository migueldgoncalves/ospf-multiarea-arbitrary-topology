import conf.conf as conf

'''
This class represents the OSPF Link State Database stored in the area layer and contains its data and operations
'''


class Lsdb:
    router_lsa_list = []
    network_lsa_list = []
    intra_area_prefix_lsa_list = []  # Only for OSPFv3
    #  Link-LSAs are stored in the appropriate interface instance

    def __init__(self):
        self.clean_lsdb()

    #  Adds a LSA to the adequate list according to its type
    def add_lsa(self, lsa):
        ls_type = lsa.get_lsa_type_from_lsa()
        if ls_type == conf.LSA_TYPE_ROUTER:
            self.router_lsa_list.append(lsa)
        elif ls_type == conf.LSA_TYPE_NETWORK:
            self.network_lsa_list.append(lsa)
        elif ls_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
            self.intra_area_prefix_lsa_list.append(lsa)
        else:
            pass

    #  Returns a LSA given its identifier, if present
    def get_lsa(self, ls_type, link_state_id, advertising_router):
        if ls_type == conf.LSA_TYPE_ROUTER:
            list_to_search = self.router_lsa_list
        elif ls_type == conf.LSA_TYPE_NETWORK:
            list_to_search = self.network_lsa_list
        elif ls_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
            list_to_search = self.intra_area_prefix_lsa_list
        else:
            return None

        for lsa in list_to_search:
            if lsa.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router):
                return lsa
        return None

    #  Returns list of LSA headers
    def get_lsa_headers(self):
        lsa_headers = []
        for lsa in self.router_lsa_list:
            lsa_headers.append(lsa.header)
        for lsa in self.network_lsa_list:
            lsa_headers.append(lsa.header)
        for lsa in self.intra_area_prefix_lsa_list:
            lsa_headers.append(lsa.header)
        #  TODO: Implement fetching of Link-LSAs

    def clean_lsdb(self):
        self.router_lsa_list = []
        self.network_lsa_list = []
        self.intra_area_prefix_lsa_list = []
