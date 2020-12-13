import struct
import time

import lsa.header as header
import lsa.router as router
import lsa.network as network
import lsa.intra_area_prefix as intra_area_prefix
import lsa.link as link
import lsa.summary as summary
import lsa.inter_area_prefix as inter_area_prefix
import lsa.extension_abr as extension_abr
import lsa.extension_prefix as extension_prefix
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
    #  Main methods  #
    #  #  #  #  #  #  #

    #  Adds an OSPF header to the LSA with the provided arguments
    def create_header(self, ls_age, options, ls_type, link_state_id, advertising_router, ls_sequence_number, version):
        self.header = header.Header(
            ls_age, options, ls_type, link_state_id, advertising_router, ls_sequence_number, version)
        self.body = None

    #  Adds an header to the LSA of the OSPF extension with the provided arguments
    def create_extension_header(
            self, ls_age, options, opaque_type, ls_type, advertising_router, ls_sequence_number, version):
        if version == conf.VERSION_IPV4:
            if opaque_type not in [conf.OPAQUE_TYPE_ABR_LSA, conf.OPAQUE_TYPE_PREFIX_LSA, conf.OPAQUE_TYPE_ASBR_LSA]:
                raise ValueError("Invalid Opaque Type")
            ls_type = conf.LSA_TYPE_OPAQUE_AS
            opaque_id = 0  # Each router creates at most one Extension LSA of each type
            link_state_id = (opaque_type << 3 * conf.BYTE_SIZE) + opaque_id
        elif version == conf.VERSION_IPV6:
            if ls_type not in [conf.LSA_TYPE_EXTENSION_ABR_LSA, conf.LSA_TYPE_EXTENSION_PREFIX_LSA,
                               conf.LSA_TYPE_EXTENSION_ASBR_LSA]:
                raise ValueError("Invalid LS Type")
            u_bit = 1  # LSA is stored and flooded as if LS Type was known
            s1_s2_bits = conf.AS_SCOPING
            ls_type = (u_bit << 15) + (s1_s2_bits << 13) + ls_type
            link_state_id = 0
        else:
            raise ValueError("Invalid OSPF version")
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
        elif (lsa_type in [conf.LSA_TYPE_SUMMARY_TYPE_3, conf.LSA_TYPE_SUMMARY_TYPE_4]) & (
                lsa_version == conf.VERSION_IPV4):
            lsa.body = summary.Summary.unpack_lsa_body(body_bytes, 0)
        elif (lsa_type == conf.LSA_TYPE_INTER_AREA_PREFIX) & (lsa_version == conf.VERSION_IPV6):
            lsa.body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(body_bytes, 0)
        elif (lsa_type == conf.LSA_TYPE_OPAQUE_AS) & (lsa_version == conf.VERSION_IPV4):
            opaque_type = Lsa.get_opaque_type_from_bytes(lsa_bytes)
            if opaque_type == conf.OPAQUE_TYPE_ABR_LSA:
                lsa.body = extension_abr.ExtensionAbr.unpack_lsa_body(body_bytes, 0)
            elif opaque_type == conf.OPAQUE_TYPE_PREFIX_LSA:
                lsa.body = extension_prefix.ExtensionPrefix.unpack_lsa_body(body_bytes, lsa_version)
            else:
                pass
        elif (lsa_type == conf.LSA_TYPE_EXTENSION_ABR_LSA) & (lsa_version == conf.VERSION_IPV6):
            lsa.body = extension_abr.ExtensionAbr.unpack_lsa_body(body_bytes, 0)
        elif (lsa_type == conf.LSA_TYPE_EXTENSION_PREFIX_LSA) & (lsa_version == conf.VERSION_IPV6):
            lsa.body = extension_prefix.ExtensionPrefix.unpack_lsa_body(body_bytes, lsa_version)
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

    #  Router-LSA

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

    def has_link_info_v2(self, link_id, link_data, link_type, tos_number, metric):
        return [link_id, link_data, link_type, tos_number, metric] in self.body.links

    def has_link_info_v3(self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id):
        return [link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id] in self.body.links

    #  Deletes all link information produced by provided interface in Router-LSA
    def delete_interface_link_info(self, interface_ip, subnet_ip, interface_id):
        self.body.delete_interface_link_info(interface_ip, subnet_ip, interface_id)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Deletes data for one link from the OSPFv2 LSA body
    def delete_link_info_v2(self, link_id, link_data, link_type, tos_number, metric):
        self.body.delete_link_info_v2(link_id, link_data, link_type, tos_number, metric)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Deletes data for one link from the OSPFv3 LSA body
    def delete_link_info_v3(self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id):
        self.body.delete_link_info_v3(link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Network-LSA

    #  Adds an OSPF Network-LSA body to the LSA with the provided arguments
    def create_network_lsa_body(self, network_mask, options, attached_routers, version):
        self.body = network.Network(network_mask, options, attached_routers, version)
        self.set_lsa_length()
        self.set_lsa_checksum()

    def add_attached_router(self, router_id):
        self.body.add_attached_router(router_id)
        self.set_lsa_length()
        self.set_lsa_checksum()

    def delete_attached_router(self, router_id):
        self.body.delete_attached_router(router_id)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Intra-Area-Prefix-LSA and Link-LSA

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
        elif lsa_type == conf.LSA_TYPE_LINK:
            self.body.add_prefix_info(prefix_length, prefix_options, prefix)
        else:
            raise ValueError("LSA Type must be Intra-Area-Prefix or Link for this method")
        self.set_lsa_length()
        self.set_lsa_checksum()

    def has_prefix_info(self, prefix_length, prefix_options, metric, prefix, lsa_type):
        if lsa_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
            return self.body.has_prefix_info(prefix_length, prefix_options, metric, prefix)
        elif lsa_type == conf.LSA_TYPE_LINK:
            return self.body.has_prefix_info(prefix_length, prefix_options, prefix)
        else:
            raise ValueError("LSA Type must be Intra-Area-Prefix or Link for this method")

    #  Deletes data for one prefix from the Intra-Area-Prefix-LSA and Link-LSA body
    def delete_prefix_info(self, prefix_length, prefix_options, metric, prefix, lsa_type):
        if lsa_type == conf.LSA_TYPE_INTRA_AREA_PREFIX:
            self.body.delete_prefix_info(prefix_length, prefix_options, metric, prefix)
        elif lsa_type == conf.LSA_TYPE_LINK:
            self.body.delete_prefix_info(prefix_length, prefix_options, prefix)
        else:
            raise ValueError("LSA Type must be Intra-Area-Prefix or Link for this method")
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Summary-LSA

    #  Adds an OSPFv2 Summary-LSA body to the LSA with the provided arguments
    def create_summary_lsa_body(self, network_mask, metric):
        self.body = summary.Summary(network_mask, metric)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Inter-Area-Prefix-LSA

    #  Adds an OSPF Inter-Area-Prefix-LSA body to the LSA with the provided arguments
    def create_inter_area_prefix_lsa_body(self, metric, prefix_length, prefix_options, address_prefix):
        self.body = inter_area_prefix.InterAreaPrefix(metric, prefix_length, prefix_options, address_prefix)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  ABR-LSA of the OSPF extension

    #  Adds a ABR-LSA body to the LSA with the provided arguments
    def create_extension_abr_lsa_body(self):
        self.body = extension_abr.ExtensionAbr()
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds data for one ABR to the ABR-LSA body
    def add_abr_info(self, metric, neighbor_router_id):
        self.body.add_abr_info(metric, neighbor_router_id)
        self.set_lsa_length()
        self.set_lsa_checksum()

    def has_abr_info(self, neighbor_router_id):
        return self.body.has_abr_info(neighbor_router_id)

    def get_abr_info(self, neighbor_router_id):
        return self.body.get_abr_info(neighbor_router_id)

    #  Deletes data for one ABR from the ABR-LSA body
    def delete_abr_info(self, neighbor_router_id):
        self.body.delete_abr_info(neighbor_router_id)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Prefix-LSA of the OSPF extension

    #  Adds a Prefix-LSA body to the LSA with the provided arguments
    def create_extension_prefix_lsa_body(self, version):
        self.body = extension_prefix.ExtensionPrefix(version)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds data for one subnet to the OSPFv2 Prefix-LSA body
    def add_subnet_info(self, metric, subnet_mask, subnet_address):
        self.body.add_subnet_info(metric, subnet_mask, subnet_address)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Adds data for one prefix to the OSPFv3 Prefix-LSA body
    def add_prefix_info_extension(self, metric, prefix_length, prefix_options, address_prefix):
        self.body.add_prefix_info(metric, prefix_length, prefix_options, address_prefix)
        self.set_lsa_length()
        self.set_lsa_checksum()

    def has_subnet_info(self, subnet_mask, subnet_address):
        return self.body.has_subnet_info(subnet_mask, subnet_address)

    def has_prefix_info_extension(self, prefix_length, address_prefix):
        return self.body.has_prefix_info(prefix_length, address_prefix)

    def get_subnet_info(self, subnet_mask, subnet_address):
        return self.body.get_subnet_info(subnet_mask, subnet_address)

    def get_prefix_info_extension(self, prefix_length, address_prefix):
        return self.body.get_prefix_info(prefix_length, address_prefix)

    #  Deletes data for one subnet from the OSPFv2 Prefix-LSA body
    def delete_subnet_info(self, subnet_mask, subnet_address):
        self.body.delete_subnet_info(subnet_mask, subnet_address)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  Deletes data for one prefix from the OSPFv3 Prefix-LSA body
    def delete_prefix_info_extension(self, prefix_length, address_prefix):
        self.body.delete_prefix_info_extension(prefix_length, address_prefix)
        self.set_lsa_length()
        self.set_lsa_checksum()

    #  #  #  #  #  #  #  #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #  #

    #  Calculates LSA checksum and inserts it on LSA header
    def set_lsa_checksum(self):
        if self.body is not None:  # Does nothing if there is no LSA body
            self.header.ls_checksum = 0

            #  Calculates and sets LSA checksum
            header_bytes = self.header.pack_header()[2:]  # Without the LS Age field
            body_bytes = self.body.pack_lsa_body()
            self.header.ls_checksum = utils.Utils.create_fletcher_checksum(header_bytes + body_bytes)

    #  Returns True if LSA checksum is valid
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

    #  Given a Opaque-LSA byte stream, returns its OSPF Opaque Type
    @staticmethod
    def get_opaque_type_from_bytes(lsa_bytes):
        opaque_type_byte = lsa_bytes[4:5]  # Fifth byte of OSPFv2 Opaque-LSA is always its Opaque Type
        opaque_type = struct.unpack("> B", opaque_type_byte)[0]
        return opaque_type

    #  Returns OSPF Opaque Type of current LSA
    def get_opaque_type(self):
        if self.get_ospf_version() != conf.VERSION_IPV4:
            return 0
        return header.Header.get_opaque_type(self.header.link_state_id)

    #  Returns type of current LSA, without flooding scope if any
    def get_lsa_type_from_lsa(self):
        return self.header.get_ls_type(self.header.ls_type)

    #  Returns identifier of current LSA
    def get_lsa_identifier(self):
        return self.header.get_lsa_identifier()

    #  Returns True if LSA identifier matches current LSA
    def is_lsa_identifier_equal(self, ls_type, link_state_id, advertising_router):
        lsa_identifier = self.get_lsa_identifier()
        return (self.header.get_ls_type(ls_type) == self.header.get_ls_type(lsa_identifier[0])) & \
               (link_state_id == lsa_identifier[1]) & (advertising_router == lsa_identifier[2])

    #  Returns True if extension LSA identifier matches current LSA
    def is_extension_lsa_identifier_equal(self, ls_type, opaque_type, advertising_router):
        if self.get_ospf_version() == conf.VERSION_IPV4:
            link_state_id = utils.Utils.decimal_to_ipv4(opaque_type << 3 * conf.BYTE_SIZE)
        else:
            link_state_id = conf.DEFAULT_LINK_STATE_ID
        return self.is_lsa_identifier_equal(ls_type, link_state_id, advertising_router)

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

    def is_lsa_self_originated(self, router_id):
        return router_id == self.header.advertising_router

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

    #  Returns True if provided LS Type is valid for provided OSPF version - Includes LSAs of the OSPF extension
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
                                conf.LSA_TYPE_INTRA_AREA_PREFIX, conf.LSA_TYPE_EXTENSION_ABR_LSA,
                                conf.LSA_TYPE_EXTENSION_PREFIX_LSA, conf.LSA_TYPE_EXTENSION_ASBR_LSA]) & (
                           s1_s2_bits in [conf.LINK_LOCAL_SCOPING, conf.AREA_SCOPING, conf.AS_SCOPING])
        else:
            return False

    #  Returns True if provided LSA is part of the OSPF extension
    def is_extension_lsa(self):
        if self.get_ospf_version() == conf.VERSION_IPV4:
            if self.get_lsa_type_from_lsa() == conf.LSA_TYPE_OPAQUE_AS:
                if self.get_opaque_type_from_bytes(self.pack_lsa()) in [
                        conf.OPAQUE_TYPE_ABR_LSA, conf.OPAQUE_TYPE_PREFIX_LSA, conf.OPAQUE_TYPE_ASBR_LSA]:
                    return True
        elif self.get_ospf_version() == conf.VERSION_IPV6:
            if self.get_lsa_type_from_lsa() in [conf.LSA_TYPE_EXTENSION_ABR_LSA, conf.LSA_TYPE_EXTENSION_PREFIX_LSA,
                                                conf.LSA_TYPE_EXTENSION_ASBR_LSA]:
                return True
        return False

    #  Returns True if provided Opaque Type is being used in the OSPF extension
    @staticmethod
    def is_opaque_type_valid(opaque_type):
        return opaque_type in [conf.OPAQUE_TYPE_ABR_LSA, conf.OPAQUE_TYPE_PREFIX_LSA, conf.OPAQUE_TYPE_ASBR_LSA]

    #  Returns next LS Sequence Number given a valid LS Sequence Number
    @staticmethod
    def get_next_ls_sequence_number(ls_sequence_number):
        return header.Header.get_next_ls_sequence_number(ls_sequence_number)

    def __str__(self):
        return 'Header: ' + self.header.__str__() + ' Body: ' + self.body.__str__()
