import struct

import lsa.body as body
import conf.conf as conf
import general.utils as utils

'''
This class represents the body of an OSPF Intra-Area-Prefix-LSA and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
#  Q - Unsigned long long (8 bytes) - struct.pack("> Q", 1) -> b'\x00\x00\x00\x00\x00\x00\x00\x01
BASE_FORMAT_STRING = "> H H L L"  # Determines the format of the byte object to be created
PREFIX_BASE_FORMAT_STRING = "> B B H"


class IntraAreaPrefix(body.Body):  # 12 bytes + 4-20 bytes / prefix

    prefix_number = 0  # 2 bytes
    referenced_ls_type = 0  # 2 bytes
    referenced_link_state_id = '0.0.0.0'  # 4 bytes
    referenced_advertising_router = '0.0.0.0'  # 4 bytes
    prefixes = []

    def __init__(self, referenced_ls_type, referenced_link_state_id, referenced_advertising_router):
        self.prefix_number = 0
        self.referenced_ls_type = referenced_ls_type
        self.referenced_link_state_id = referenced_link_state_id
        self.referenced_advertising_router = referenced_advertising_router
        self.prefixes = []

    #  Adds data for one prefix to the LSA body
    def add_prefix_info(self, prefix_length, prefix_options, metric, prefix):
        self.prefix_number += 1
        prefix_data = [prefix_length, prefix_options, metric, prefix]
        self.prefixes.append(prefix_data)

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Intra-Area-Prefix-LSA
    def pack_lsa_body(self):
        referenced_ls_type = self.referenced_ls_type + 0x2000
        decimal_referenced_link_state_id = utils.Utils.ipv4_to_decimal(self.referenced_link_state_id)
        decimal_referenced_advertising_router = utils.Utils.ipv4_to_decimal(self.referenced_advertising_router)
        body_bytes = struct.pack(BASE_FORMAT_STRING, self.prefix_number, referenced_ls_type,
                                 decimal_referenced_link_state_id, decimal_referenced_advertising_router)
        for p in self.prefixes:
            prefix_length = p[0]
            prefix_options = p[1]
            metric = p[2]
            decimal_prefix = utils.Utils.ipv6_to_decimal(p[3])
            prefix_data = struct.pack(PREFIX_BASE_FORMAT_STRING, prefix_length, prefix_options, metric)
            body_bytes += prefix_data

            #  Packing data with variable length
            if prefix_length == 0:
                prefix_bytes = b''
            elif 0 < prefix_length <= 32:
                prefix_bytes = struct.pack("> L", decimal_prefix >> 96)
            elif 32 < prefix_length <= 64:
                prefix_bytes = struct.pack("> Q", decimal_prefix >> 64)
            elif 64 < prefix_length <= 96:
                prefix_bytes = struct.pack("> Q", decimal_prefix >> 64)
                prefix_bytes += struct.pack("> L", (decimal_prefix >> 32) & conf.MAX_VALUE_32_BITS)
            else:  # 96 < prefix_length <= 128:
                prefix_bytes = struct.pack("> Q", decimal_prefix >> 64)
                prefix_bytes += struct.pack("> Q", decimal_prefix & conf.MAX_VALUE_64_BITS)
            body_bytes += prefix_bytes
        return body_bytes

    #  Converts byte stream to body of an OSPF Intra-Area-Prefix-LSA
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        pass
