import struct

import conf.conf as conf
import packet.hello_v2 as hello_v2
import packet.header_v2 as header_v2
import packet.packet_creator as packet_creator
import general.utils as utils

'''
This class serves as an interface to incoming packet processing, both for OSPFv2 and OSPFv3
'''

#  Format strings indicate the format of the byte objects to be created, or converted to other object types
#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.unpack("> B", b'\x01) -> 1
#  H - Unsigned short (2 bytes) - struct.unpack("> H", b'\x00\x01) -> 1
#  L - Unsigned long (4 bytes) - struct.unpack("> L", b'\x00\x00\x00\x01) -> 1
#  Q - Unsigned long long (8 bytes) - struct.unpack("> Q", b'\x00\x00\x00\x00\x00\x00\x00\x01) -> 1
FORMAT_STRING = "> B"

PACKET_TUPLE_BASE_LENGTH = 15  # No neighbors - First neighbor IP is in 16th parameter (packet_tuple[15])


class PacketReader:

    #  Converts a byte stream into a OSPF packet
    @staticmethod
    def convert_bytes_to_packet(packet_bytes):
        #  An OSPF packet just with a header, or with less bytes, can immediately be discarded
        if (packet_bytes is None) |\
                (len(packet_bytes) <= min(conf.OSPFV2_HEADER_LENGTH, conf.OSPFV3_HEADER_LENGTH)):
            raise ValueError("Packet byte stream is too short")

        packet_version = PacketReader.get_ospf_version(packet_bytes)
        packet_type = PacketReader.get_ospf_packet_type(packet_bytes)

        #  If no exception is thrown, both packet version and type are valid
        packet = None
        if packet_version == conf.VERSION_IPV4:
            if packet_type == conf.PACKET_TYPE_HELLO:
                neighbor_number = PacketReader.get_hello_packet_neighbor_number(packet_bytes)
                format_string_hello = header_v2.FORMAT_STRING + hello_v2.HelloV2.get_format_string(neighbor_number)
                packet_tuple = struct.unpack(format_string_hello, packet_bytes)

                #  From tuple, create packet

                #  IP addresses and network masks need previous conversion from integers
                router_id = utils.Utils.decimal_to_ipv4(packet_tuple[3])
                area_id = utils.Utils.decimal_to_ipv4(packet_tuple[4])
                network_mask = utils.Utils.decimal_to_ipv4(packet_tuple[8])
                designated_router = utils.Utils.decimal_to_ipv4(packet_tuple[13])
                backup_designated_router = utils.Utils.decimal_to_ipv4(packet_tuple[14])

                header_parameters = [packet_tuple[0], packet_tuple[1], router_id, area_id,
                                     packet_tuple[6], packet_tuple[7]]
                packet = packet_creator.PacketCreator(header_parameters)

                #  Each neighbor, if any, is a separate parameter in packet tuple - Must be put in single tuple
                neighbors = PacketReader.get_hello_packet_neighbors(packet_tuple)

                packet.create_hello_v2_packet(
                        network_mask, packet_tuple[9], packet_tuple[10], packet_tuple[11], packet_tuple[12],
                        designated_router, backup_designated_router, neighbors)

        return packet

    #  Given a packet byte stream, returns its OSPF version
    @staticmethod
    def get_ospf_version(packet_bytes):
        if (packet_bytes is None) | (packet_bytes == b''):
            raise ValueError("Packet byte stream is too short")
        version = packet_bytes[0]  # First byte of OSPF packet is always its version
        if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
            raise ValueError("Invalid OSPF version")
        return version

    #  Given a packet byte stream, returns its OSPF packet type
    @staticmethod
    def get_ospf_packet_type(packet_bytes):
        if (packet_bytes is None) | (len(packet_bytes) < 2):
            raise ValueError("Packet byte stream is too short")
        packet_type_byte = packet_bytes[1:2]  # Second byte of OSPF packet is always its type
        packet_type = struct.unpack(FORMAT_STRING, packet_type_byte)[0]
        if packet_type not in [conf.PACKET_TYPE_HELLO, conf.PACKET_TYPE_DB_DESCRIPTION, conf.PACKET_TYPE_LS_REQUEST,
                               conf.PACKET_TYPE_LS_UPDATE, conf.PACKET_TYPE_LS_ACKNOWLEDGMENT]:
            raise ValueError("Invalid OSPF packet type")
        return packet_type

    #  Given a OSPF Hello packet, returns the number of its neighbors
    @staticmethod
    def get_hello_packet_neighbor_number(packet_bytes):
        if (packet_bytes is None) | (len(packet_bytes) < conf.OSPFV2_BASE_HELLO_LENGTH):
            raise ValueError("Invalid Hello packet")
        neighbor_number = int((len(packet_bytes) - conf.OSPFV2_BASE_HELLO_LENGTH) / 4)
        return neighbor_number

    #  Given a OSPF Hello packet, returns its neighbors
    @staticmethod
    def get_hello_packet_neighbors(packet_tuple):
        if len(packet_tuple) < PACKET_TUPLE_BASE_LENGTH:
            raise ValueError("Packet tuple is too short")
        neighbors = []
        for i in range(len(packet_tuple) - PACKET_TUPLE_BASE_LENGTH):  # All neighbor parameters, if any
            neighbor_decimal = packet_tuple[PACKET_TUPLE_BASE_LENGTH + i]
            neighbor_ip = utils.Utils.decimal_to_ipv4(neighbor_decimal)
            neighbors.append(neighbor_ip)  # 1st neighbor is in 15th tuple parameter
        return neighbors
