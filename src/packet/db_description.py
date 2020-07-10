import struct

import packet.body as body
import conf.conf as conf
import lsa.header as header

'''
This class represents the body of an OSPF Database Description packet and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
OSPFV2_BASE_FORMAT_STRING = "> H B B L"  # Determines the format of the byte object to be created
OSPFV3_BASE_FORMAT_STRING = "> L H H L"


class DBDescription(body.Body):  # OSPFv2 - 8 bytes + 20 bytes / LSA Header; OSPFv3 - 12 bytes + 20 bytes / LSA Header

    def __init__(self, interface_mtu, options, i_bit, m_bit, ms_bit, dd_sequence_number, lsa_headers, version):
        is_valid, message = self.parameter_validation(
            interface_mtu, options, i_bit, m_bit, ms_bit, dd_sequence_number, lsa_headers, version)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)

        self.interface_mtu = interface_mtu  # 2 bytes
        self.options = options  # 1 byte in OSPFv2, 3 bytes in OSPFv3
        self.i_bit = i_bit  # Init bit
        self.m_bit = m_bit  # More bit
        self.ms_bit = ms_bit  # Master/Slave bit
        self.dd_sequence_number = dd_sequence_number  # 4 bytes
        self.lsa_headers = lsa_headers  # 20 bytes / LSA Header
        self.version = version

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Database Description packet
    def pack_packet_body(self):
        i_m_ms_byte = (self.i_bit << 2) + (self.m_bit << 1) + self.ms_bit  # Byte that contains the I, M and MS bits
        if self.version == conf.VERSION_IPV4:
            header_bytes = struct.pack(
                OSPFV2_BASE_FORMAT_STRING, self.interface_mtu, self.options, i_m_ms_byte, self.dd_sequence_number)
        else:
            header_bytes = struct.pack(
                OSPFV3_BASE_FORMAT_STRING, self.options, self.interface_mtu, i_m_ms_byte, self.dd_sequence_number)
            header_bytes = header_bytes
        for lsa_header in self.lsa_headers:
            lsa_header_bytes = lsa_header.pack_header()
            header_bytes += lsa_header_bytes
        return header_bytes

    #  Converts byte stream to body of an OSPF Hello packet
    @staticmethod
    def unpack_packet_body(body_bytes, version):
        if version == conf.VERSION_IPV4:
            base_body_bytes = body_bytes[:conf.OSPFV2_BASE_DB_DESCRIPTION_LENGTH]
        else:
            base_body_bytes = body_bytes[:conf.OSPFV3_BASE_DB_DESCRIPTION_LENGTH]
        body_tuple = struct.unpack(DBDescription.get_format_string(version), base_body_bytes)
        if version == conf.VERSION_IPV4:
            interface_mtu = body_tuple[0]
            options = body_tuple[1]
        else:
            options = body_tuple[0]
            interface_mtu = body_tuple[1]
        i_m_ms_byte = body_tuple[2]
        i_bit = bool(i_m_ms_byte >> 2)  # 6th bit
        m_bit = bool((i_m_ms_byte & 2) >> 1)  # 7th bit
        ms_bit = bool(i_m_ms_byte & 1)  # 8th bit
        dd_sequence_number = body_tuple[3]
        lsa_headers = DBDescription.get_lsa_headers_from_packet_body(body_bytes, version)
        return DBDescription(interface_mtu, options, i_bit, m_bit, ms_bit, dd_sequence_number, lsa_headers, version)

    @staticmethod
    def get_format_string(version):
        if version == conf.VERSION_IPV4:
            format_string = OSPFV2_BASE_FORMAT_STRING
        elif version == conf.VERSION_IPV6:
            format_string = OSPFV3_BASE_FORMAT_STRING
        else:
            raise ValueError("Invalid OSPF version")
        return format_string

    #  Gets the LSA Headers from a byte object representing the body of an OSPF DB Description packet
    @staticmethod
    def get_lsa_headers_from_packet_body(body_bytes, version):
        if version == conf.VERSION_IPV4:
            lsa_headers_bytes = body_bytes[conf.OSPFV2_BASE_DB_DESCRIPTION_LENGTH:]
        else:
            lsa_headers_bytes = body_bytes[conf.OSPFV3_BASE_DB_DESCRIPTION_LENGTH:]
        lsa_headers = []
        for i in range(len(lsa_headers_bytes) // conf.LSA_HEADER_LENGTH):
            lsa_header_bytes = lsa_headers_bytes[i * conf.LSA_HEADER_LENGTH:(i + 1) * conf.LSA_HEADER_LENGTH]
            lsa_header = header.Header.unpack_header(lsa_header_bytes, version)
            lsa_headers.append(lsa_header)
        return tuple(lsa_headers)

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
            if (len(lsa_headers) > 0) & i_bit:
                return False, "ExStart state - There must be no LSA Headers"
            for lsa_header in lsa_headers:
                lsa_header.pack_header()  # An error will be raised if it is not a LSA Header instance
            if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
                return False, "Invalid OSPF version"
            return True, ''  # No error message to return
        except (ValueError, TypeError, AttributeError):
            return False, "Invalid parameter type"

    def __str__(self):
        lsa_headers = []
        for lsa_header in self.lsa_headers:
            lsa_headers.append(str(lsa_header))
        return str({'Interface MTU': self.interface_mtu, 'Options': self.options, 'I-bit': self.i_bit,
                    'M-bit': self.m_bit, 'MS-bit': self.ms_bit, 'DD Sequence Number': self.dd_sequence_number,
                    'LSA Headers': lsa_headers, 'Version': self.version})
