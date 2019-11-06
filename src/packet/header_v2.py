import struct

import general.utils as utils
import conf.conf as conf

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

    def __init__(self, version, packet_type, router_id, area_id, auth_type, authentication):
        is_valid, message = self.parameter_validation(version, packet_type, router_id, area_id, auth_type,
                                                      authentication)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)

        self.version = version
        self.packet_type = packet_type
        self.router_id = router_id
        self.area_id = area_id
        self.auth_type = auth_type
        self.authentication = authentication

    #  Converts set of parameters to a byte object suitable to be sent and recognized as the header of an OSPF packet
    def pack_header(self):
        decimal_router_id = self.utils.ipv4_to_decimal(self.router_id)
        decimal_area_id = self.utils.ipv4_to_decimal(self.area_id)
        return struct.pack(FORMAT_STRING, self.version, self.packet_type, self.length, decimal_router_id,
                           decimal_area_id, self.checksum, self.auth_type, self.authentication)

    #  Cleans packet checksum, authentication type and authentication fields for checksum calculation
    def prepare_packet_checksum(self):
        self.checksum = 0
        self.auth_type = 0
        self.authentication = 0

    #  Validates constructor parameters - Returns error message in case of failed validation
    def parameter_validation(self, version, packet_type, router_id, area_id, auth_type, authentication):
        if version != conf.VERSION_IPV4:
            return False, "Invalid OSPF version"
        if packet_type not in [conf.PACKET_TYPE_HELLO, conf.PACKET_TYPE_DB_DESCRIPTION, conf.PACKET_TYPE_LS_REQUEST,
                               conf.PACKET_TYPE_LS_UPDATE, conf.PACKET_TYPE_LS_ACKNOWLEDGMENT]:
            return False, "Invalid packet type"
        if not self.utils.is_ipv4_address(router_id):
            return False, "Invalid router ID"
        if not self.utils.is_ipv4_address(area_id):
            return False, "Invalid area ID"
        if auth_type not in [conf.NULL_AUTHENTICATION, conf.SIMPLE_PASSWORD, conf.CRYPTOGRAPHIC_AUTHENTICATION]:
            return False, "Invalid authentication type"
        if authentication < 0:
            return False, "Invalid authentication field"
        return True, ''  # No error message to return

    def set_checksum(self, checksum):
        if (checksum < 0) | (checksum > conf.MAX_VALUE_16_BITS):
            raise ValueError("Checksum must be between 0 and", conf.MAX_VALUE_16_BITS, ", was:", checksum)
        self.checksum = checksum

    def set_length(self, length):
        if length < conf.OSPFV2_HEADER_LENGTH:
            raise ValueError("Packet length must be at least", conf.OSPFV2_HEADER_LENGTH, ", was:", length)
        self.length = length

    def print_header_packet(self):
        print(self.pack_header())

    @staticmethod
    def get_format_string():
        return FORMAT_STRING
