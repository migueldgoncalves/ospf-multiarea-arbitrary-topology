import struct

import lsa.body as body
import conf.conf as conf
import general.utils as utils

'''
This class represents the body of an OSPF Link-LSA and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
#  Q - Unsigned long long (8 bytes) - struct.pack("> Q", 1) -> b'\x00\x00\x00\x00\x00\x00\x00\x01
BASE_FORMAT_STRING = "> L Q Q L"  # Determines the format of the byte object to be created
PREFIX_BASE_FORMAT_STRING = "> B B H"


class Link(body.Body):  # 24 bytes + 4-20 bytes / prefix

    def __init__(self, router_priority, options, link_local_address):
        self.router_priority = router_priority  # 1 byte
        self.options = options  # 3 bytes
        self.link_local_address = link_local_address  # 16 bytes
        self.prefix_number = 0  # 4 bytes
        self.prefixes = []  # 4-20 bytes / prefix

    #  Adds data for one prefix to the LSA body
    def add_prefix_info(self, prefix_length, prefix_options, prefix):
        prefix_info = [prefix_length, prefix_options, prefix]
        if prefix_info not in self.prefixes:
            self.prefix_number += 1
            self.prefixes.append(prefix_info)

    def has_prefix_info(self, prefix_length, prefix_options, prefix):
        return [prefix_length, prefix_options, prefix] in self.prefixes

    #  Deletes data for one prefix from the LSA body
    def delete_prefix_info(self, prefix_length, prefix_options, prefix):
        prefix_info = [prefix_length, prefix_options, prefix]
        if prefix_info in self.prefixes:
            self.prefix_number -= 1
            self.prefixes.remove(prefix_info)

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Link-LSA
    def pack_lsa_body(self):
        decimal_link_local_address = utils.Utils.ipv6_to_decimal(self.link_local_address)
        body_bytes = struct.pack(
            BASE_FORMAT_STRING, (self.router_priority << 24) + self.options, decimal_link_local_address >> 64,
            decimal_link_local_address & conf.MAX_VALUE_64_BITS, self.prefix_number)

        for p in self.prefixes:
            prefix_length = p[0]
            prefix_options = p[1]
            decimal_prefix = utils.Utils.ipv6_to_decimal(p[2])
            prefix_data = struct.pack(PREFIX_BASE_FORMAT_STRING, prefix_length, prefix_options, 0)
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

    #  Converts byte stream to body of an OSPF Link-LSA
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        first_fields = struct.unpack(BASE_FORMAT_STRING, body_bytes[:24])
        router_priority = first_fields[0] >> 24
        options = first_fields[0] & conf.MAX_VALUE_24_BITS
        link_local_address = utils.Utils.decimal_to_ipv6((first_fields[1] << 64) + first_fields[2])
        prefix_number = first_fields[3]
        unpacked_body = Link(router_priority, options, link_local_address)
        body_bytes = body_bytes[24:]

        for i in range(prefix_number):
            prefix_fields = struct.unpack(PREFIX_BASE_FORMAT_STRING, body_bytes[:4])
            prefix_length = prefix_fields[0]
            prefix_options = prefix_fields[1]

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

            unpacked_body.add_prefix_info(prefix_length, prefix_options, prefix)

        return unpacked_body
