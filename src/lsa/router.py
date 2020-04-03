import struct

import lsa.body as body
import conf.conf as conf

'''
This class represents the body of an OSPF Router LSA and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
BASE_FORMAT_STRING = "> H"  # Determines the format of the byte object to be created
OSPFV2_LINK_FORMAT_STRING = " L L B B H"
OSPFV3_LINK_FORMAT_STRING = " L L L L"


class Router(body.Body):  # OSPFv2 - 3 bytes + 12 bytes/link; OSPFv3 - 4 bytes + 16 bytes/link

    bit_v = False  # Virtual link endpoint bit
    bit_e = False  # AS boundary router bit
    bit_b = False  # Area border router bit
    link_number = 0  # 2 bytes - Just for OSPFv2
    options = 0  # 3 bytes - Just for OSPFv3
    links = []  # 12 bytes/link in OSPFv2; 16 bytes/link in OSPFv3

    version = 0

    def __init__(self, bit_v, bit_e, bit_b, link_number, options):
        self.bit_v = bit_v
        self.bit_e = bit_e
        self.bit_b = bit_b
        self.link_number = link_number
        self.options = options

    #  Adds data for one link (interface) to the OSPFv2 LSA body
    def add_link_info_v2(self, link_id, link_data, link_type, tos_number, metric):
        if self.version == conf.VERSION_IPV4:
            new_link = [link_id, link_data, link_type, tos_number, metric]
            self.links.append(new_link)

    #  Adds data for one link (interface) to the OSPFv3 LSA body
    def add_link_info_v3(self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id):
        if self.version == conf.VERSION_IPV6:
            new_link = [link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id]
            self.links.append(new_link)

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Router LSA
    def pack_lsa_body(self):
        flags_byte = (self.bit_v << 2) + (self.bit_e << 1) + self.bit_b
        if self.version == conf.VERSION_IPV6:
            flags_byte << 1

        if self.version == conf.VERSION_IPV4:
            #  TODO: Continue
            pass

    #  Converts byte stream to body of an OSPF Router LSA
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        pass

    #  Validates constructor parameters - Returns error message in case of failed validation
    @staticmethod
    def parameter_validation(version):
        try:
            if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
                return False, "Invalid OSPF version"
            return True, ''  # No error message to return
        except (ValueError, TypeError, AttributeError):
            return False, "Invalid parameter type"
