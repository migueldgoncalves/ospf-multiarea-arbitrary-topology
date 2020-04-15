import struct

import lsa.header as header
import lsa.router as router
import lsa.network as network
import lsa.intra_area_prefix as intra_area_prefix
import lsa.link as link
import conf.conf as conf
import general.utils as utils

'''
This class serves as an interface to LSA creation, storage and manipulation, both for OSPFv2 and OSPFv3
'''


class Lsa:
    header = None
    body = None

    #  #  #  #  #  #  #
    #  Main methods   #
    #  #  #  #  #  #  #

    #  Adds an OSPF header to the LSA with the provided arguments
    def create_header(self, ls_age, options, ls_type, link_state_id, advertising_router, ls_sequence_number, version):
        self.header = header.Header(
            ls_age, options, ls_type, link_state_id, advertising_router, ls_sequence_number, version)
        self.body = None

    #  Converts an OSPF LSA into a byte stream
    def pack_lsa(self):
        if self.header is None:
            raise ValueError("LSA header is not set")
        if self.body is None:
            raise ValueError("LSA body is not set")

        header_bytes = self.header.pack_header()
        body_bytes = self.body.pack_lsa_body()
        return header_bytes + body_bytes

    #  Converts a byte stream into an OSPF LSA
    @staticmethod
    def unpack_lsa(lsa_bytes, lsa_version):
        lsa_type = Lsa.get_ospf_lsa_type(lsa_bytes)

        #  An OSPF LSA just with a header, or with less bytes, can immediately be discarded
        if len(lsa_bytes) <= conf.LSA_HEADER_LENGTH:
            raise ValueError("LSA byte stream is too short")

        lsa = Lsa()
        header_bytes = lsa_bytes[:conf.LSA_HEADER_LENGTH]
        body_bytes = lsa_bytes[conf.LSA_HEADER_LENGTH:]

        #  Creates the header and the body of the LSA from their byte streams
        lsa.header = header.Header.unpack_header(header_bytes, lsa_version)
        if lsa_type == conf.LSA_TYPE_ROUTER:
            lsa.body = router.Router.unpack_lsa_body(body_bytes, lsa_version)
        elif lsa_type == conf.LSA_TYPE_NETWORK:
            lsa.body = network.Network.unpack_lsa_body(body_bytes, lsa_version)
        elif (lsa_type == conf.LSA_TYPE_INTRA_AREA_PREFIX) & (lsa_version == conf.VERSION_IPV6):
            lsa.body = intra_area_prefix.IntraAreaPrefix.unpack_lsa_body(body_bytes, 0)
        elif (lsa_type == conf.LSA_TYPE_LINK) & (lsa_version == conf.VERSION_IPV6):
            lsa.body = link.Link.unpack_lsa_body(body_bytes, 0)
        else:
            pass

        return lsa

    #  Adds an OSPF Router-LSA body to the LSA with the provided arguments
    def create_router_lsa_body(self, bit_v, bit_e, bit_b, options, version):
        self.body = router.Router(bit_v, bit_e, bit_b, options, version)
        self.set_lsa_length()  # LSA length must be set after body is created and before checksum is computed
        self.set_lsa_checksum()

    #  Adds an OSPF Network-LSA body to the LSA with the provided arguments
    def create_network_lsa_body(self, network_mask, options, attached_routers, version):
        self.body = network.Network(network_mask, options, attached_routers, version)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds an OSPF Intra-Area-Prefix-LSA body to the LSA with the provided arguments
    def create_intra_area_prefix_lsa_body(
            self, referenced_ls_type, referenced_link_state_id, referenced_advertising_router):
        self.body = intra_area_prefix.IntraAreaPrefix(
            referenced_ls_type, referenced_link_state_id, referenced_advertising_router)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds an OSPF Link-LSA body to the LSA with the provided arguments
    def create_link_lsa_body(self, router_priority, options, link_local_address):
        self.body = link.Link(router_priority, options, link_local_address)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  #  #  #  #  #  #   #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #   #

    #  Calculates LSA checksum and inserts it on LSA header
    def set_lsa_checksum(self):
        if self.body is not None:  # Does nothing if there is no LSA body
            self.header.ls_checksum = 0

            #  Calculates and sets LSA checksum
            header_bytes = self.header.pack_header()[2:]  # Without the LS Age field
            body_bytes = self.body.pack_lsa_body()
            self.header.ls_checksum = utils.Utils.create_checksum_ospfv2(header_bytes + body_bytes)

    #  Calculates LSA length and inserts it on given LSA header
    def set_lsa_length(self):
        if self.body is not None:
            header_bytes = self.header.pack_header()
            body_bytes = self.body.pack_lsa_body()
            self.header.length = len(header_bytes + body_bytes)

    #  Given a LSA byte stream, returns its OSPF LSA type
    @staticmethod
    def get_ospf_lsa_type(lsa_bytes):
        lsa_type_byte = lsa_bytes[2:3]  # Third byte of OSPF LSA is always its type
        lsa_type = struct.unpack("> B", lsa_type_byte)[0]
        return lsa_type
