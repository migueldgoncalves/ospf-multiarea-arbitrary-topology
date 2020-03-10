import traceback
import struct

import general.utils as utils
import packet.header as header
import packet.hello as hello
import conf.conf as conf

'''
This class serves as an interface to packet creation, storage and manipulation, both for OSPFv2 and OSPFv3
'''

#  Format strings indicate the format of the byte objects to be created, or converted to other object types
#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.unpack("> B", b'\x01) -> 1
#  H - Unsigned short (2 bytes) - struct.unpack("> H", b'\x00\x01) -> 1
#  L - Unsigned long (4 bytes) - struct.unpack("> L", b'\x00\x00\x00\x01) -> 1
#  Q - Unsigned long long (8 bytes) - struct.unpack("> Q", b'\x00\x00\x00\x00\x00\x00\x00\x01) -> 1
FORMAT_STRING = "> B"


class Packet:
    header = None
    body = None
    utils = utils.Utils()

    #  #  #  #  #  #  #
    #  Main methods   #
    #  #  #  #  #  #  #

    #  Adds an OSPFv2 header to the packet with the provided arguments
    def create_header_v2(self, packet_type, router_id, area_id, auth_type, authentication):
        self.header = header.Header(conf.VERSION_IPV4, packet_type, router_id, area_id, auth_type, authentication, 0)
        self.body = None

    #  Adds an OSPFv3 header to the packet with the provided arguments
    def create_header_v3(self, packet_type, router_id, area_id, instance_id):
        self.header = header.Header(conf.VERSION_IPV6, packet_type, router_id, area_id, 0, 0, instance_id)
        self.body = None

    #  Converts an OSPF packet into a byte stream
    def pack_packet(self):
        if self.header is None:
            raise ValueError("Packet header is not set")
        if self.body is None:
            raise ValueError("Packet body is not set")

        header_bytes = self.header.pack_header()
        body_bytes = self.body.pack_packet_body()
        return header_bytes + body_bytes

    #  Converts a byte stream into an OSPF packet
    @staticmethod
    def unpack_packet(packet_bytes):
        packet_version = Packet.get_ospf_version(packet_bytes)
        packet_type = Packet.get_ospf_packet_type(packet_bytes)

        #  An OSPF packet just with a header, or with less bytes, can immediately be discarded
        if (len(packet_bytes) <= conf.OSPFV2_HEADER_LENGTH) & (packet_version == conf.VERSION_IPV4):
            raise ValueError("OSPFv2 packet byte stream is too short")
        if (len(packet_bytes) <= conf.OSPFV3_HEADER_LENGTH) & (packet_version == conf.VERSION_IPV6):
            raise ValueError("OSPFv3 packet byte stream is too short")

        #  If no exception is thrown, both packet version and type are valid
        packet = Packet()
        if packet_version == conf.VERSION_IPV4:
            header_bytes = packet_bytes[:conf.OSPFV2_HEADER_LENGTH]
            body_bytes = packet_bytes[conf.OSPFV2_HEADER_LENGTH:]
        else:
            header_bytes = packet_bytes[:conf.OSPFV3_HEADER_LENGTH]
            body_bytes = packet_bytes[conf.OSPFV3_HEADER_LENGTH:]

        #  Creates the header and the body of the packet from their byte streams
        packet.header = header.Header.unpack_header(header_bytes, packet_version)
        if packet_type == conf.PACKET_TYPE_HELLO:
            packet.body = hello.Hello.unpack_packet_body(body_bytes, packet_version)
        elif packet_type == conf.PACKET_TYPE_DB_DESCRIPTION:
            pass
        elif packet_type == conf.PACKET_TYPE_LS_REQUEST:
            pass
        elif packet_type == conf.PACKET_TYPE_LS_UPDATE:
            pass
        else:
            pass

        return packet

    #  Adds an OSPFv2 Hello packet body to the packet with the provided arguments
    def create_hello_v2_packet_body(self, network_mask, hello_interval, options, router_priority, router_dead_interval,
                                    designated_router, backup_designated_router, neighbors):
        if self.header is None:
            raise ValueError("Packet header is not set")
        if self.header.version == conf.VERSION_IPV6:
            raise ValueError("Incorrect version for packet body")

        self.body = hello.Hello(network_mask, hello_interval, options, router_priority, router_dead_interval,
                                designated_router, backup_designated_router, neighbors, 0, conf.VERSION_IPV4)
        self.set_packet_length()  # Packet length must be set after body is created and before checksum is computed
        self.set_packet_checksum()

    #  Adds an OSPFv3 Hello packet body to the packet with the provided arguments
    def create_hello_v3_packet_body(self, interface_id, hello_interval, options, router_priority, router_dead_interval,
                                    designated_router, backup_designated_router, neighbors):
        if self.header is None:
            raise ValueError("Packet header is not set")
        if self.header.version == conf.VERSION_IPV4:
            raise ValueError("Incorrect version for packet body")

        self.body = hello.Hello('', hello_interval, options, router_priority, router_dead_interval,
                                designated_router, backup_designated_router, neighbors, interface_id, conf.VERSION_IPV6)
        self.set_packet_length()  # Packet length must be set after body is created and before checksum is computed
        self.set_packet_checksum()

    #  #  #  #  #  #  #   #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #   #

    #  Calculates packet checksum and inserts it on given packet header
    def set_packet_checksum(self):
        if self.body is not None:  # Does nothing if there is no packet body
            bogus_header = self.header
            bogus_header.prepare_packet_checksum()  # Cleans required fields before checksum calculation

            #  Calculates and sets packet checksum - It is set to 0 in the packet sent as argument
            header_bytes = bogus_header.pack_header()  # Without the checksum
            body_bytes = self.body.pack_packet_body()
            checksum = self.utils.create_checksum_ospfv2(header_bytes + body_bytes)

            self.header.set_checksum(checksum)

    #  Calculates packet length and inserts it on given packet header
    def set_packet_length(self):
        if self.body is not None:  # Does nothing if there is no packet body
            header_bytes = self.header.pack_header()
            body_bytes = self.body.pack_packet_body()
            packet_length = len(header_bytes + body_bytes)
            self.header.set_length(packet_length)

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
