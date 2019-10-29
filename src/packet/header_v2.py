import struct

import general.utils as utils

'''
This class represents the OSPFv2 packet header and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
#  Q - Unsigned long long (8 bytes) - struct.pack("> Q", 1) -> b'\x00\x00\x00\x00\x00\x00\x00\x01
FORMAT_STRING = "> B B H L L H H Q"  # Determines the format of the byte object to be created


class HeaderV2:

    utils = utils.Utils()

    version = 0  # 1 byte
    packet_type = 0  # 1 byte
    length = 0  # 2 bytes
    router_id = ''  # 4 bytes
    area_id = ''  # 4 bytes
    checksum = 0  # 2 bytes
    auth_type = 0  # 2 bytes
    authentication = 0  # 8 bytes

    def __init__(self, version, packet_type, length, router_id, area_id, auth_type, authentication):
        self.version = version
        self.packet_type = packet_type
        self.length = length
        self.router_id = router_id
        self.area_id = area_id
        self.auth_type = auth_type
        self.authentication = authentication

    def set_checksum(self, checksum):
        self.checksum = checksum

    #  Converts set of parameters to a byte object suitable to be sent and recognized as the header of an OSPF packet
    def pack_header(self):
        decimal_router_id = self.utils.ipv4_to_decimal(self.router_id)
        decimal_area_id = self.utils.ipv4_to_decimal(self.area_id)
        return struct.pack(FORMAT_STRING, self.version, self.packet_type, self.length, decimal_router_id,
                           decimal_area_id, self.checksum, self.auth_type, self.authentication)

    def print_header_packet(self):
        print(self.pack_header())

    @staticmethod
    def get_format_string():
        return FORMAT_STRING
