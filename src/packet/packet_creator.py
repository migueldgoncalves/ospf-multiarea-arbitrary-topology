import traceback

import general.utils as utils
import packet.header as header
import packet.hello_v2 as hello_v2
import conf.conf as conf

'''
This class serves as an interface to packet creation, storage and manipulation, both for OSPFv2 and OSPFv3
'''


class PacketCreator:
    header = None
    body = None
    utils = utils.Utils()

    #  Packet header is set on creation
    def __init__(self, parameters):
        if parameters[0] == conf.VERSION_IPV4:
            self.header = header.Header(parameters[1], parameters[2], parameters[3], parameters[4], parameters[5])
        elif parameters[0] == conf.VERSION_IPV6:
            pass
        else:
            raise ValueError("Invalid OSPF version")

    #  Creates a full OSPFv2 Hello packet
    def create_hello_v2_packet(self, network_mask, hello_interval, options, router_priority, router_dead_interval,
                               designated_router, backup_designated_router, neighbors):
        try:
            self.body = hello_v2.HelloV2(network_mask, hello_interval, options, router_priority, router_dead_interval,
                                         designated_router, backup_designated_router, neighbors)
            self.set_packet_length()  # Packet length must be set after body is created and before checksum is computed
            self.set_packet_checksum()

            header_bytes = self.header.pack_header()  # With the checksum
            body_bytes = self.body.pack_packet()
            return header_bytes + body_bytes
        except ValueError:  # Thrown if packet body parameters are incorrect
            print(traceback.format_exc())
            return b''

    #  Calculates packet checksum and inserts it on given packet header
    def set_packet_checksum(self):
        if self.body is not None:  # Does nothing if there is no packet body
            self.header.prepare_packet_checksum()  # Clean required fields before checksum calculation

            #  Gets and sets packet checksum - It is set to 0 in the packet sent as argument
            header_bytes = self.header.pack_header()  # Without the checksum
            body_bytes = self.body.pack_packet()
            checksum = self.utils.create_checksum_ipv4(header_bytes + body_bytes)

            self.header.set_checksum(checksum)

    #  Calculates packet length and inserts it on given packet header
    def set_packet_length(self):
        if self.body is not None:  # Does nothing if there is no packet body
            header_bytes = self.header.pack_header()
            body_bytes = self.body.pack_packet()
            packet_length = len(header_bytes + body_bytes)
            self.header.set_length(packet_length)
