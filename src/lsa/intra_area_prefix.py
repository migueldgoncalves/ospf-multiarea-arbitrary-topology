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

    def __init__(self, referenced_ls_type, referenced_link_state_id, referenced_advertising_router):
        self.prefix_number = 0  # 2 bytes
        self.referenced_ls_type = referenced_ls_type  # 2 bytes
        self.referenced_link_state_id = referenced_link_state_id  # 4 bytes
        self.referenced_advertising_router = referenced_advertising_router  # 4 bytes
        self.prefixes = []  # 4-20 bytes / prefix

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
        first_fields = struct.unpack(BASE_FORMAT_STRING, body_bytes[:12])
        prefix_number = first_fields[0]
        referenced_ls_type = first_fields[1] - 0x2000
        referenced_link_state_id = utils.Utils.decimal_to_ipv4(first_fields[2])
        referenced_advertising_router = utils.Utils.decimal_to_ipv4(first_fields[3])
        unpacked_body = IntraAreaPrefix(referenced_ls_type, referenced_link_state_id, referenced_advertising_router)
        body_bytes = body_bytes[12:]

        for i in range(prefix_number):
            prefix_fields = struct.unpack(PREFIX_BASE_FORMAT_STRING, body_bytes[:4])
            prefix_length = prefix_fields[0]
            prefix_options = prefix_fields[1]
            metric = prefix_fields[2]

            #  Unpacking data with variable length
            if prefix_length == 0:
                prefix = 0
                body_bytes = body_bytes[4:]
            elif 0 < prefix_length <= 32:
                prefix_bytes = body_bytes[4:8]
                prefix = struct.unpack("> L", prefix_bytes)[0] << 96
                body_bytes = body_bytes[8:]
            elif 32 < prefix_length <= 64:
                prefix_bytes = body_bytes[4:12]
                prefix = struct.unpack("> Q", prefix_bytes)[0] << 64
                body_bytes = body_bytes[12:]
            elif 64 < prefix_length <= 96:
                prefix_bytes = body_bytes[4:12]
                prefix = struct.unpack("> Q", prefix_bytes)[0] << 64
                prefix_bytes = body_bytes[12:16]
                prefix += struct.unpack("> L", prefix_bytes)[0]
                body_bytes = body_bytes[16:]
            else:  # 96 < prefix_length <= 128:
                prefix_bytes = body_bytes[4:12]
                prefix = struct.unpack("> Q", prefix_bytes)[0] << 64
                prefix_bytes = body_bytes[12:20]
                prefix += struct.unpack("> Q", prefix_bytes)[0]
                body_bytes = body_bytes[20:]
            prefix = utils.Utils.decimal_to_ipv6(prefix)

            unpacked_body.add_prefix_info(prefix_length, prefix_options, metric, prefix)

        return unpacked_body
