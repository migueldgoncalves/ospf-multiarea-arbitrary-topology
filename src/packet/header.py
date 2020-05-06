import struct

import general.utils as utils
import conf.conf as conf

'''
This class represents the OSPF packet header and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
#  Q - Unsigned long long (8 bytes) - struct.pack("> Q", 1) -> b'\x00\x00\x00\x00\x00\x00\x00\x01
OSPFV2_FORMAT_STRING = "> B B H L L H H Q"  # Determines the format of the byte object to be created
OSPFV3_FORMAT_STRING = "> B B H L L H B B"


class Header:  # OSPFv2 - 24 bytes; OSPFv3 - 16 bytes

    def __init__(self, version, packet_type, router_id, area_id, auth_type, authentication, instance_id):
        is_valid, message = self.parameter_validation(
            version, packet_type, router_id, area_id, auth_type, authentication, instance_id)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)

        self.version = version  # 1 byte
        self.packet_type = packet_type  # 1 byte
        self.length = 0  # 2 bytes
        self.router_id = router_id  # 4 bytes
        self.area_id = area_id  # 4 bytes
        self.checksum = 0  # 2 bytes
        if self.version == conf.VERSION_IPV4:
            self.auth_type = auth_type  # 2 bytes - Only for OSPFv2
            self.authentication = authentication  # 8 bytes - Only for OSPFv2
            self.instance_id = 0
        else:
            self.auth_type = 0
            self.authentication = 0
            self.instance_id = instance_id  # 1 byte - Only for OSPFv3 (last byte in OSPFv3 header is set to 0)

    #  Converts set of parameters to a byte object suitable to be sent and recognized as the header of an OSPF packet
    def pack_header(self):
        decimal_router_id = utils.Utils.ipv4_to_decimal(self.router_id)
        decimal_area_id = utils.Utils.ipv4_to_decimal(self.area_id)
        if self.version == conf.VERSION_IPV4:
            return struct.pack(OSPFV2_FORMAT_STRING, self.version, self.packet_type, self.length, decimal_router_id,
                               decimal_area_id, self.checksum, self.auth_type, self.authentication)
        else:
            return struct.pack(OSPFV3_FORMAT_STRING, self.version, self.packet_type, self.length, decimal_router_id,
                               decimal_area_id, self.checksum, self.instance_id, 0)  # Last byte is set to 0

    #  Converts byte object to an OSPF packet header
    @staticmethod
    def unpack_header(header_bytes, version):
        format_string = Header.get_format_string(version)
        header_tuple = struct.unpack(format_string, header_bytes)

        version = header_tuple[0]
        packet_type = header_tuple[1]
        length = header_tuple[2]
        router_id = utils.Utils.decimal_to_ipv4(header_tuple[3])
        area_id = utils.Utils.decimal_to_ipv4(header_tuple[4])
        checksum = header_tuple[5]
        if version == conf.VERSION_IPV4:
            auth_type = header_tuple[6]
            authentication = header_tuple[7]
            header = Header(version, packet_type, router_id, area_id, auth_type, authentication, 0)
        else:
            instance_id = header_tuple[6]
            header = Header(version, packet_type, router_id, area_id, 0, 0, instance_id)
        header.length = length
        header.checksum = checksum
        return header

    #  Cleans packet checksum, authentication type and authentication fields for checksum calculation
    def prepare_packet_checksum(self):
        parameters_to_restore = [self.auth_type, self.authentication]
        self.checksum = 0
        self.auth_type = 0
        self.authentication = 0
        return parameters_to_restore

    #  Restores packet authentication type and authentication fields after checksum calculation
    def finish_packet_checksum(self, cleaned_parameters):
        self.auth_type = cleaned_parameters[0]
        self.authentication = cleaned_parameters[1]

    #  Validates constructor parameters - Returns error message in case of failed validation
    def parameter_validation(self, version, packet_type, router_id, area_id, auth_type, authentication, instance_id):
        try:
            if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
                return False, "Invalid OSPF version"
            if packet_type not in [conf.PACKET_TYPE_HELLO, conf.PACKET_TYPE_DB_DESCRIPTION, conf.PACKET_TYPE_LS_REQUEST,
                                   conf.PACKET_TYPE_LS_UPDATE, conf.PACKET_TYPE_LS_ACKNOWLEDGMENT]:
                return False, "Invalid packet type"
            if not utils.Utils.is_ipv4_address(router_id):
                return False, "Invalid router ID"
            if not utils.Utils.is_ipv4_address(area_id):
                return False, "Invalid area ID"
            if (auth_type not in [conf.NULL_AUTHENTICATION, conf.SIMPLE_PASSWORD, conf.CRYPTOGRAPHIC_AUTHENTICATION])\
                    & (version == conf.VERSION_IPV4):
                return False, "Invalid authentication type"
            if (not (0 <= authentication <= conf.MAX_VALUE_64_BITS)) & (version == conf.VERSION_IPV4):
                return False, "Invalid authentication field"
            if (not (0 <= instance_id <= conf.MAX_VALUE_8_BITS)) & (version == conf.VERSION_IPV6):
                return False, "Invalid instance ID"
            return True, ''  # No error message to return
        except (ValueError, TypeError):
            return False, "Invalid parameter type"

    def set_checksum(self, checksum):
        if (checksum < 0) | (checksum > conf.MAX_VALUE_16_BITS):
            error = "Checksum must be between 0 and " + str(conf.MAX_VALUE_16_BITS) + " bytes, was " + str(checksum)
            raise ValueError(error)
        self.checksum = checksum

    def set_length(self, length):
        if (length < conf.OSPFV2_PACKET_HEADER_LENGTH) & (self.version == conf.VERSION_IPV4):
            error = "Packet length must be at least " + str(conf.OSPFV2_PACKET_HEADER_LENGTH) + " bytes, was " + str(length)
            raise ValueError(error)
        elif (length < conf.OSPFV3_PACKET_HEADER_LENGTH) & (self.version == conf.VERSION_IPV6):
            error = "Packet length must be at least " + str(conf.OSPFV3_PACKET_HEADER_LENGTH) + " bytes, was " + str(length)
            raise ValueError(error)
        elif length > conf.MAX_VALUE_16_BITS:
            error = "Packet length must be no larger than " + str(conf.MAX_VALUE_16_BITS) + " bytes, was" + str(length)
            raise ValueError(error)
        self.length = length

    @staticmethod
    def get_format_string(version):
        if version == conf.VERSION_IPV4:
            return OSPFV2_FORMAT_STRING
        elif version == conf.VERSION_IPV6:
            return OSPFV3_FORMAT_STRING
        else:
            raise ValueError("Invalid OSPF version")
