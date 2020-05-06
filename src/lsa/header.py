import struct

import general.utils as utils
import conf.conf as conf

'''
This class represents the OSPF LSA header and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
OSPFV2_FORMAT_STRING = "> H B B L L L H H"  # Determines the format of the byte object to be created
OSPFV3_FORMAT_STRING = "> H H L L L H H"


class Header:  # OSPFv2 and OSPFv3 - 20 bytes

    def __init__(self, ls_age, options, ls_type, link_state_id, advertising_router, ls_sequence_number, version):
        is_valid, message = self.parameter_validation(
            ls_age, options, ls_type, link_state_id, advertising_router, ls_sequence_number, version)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)

        self.ospf_version = version
        self.ls_age = ls_age  # 2 bytes
        if version == conf.VERSION_IPV4:
            self.options = options  # 1 byte - Only for OSPFv2
        else:
            self.options = 0
        self.ls_type = ls_type  # 1 byte in OSPFv2, 2 bytes in OSPFv3
        self.link_state_id = link_state_id  # 4 bytes
        self.advertising_router = advertising_router  # 4 bytes
        self.ls_sequence_number = ls_sequence_number  # 4 bytes
        self.ls_checksum = 0  # 2 bytes
        self.length = 0  # 2 bytes

    #  Converts set of parameters to a byte object suitable to be sent and recognized as the header of an OSPF LSA
    def pack_header(self):
        decimal_link_state_id = utils.Utils.ipv4_to_decimal(self.link_state_id)
        decimal_advertising_router = utils.Utils.ipv4_to_decimal(self.advertising_router)
        if self.ospf_version == conf.VERSION_IPV4:
            return struct.pack(OSPFV2_FORMAT_STRING, self.ls_age, self.options, self.ls_type, decimal_link_state_id,
                               decimal_advertising_router, self.ls_sequence_number, self.ls_checksum, self.length)
        else:
            return struct.pack(OSPFV3_FORMAT_STRING, self.ls_age, self.ls_type, decimal_link_state_id,
                               decimal_advertising_router, self.ls_sequence_number, self.ls_checksum, self.length)

    #  Converts byte object to an OSPF LSA header
    @staticmethod
    def unpack_header(header_bytes, version):
        format_string = Header.get_format_string(version)
        header_tuple = struct.unpack(format_string, header_bytes)

        ls_age = header_tuple[0]
        if version == conf.VERSION_IPV4:
            options = header_tuple[1]
            ls_type = header_tuple[2]
            link_state_id = utils.Utils.decimal_to_ipv4(header_tuple[3])
            advertising_router = utils.Utils.decimal_to_ipv4(header_tuple[4])
            ls_sequence_number = header_tuple[5]
            ls_checksum = header_tuple[6]
            length = header_tuple[7]
            header = Header(ls_age, options, ls_type, link_state_id, advertising_router, ls_sequence_number, version)
        else:
            ls_type = header_tuple[1]
            link_state_id = utils.Utils.decimal_to_ipv4(header_tuple[2])
            advertising_router = utils.Utils.decimal_to_ipv4(header_tuple[3])
            ls_sequence_number = header_tuple[4]
            ls_checksum = header_tuple[5]
            length = header_tuple[6]
            header = Header(ls_age, 0, ls_type, link_state_id, advertising_router, ls_sequence_number, version)
        header.ls_checksum = ls_checksum
        header.length = length
        return header

    #  Validates constructor parameters - Returns error message in case of failed validation
    def parameter_validation(
            self, ls_age, options, ls_type, link_state_id, advertising_router, ls_sequence_number, version):
        try:
            if (ls_age < 0) | (ls_age > conf.MAX_AGE):
                return False, "Invalid LS Age"
            if (version == conf.VERSION_IPV4) & ((options < 0) | (options > conf.MAX_VALUE_8_BITS)):
                return False, "Invalid options"
            if (version == conf.VERSION_IPV4) & (
                    ls_type not in [conf.LSA_TYPE_ROUTER, conf.LSA_TYPE_NETWORK, conf.LSA_TYPE_SUMMARY_TYPE_3,
                                    conf.LSA_TYPE_SUMMARY_TYPE_4, conf.LSA_TYPE_AS_EXTERNAL]):
                return False, "Invalid LS Type"
            if (version == conf.VERSION_IPV6) & ((ls_type <= 0) | (ls_type > conf.MAX_VALUE_16_BITS)):
                return False, "Invalid LS Type"
            s1_s2_bits = Header.get_s1_s2_bits(ls_type)
            if (version == conf.VERSION_IPV6) & (
                    s1_s2_bits not in [conf.LINK_LOCAL_SCOPING, conf.AREA_SCOPING, conf.AS_SCOPING]):
                return False, "Invalid values for S1 and S2 bits"
            if not utils.Utils.is_ipv4_address(link_state_id):
                return False, "Invalid Link State ID"
            if (not utils.Utils.is_ipv4_address(advertising_router)) | (advertising_router == '0.0.0.0'):
                return False, "Invalid Advertising Router"
            if (ls_sequence_number < 0) | (ls_sequence_number > conf.MAX_VALUE_32_BITS) |\
                    (ls_sequence_number == 0x80000000):  # Sequence Number 0x80000000 is unused
                return False, "Invalid LS Sequence Number"
            if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
                return False, "Invalid OSPF version"
            return True, ''  # No error message to return
        except (ValueError, TypeError):
            return False, "Invalid parameter type"

    #  Gets U-bit value from LS Type value in OSPFv3 LSA header
    @staticmethod
    def get_u_bit(ls_type):
        return ls_type >> 15  # U-bit is 1st bit of LS Type in OSPFv3

    #  Gets S1 and S2 bits value from LS Type value in OSPFv3 LSA header
    @staticmethod
    def get_s1_s2_bits(ls_type):
        first_3_bytes = ls_type >> 13
        return first_3_bytes & 0x3  # S1 and S2 bits are respectively 3rd and 2nd bits of LS Type in OSPFv3

    @staticmethod
    def get_format_string(version):
        if version == conf.VERSION_IPV4:
            return OSPFV2_FORMAT_STRING
        elif version == conf.VERSION_IPV6:
            return OSPFV3_FORMAT_STRING
        else:
            raise ValueError("Invalid OSPF version")
