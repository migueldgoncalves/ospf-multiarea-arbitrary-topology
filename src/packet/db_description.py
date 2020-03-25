import struct

import packet.body as body
import conf.conf as conf

'''
This class represents the body of an OSPF Database Description packet and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
OSPFV2_BASE_FORMAT_STRING = "> H B B L"  # Determines the format of the byte object to be created
OSPFV3_BASE_FORMAT_STRING = "> L H B L"


class DBDescription(body.Body):  # OSPFv2 - 8 bytes + 20 bytes / LSA Header; OSPFv3 - 10 bytes + 20 bytes / LSA Header

    interface_mtu = 0  # 2 bytes
    options = 0  # 1 byte in OSPFv2, 3 bytes in OSPFv3
    # I-bit, M-bit and MS-bit are respectively the last 3 bits of a byte with all other bits set to 0
    i_bit = False  # Init bit
    m_bit = False  # More bit
    ms_bit = False  # Master/Slave bit
    dd_sequence_number = 0  # 4 bytes
    lsa_headers = ()  # 20 bytes / LSA Header

    version = 0

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Database Description packet
    def pack_packet_body(self):
        pass

    #  Converts byte stream to body of an OSPF Hello packet
    @staticmethod
    def unpack_packet_body(body_bytes, version):
        pass

    #  Validates constructor parameters - Returns error message in case of failed validation
    @staticmethod
    def parameter_validation(interface_mtu, options, i_bit, m_bit, ms_bit, dd_sequence_number, lsa_headers, version):
        try:
            if (interface_mtu <= 0) | (interface_mtu > conf.MAX_VALUE_16_BITS):
                return False, "Invalid MTU"
            if (not (0 <= options <= conf.MAX_VALUE_8_BITS)) & (version == conf.VERSION_IPV4):  # OSPFv2
                return False, "Invalid packet options"
            if (not (0 <= options <= conf.MAX_VALUE_24_BITS)) & (version == conf.VERSION_IPV6):  # OSPFv3
                return False, "Invalid packet options"
            if (i_bit is True) & ((m_bit is False) | (ms_bit is False)):
                return False, "Invalid values for I, M and MS bits"
            if (dd_sequence_number < 0) | (dd_sequence_number > conf.MAX_VALUE_32_BITS):
                return False, "Invalid DD Sequence Number"
            if len(lsa_headers) == 0:
                return False, "There must be at least 1 LSA Header"
            for lsa_header in lsa_headers:
                lsa_header.pack_header()  # An error will be raised if it is not a LSA Header instance
            if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
                return False, "Invalid OSPF version"
            return True, ''  # No error message to return
        except (ValueError, TypeError, AttributeError):
            return False, "Invalid parameter type"
