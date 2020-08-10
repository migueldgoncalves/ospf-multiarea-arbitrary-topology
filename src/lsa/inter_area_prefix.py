import struct

import lsa.body as body
import general.utils as utils
import conf.conf as conf

'''
This class represents the body of an OSPF Inter-Area-Prefix-LSA and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
#  Q - Unsigned long long (8 bytes) - struct.pack("> Q", 1) -> b'\x00\x00\x00\x00\x00\x00\x00\x01
BASE_FORMAT_STRING = "> L B B H"  # Determines the format of the byte object to be created


class InterAreaPrefix(body.Body):  # 8-24 bytes

    def __init__(self, metric, prefix_length, prefix_options, address_prefix):
        self.metric = metric  # 3 bytes
        self.prefix_length = prefix_length  # 1 byte
        self.prefix_options = prefix_options  # 1 byte
        self.address_prefix = address_prefix  # 0-16 bytes

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Inter-Area-Prefix-LSA
    def pack_lsa_body(self):
        body_bytes = struct.pack(BASE_FORMAT_STRING, self.metric, self.prefix_length, self.prefix_options, 0)
        decimal_prefix = utils.Utils.ipv6_to_decimal(self.address_prefix)

        #  Packing data with variable length
        if self.prefix_length == 0:
            prefix_bytes = b''
        elif 0 < self.prefix_length <= 32:
            prefix_bytes = struct.pack("> L", decimal_prefix >> 96)
        elif 32 < self.prefix_length <= 64:
            prefix_bytes = struct.pack("> Q", decimal_prefix >> 64)
        elif 64 < self.prefix_length <= 96:
            prefix_bytes = struct.pack("> Q", decimal_prefix >> 64)
            prefix_bytes += struct.pack("> L", (decimal_prefix >> 32) & conf.MAX_VALUE_32_BITS)
        else:  # 96 < prefix_length <= 128:
            prefix_bytes = struct.pack("> Q", decimal_prefix >> 64)
            prefix_bytes += struct.pack("> Q", decimal_prefix & conf.MAX_VALUE_64_BITS)
        body_bytes += prefix_bytes
        return body_bytes

    #  Converts byte stream to body of an OSPF Inter-Area-Prefix-LSA
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        parameters = struct.unpack(BASE_FORMAT_STRING, body_bytes[:8])
        metric = parameters[0]
        prefix_length = parameters[1]
        prefix_options = parameters[2]
        body_bytes = body_bytes[8:]

        #  Unpacking data with variable length
        if prefix_length == 0:
            prefix = 0
        elif 0 < prefix_length <= 32:
            prefix = struct.unpack("> L", body_bytes)[0] << 96
        elif 32 < prefix_length <= 64:
            prefix = struct.unpack("> Q", body_bytes)[0] << 64
        elif 64 < prefix_length <= 96:
            prefix_bytes = body_bytes[:8]
            prefix = struct.unpack("> Q", prefix_bytes)[0] << 64
            prefix_bytes = body_bytes[8:12]
            prefix += struct.unpack("> L", prefix_bytes)[0]
        else:  # 96 < prefix_length <= 128:
            prefix_bytes = body_bytes[:8]
            prefix = struct.unpack("> Q", prefix_bytes)[0] << 64
            prefix_bytes = body_bytes[8:16]
            prefix += struct.unpack("> Q", prefix_bytes)[0]
        prefix = utils.Utils.decimal_to_ipv6(prefix)

        return InterAreaPrefix(metric, prefix_length, prefix_options, prefix)

    def __str__(self):
        return str({'Metric': self.metric, 'Prefix Length': self.prefix_length, 'Prefix Options': self.prefix_options,
                    'Address Prefix': self.address_prefix})
