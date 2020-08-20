import struct

import lsa.body as body
import conf.conf as conf
import general.utils as utils

'''
This class represents the body of a Prefix-LSA of the OSPF extension and contains its operations

OSPFv2

     0         1         2         3     bytes
+---------+---------+---------+---------+
|    0    |           Metric            |
+---------+---------+---------+---------+
|               Subnet Mask             |
+---------+---------+---------+---------+
|             Subnet Address            |
+---------+---------+---------+---------+
|                  ...                  |
+---------+---------+---------+---------+
|    0    |           Metric            |
+---------+---------+---------+---------+
|               Subnet Mask             |
+---------+---------+---------+---------+
|             Subnet Address            |
+---------+---------+---------+---------+

OSPFv3

     0         1         2         3     bytes
+---------+---------+---------+---------+
|               # prefixes              |
+---------+---------+---------+---------+
|    0    |           Metric            |
+---------+---------+---------+---------+
|P. Length| P. Opt. |         0         |
+---------+---------+---------+---------+
|             Address Prefix            |
|                  ...                  |
+---------+---------+---------+---------+
|                  ...                  |
+---------+---------+---------+---------+
|    0    |           Metric            |
+---------+---------+---------+---------+
|P. Length| P. Opt. |         0         |
+---------+---------+---------+---------+
|             Address Prefix            |
|                  ...                  |
+---------+---------+---------+---------+
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
#  Q - Unsigned long long (8 bytes) - struct.pack("> Q", 1) -> b'\x00\x00\x00\x00\x00\x00\x00\x01
SUBNET_FORMAT_STRING = "> L L L"
OSPFV3_BASE_FORMAT_STRING = "> L"
PREFIX_DATA_FORMAT_STRING = "> L B B H"


class ExtensionPrefix(body.Body):  # OSPFv2 - 12 bytes / subnet; OSPFv3 - 4 bytes + 8-24 bytes / prefix

    def __init__(self, version):
        self.subnet_list = []  # 12 bytes / subnet - Just for OSPFv2
        self.prefix_number = 0  # 4 bytes - Just for OSPFv3
        self.prefix_list = []  # 8-24 bytes / prefix - Just for OSPFv3
        self.version = version

    #  Adds data for one subnet to the OSPFv2 LSA body
    def add_subnet_info(self, metric, subnet_mask, subnet_address):
        if self.version != conf.VERSION_IPV4:
            return
        if not (0 <= metric <= conf.MAX_VALUE_24_BITS):
            raise ValueError("Invalid Metric")
        if not utils.Utils.is_ipv4_network_mask(subnet_mask):
            raise ValueError("Invalid Subnet Mask")
        if not utils.Utils.is_ipv4_address(subnet_address):
            raise ValueError("Invalid Subnet Address")

        if not self.has_subnet_info(subnet_mask, subnet_address):
            self.subnet_list.append([metric, subnet_mask, subnet_address])

    #  Adds data for one prefix to the OSPFv3 LSA body
    def add_prefix_info(self, metric, prefix_length, prefix_options, address_prefix):
        if self.version != conf.VERSION_IPV6:
            return
        if not (0 <= metric <= conf.MAX_VALUE_24_BITS):
            raise ValueError("Invalid Metric")
        if not (0 <= prefix_length <= 16 * conf.BYTE_SIZE):
            raise ValueError("Invalid Prefix Length")
        if not (0 <= prefix_options <= conf.MAX_VALUE_8_BITS):
            raise ValueError("Invalid Prefix Options")
        if not utils.Utils.is_ipv6_address(address_prefix):
            raise ValueError("Invalid Address Prefix")

        if not self.has_prefix_info(prefix_length, address_prefix):
            self.prefix_list.append([metric, prefix_length, prefix_options, address_prefix])
            self.prefix_number += 1

    def has_subnet_info(self, subnet_mask, subnet_address):
        has_subnet_info = False
        for subnet_info in self.subnet_list:
            if (subnet_info[1] == subnet_mask) & (subnet_info[2] == subnet_address):
                has_subnet_info = True
        return has_subnet_info

    def has_prefix_info(self, prefix_length, address_prefix):
        has_prefix_info = False
        for prefix_info in self.prefix_list:
            if (prefix_info[1] == prefix_length) & (prefix_info[3] == address_prefix):
                has_prefix_info = True
        return has_prefix_info

    def get_subnet_info(self, subnet_mask, subnet_address):
        for subnet_info in self.subnet_list:
            if (subnet_info[1] == subnet_mask) & (subnet_info[2] == subnet_address):
                return subnet_info
        return None

    def get_prefix_info(self, prefix_length, address_prefix):
        for prefix_info in self.prefix_list:
            if (prefix_info[1] == prefix_length) & (prefix_info[3] == address_prefix):
                return prefix_info
        return None

    #  Deletes data for one subnet from the OSPFv2 LSA body
    def delete_subnet_info(self, subnet_mask, subnet_address):
        for subnet_info in self.subnet_list:
            if (subnet_info[1] == subnet_mask) & (subnet_info[2] == subnet_address):
                self.subnet_list.remove(subnet_info)

    #  Deletes data for one prefix from the OSPFv3 LSA body
    def delete_prefix_info(self, prefix_length, address_prefix):
        for prefix_info in self.prefix_list:
            if (prefix_info[1] == prefix_length) & (prefix_info[3] == address_prefix):
                self.prefix_list.remove(prefix_info)
                self.prefix_number -= 1

    #  Creates byte object suitable to be sent and recognized as the body of a Prefix-LSA of the OSPF extension
    def pack_lsa_body(self):
        body_bytes = b''
        if self.version == conf.VERSION_IPV4:
            for subnet_info in self.subnet_list:
                metric = subnet_info[0]
                decimal_subnet_mask = utils.Utils.ipv4_to_decimal(subnet_info[1])
                decimal_subnet_address = utils.Utils.ipv4_to_decimal(subnet_info[2])
                body_bytes += struct.pack(SUBNET_FORMAT_STRING, metric, decimal_subnet_mask, decimal_subnet_address)

        elif self.version == conf.VERSION_IPV6:
            body_bytes = struct.pack(OSPFV3_BASE_FORMAT_STRING, self.prefix_number)
            for prefix_info in self.prefix_list:
                metric = prefix_info[0]
                prefix_length = prefix_info[1]
                prefix_options = prefix_info[2]
                decimal_prefix = utils.Utils.ipv6_to_decimal(prefix_info[3])
                prefix_data = struct.pack(PREFIX_DATA_FORMAT_STRING, metric, prefix_length, prefix_options, 0)
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

        else:
            raise ValueError("Invalid OSPF version")

        return body_bytes

    #  Converts byte stream to body of a Prefix-LSA of the OSPF extension
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        if version == conf.VERSION_IPV4:
            unpacked_body = ExtensionPrefix(conf.VERSION_IPV4)
            while len(body_bytes) > 0:
                subnet_bytes = body_bytes[:12]
                subnet_parameters = struct.unpack(SUBNET_FORMAT_STRING, subnet_bytes)
                metric = subnet_parameters[0]
                subnet_mask = utils.Utils.decimal_to_ipv4(subnet_parameters[1])
                subnet_address = utils.Utils.decimal_to_ipv4(subnet_parameters[2])
                unpacked_body.add_subnet_info(metric, subnet_mask, subnet_address)
                body_bytes = body_bytes[12:]

        elif version == conf.VERSION_IPV6:
            unpacked_body = ExtensionPrefix(conf.VERSION_IPV6)
            prefix_number = struct.unpack(OSPFV3_BASE_FORMAT_STRING, body_bytes[:4])[0]
            body_bytes = body_bytes[4:]
            for i in range(prefix_number):
                prefix_data = struct.unpack(PREFIX_DATA_FORMAT_STRING, body_bytes[:8])
                metric = prefix_data[0]
                prefix_length = prefix_data[1]
                prefix_options = prefix_data[2]
                body_bytes = body_bytes[8:]

                #  Unpacking data with variable length
                if prefix_length == 0:
                    prefix = 0
                elif 0 < prefix_length <= 32:
                    prefix_bytes = body_bytes[:4]
                    prefix = struct.unpack("> L", prefix_bytes)[0] << 96
                    body_bytes = body_bytes[4:]
                elif 32 < prefix_length <= 64:
                    prefix_bytes = body_bytes[:8]
                    prefix = struct.unpack("> Q", prefix_bytes)[0] << 64
                    body_bytes = body_bytes[8:]
                elif 64 < prefix_length <= 96:
                    prefix_bytes = body_bytes[:8]
                    prefix = struct.unpack("> Q", prefix_bytes)[0] << 64
                    prefix_bytes = body_bytes[8:12]
                    prefix += struct.unpack("> L", prefix_bytes)[0]
                    body_bytes = body_bytes[12:]
                else:  # 96 < prefix_length <= 128:
                    prefix_bytes = body_bytes[:8]
                    prefix = struct.unpack("> Q", prefix_bytes)[0] << 64
                    prefix_bytes = body_bytes[8:16]
                    prefix += struct.unpack("> Q", prefix_bytes)[0]
                    body_bytes = body_bytes[16:]
                prefix = utils.Utils.decimal_to_ipv6(prefix)

                unpacked_body.add_prefix_info(metric, prefix_length, prefix_options, prefix)

        else:
            raise ValueError("Invalid OSPF version")

        return unpacked_body

    def __str__(self):
        if self.version == conf.VERSION_IPV4:
            return str({"Subnets": self.subnet_list})
        elif self.version == conf.VERSION_IPV6:
            return str({"Prefix Number": self.prefix_number, "Prefixes": self.prefix_list})
        else:
            raise ValueError("Invalid OSPF version")
