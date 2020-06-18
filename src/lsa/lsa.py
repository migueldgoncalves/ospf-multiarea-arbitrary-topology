import struct
import time

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

    def __init__(self):
        self.header = None
        self.body = None

        self.system_time = time.perf_counter()  # Current system time in seconds
        self.installation_time = time.perf_counter()  # Time of installation in LSDB

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

    #  Converts an OSPF LSA header into a byte stream
    def pack_header(self):
        if self.header is None:
            raise ValueError("LSA header is not set")
        header_bytes = self.header.pack_header()
        return header_bytes

    #  Converts a byte stream into an OSPF LSA
    @staticmethod
    def unpack_lsa(lsa_bytes, lsa_version):
        lsa_type = Lsa.get_lsa_type_from_bytes(lsa_bytes)

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

    #  Converts a byte stream into an OSPF LSA header
    @staticmethod
    def unpack_header(lsa_bytes, lsa_version):
        if len(lsa_bytes) < conf.LSA_HEADER_LENGTH:
            raise ValueError("LSA byte stream is too short")
        lsa = Lsa()
        header_bytes = lsa_bytes[:conf.LSA_HEADER_LENGTH]
        lsa.header = header.Header.unpack_header(header_bytes, lsa_version)
        return lsa

    #  Adds an OSPF Router-LSA body to the LSA with the provided arguments
    def create_router_lsa_body(self, bit_v, bit_e, bit_b, options, version):
        self.body = router.Router(bit_v, bit_e, bit_b, options, version)
        self.set_lsa_length()  # LSA length must be set after body is created and before checksum is computed
        self.set_lsa_checksum()

    #  Adds data for one link (interface) to the OSPFv2 Router-LSA body
    def add_link_info_v2(self, link_id, link_data, link_type, tos_number, metric):
        self.body.add_link_info_v2(link_id, link_data, link_type, tos_number, metric)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds data for one link (interface) to the OSPFv3 Router-LSA body
    def add_link_info_v3(self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id):
        self.body.add_link_info_v3(link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds an OSPF Network-LSA body to the LSA with the provided arguments
    def create_network_lsa_body(self, network_mask, options, attached_routers, version):
        self.body = network.Network(network_mask, options, attached_routers, version)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds an OSPF Intra-Area-Prefix-LSA body to the LSA with the provided arguments
    def create_intra_area_prefix_lsa_body(
            self, referenced_ls_type, referenced_link_state_id, referenced_advertising_router):
        if (self.get_ospf_version() == conf.VERSION_IPV6) & (referenced_ls_type != conf.LSA_TYPE_LINK) & (
                referenced_ls_type < 0x2000):
            referenced_ls_type += 0x2000
        self.body = intra_area_prefix.IntraAreaPrefix(
            referenced_ls_type, referenced_link_state_id, referenced_advertising_router)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds an OSPF Link-LSA body to the LSA with the provided arguments
    def create_link_lsa_body(self, router_priority, options, link_local_address):
        self.body = link.Link(router_priority, options, link_local_address)
        #  Link-LSAs have link local scope - LS Type field remains unchanged
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds data for one prefix to the Intra-Area-Prefix-LSA and Link-LSA bodies
    def add_prefix_info(self, prefix_length, prefix_options, metric, prefix, lsa_type):
        if lsa_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
            self.body.add_prefix_info(prefix_length, prefix_options, metric, prefix)
        else:  # Link-LSA
            self.body.add_prefix_info(prefix_length, prefix_options, prefix)
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
            self.header.ls_checksum = utils.Utils.create_fletcher_checksum(header_bytes + body_bytes)

    #  Returns True is LSA checksum is valid
    def is_lsa_checksum_valid(self):
        if self.body is None:
            return False
        header_bytes = self.header.pack_header()[2:]  # Without the LS Age field
        body_bytes = self.body.pack_lsa_body()
        checksum = utils.Utils.create_fletcher_checksum(header_bytes + body_bytes)
        return checksum == 0  # Checksum of LSA with valid checksum will always be 0

    #  Calculates LSA length and inserts it on given LSA header
    def set_lsa_length(self):
        if self.body is not None:
            header_bytes = self.header.pack_header()
            body_bytes = self.body.pack_lsa_body()
            self.header.length = len(header_bytes + body_bytes)

    #  Given a LSA byte stream, returns its OSPF LSA type
    @staticmethod
    def get_lsa_type_from_bytes(lsa_bytes):
        lsa_type_byte = lsa_bytes[3:4]  # Forth byte of OSPF LSA is always its type
        lsa_type = struct.unpack("> B", lsa_type_byte)[0]
        return lsa_type

    #  Returns type of current LSA, without flooding scope if any
    def get_lsa_type_from_lsa(self):
        return self.header.get_ls_type(self.header.ls_type)

    #  Returns identifier of current LSA
    def get_lsa_identifier(self):
        return self.header.get_lsa_identifier()

    #  Returns True if LSA identifier matches current LSA
    def is_lsa_identifier_equal(self, ls_type, link_state_id, advertising_router):
        lsa_identifier = self.get_lsa_identifier()
        return (ls_type == lsa_identifier[0]) & (link_state_id == lsa_identifier[1]) & \
               (advertising_router == lsa_identifier[2])

    #  Increases LS Age field, if enough time has passed
    def increase_lsa_age(self):
        if self.header.ls_age < conf.MAX_AGE:
            self.header.ls_age += int(time.perf_counter() - self.system_time)
            if self.header.ls_age > conf.MAX_AGE:
                self.header.ls_age = conf.MAX_AGE
        self.system_time = int(time.perf_counter())

    #  Sets LS Age to 3600
    def set_ls_age_max(self):
        self.header.ls_age = 3600
        self.system_time = int(time.perf_counter())

    def get_ospf_version(self):
        return self.header.ospf_version

    # Given a bite stream with LSAs, returns the length of the first LSA
    @staticmethod
    def get_lsa_length(lsa_bytes):
        lsa_length_byte = lsa_bytes[18:20]  # 19th and 20th bytes of OSPF LSA are always its length
        lsa_length = struct.unpack("> H", lsa_length_byte)[0]
        return lsa_length

    #  Given 2 instances of LSAs, states which of them is fresher or if both have same freshness
    @staticmethod
    def get_fresher_lsa(first, second):
        if (first is None) & (second is None):
            raise ValueError("LSA cannot be None")
        elif first is None:
            return header.SECOND
        elif second is None:
            return header.FIRST
        else:
            return header.Header.get_fresher_lsa_header(first.header, second.header)

    #  Returns True if provided LS Type is valid for provided OSPF version - Includes Opaque-LSAs for OSPFv2
    @staticmethod
    def is_ls_type_valid(ls_type, version):
        if version == conf.VERSION_IPV4:
            return ls_type in [conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK, conf.LSA_TYPE_SUMMARY_TYPE_3,
                               conf.LSA_TYPE_SUMMARY_TYPE_4, conf.LSA_TYPE_AS_EXTERNAL, conf.LSA_TYPE_OPAQUE_LINK_LOCAL,
                               conf.LSA_TYPE_OPAQUE_AREA, conf.LSA_TYPE_OPAQUE_AS]
        elif version == conf.VERSION_IPV6:
            s1_s2_bits = header.Header.get_s1_s2_bits(ls_type)
            ls_type = header.Header.get_ls_type(ls_type)
            return (ls_type in [conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK, conf.LSA_TYPE_INTER_AREA_PREFIX,
                                conf.LSA_TYPE_INTER_AREA_ROUTER, conf.LSA_TYPE_AS_EXTERNAL, conf.LSA_TYPE_LINK,
                                conf.LSA_TYPE_INTRA_AREA_PREFIX]) & (
                    s1_s2_bits in [conf.LINK_LOCAL_SCOPING, conf.AREA_SCOPING, conf.AS_SCOPING])
        else:
            return False
