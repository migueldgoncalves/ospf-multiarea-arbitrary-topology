import socket
import struct
import queue
import multiprocessing

import conf.conf as conf
import general.utils as utils
import packet.packet as packet
import lsa.lsa as lsa

'''
This class performs the socket operations in the router
'''

PORT = 0  # Has no effect and should be 0 - Still must be included
MULTICAST_STRING_FORMAT_IPV4 = "4sL"  # Required when joining multicast groups (4s - 4 letter string; L - Signed long)
MULTICAST_STRING_FORMAT_IPV6 = "=I"  # Required when joining multicast groups (= - Native byte order; I - Unsigned int)
ENCODING = "UTF-8"


class Socket:

    def __init__(self):
        #  Test parameters
        self.is_dr = multiprocessing.Event()  # Set if router is DR/BDR
        self.exit_pipeline_v2 = queue.Queue()
        self.exit_pipeline_v3 = queue.Queue()

    #  #  #  #  #  #  #
    #  Main methods  #
    #  #  #  #  #  #  #

    #  Listens to IPv4 packets in the network until signaled to stop
    def receive_ipv4(self, pipeline, shutdown, interface, accept_self_packets, is_dr, localhost):
        if localhost:  # No sockets will be used in the integration tests
            return

        if pipeline is None:
            raise ValueError("No pipeline provided")
        if shutdown is None:
            raise ValueError("No shutdown event provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")

        #  Creates socket and binds it to interface
        self.is_dr = is_dr
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Joins multicast groups and listens to packets from the network
        flag = False
        Socket.join_multicast_group(s, interface, conf.ALL_OSPF_ROUTERS_IPV4, conf.VERSION_IPV4)
        while not shutdown.is_set():
            if is_dr.is_set() != flag:  # Interface state has just changed to or from DR/BDR
                if is_dr.is_set():  # DR/BDR
                    Socket.join_multicast_group(s, interface, conf.ALL_DR_IPV4, conf.VERSION_IPV4)
                else:  # Non-DR/BDR
                    Socket.leave_multicast_group(s, interface, conf.ALL_DR_IPV4, conf.VERSION_IPV4)
                flag = is_dr.is_set()
            s.settimeout(0.1)
            try:
                data = s.recvfrom(conf.MTU)  # Includes IP header
                array = Socket.process_ipv4_data(data[0])  # [packet_byte_stream, source_ip_address]
                #  If packet is not from itself OR if packets from itself are allowed
                if (array[1] != utils.Utils.interface_name_to_ipv4_address(interface)) | accept_self_packets:
                    pipeline.put(array)
            except socket.timeout:
                pass  # Required since program will block until packet is received
        s.close()

    #  Listens to IPv6 packets in the network until signaled to stop
    def receive_ipv6(self, pipeline, shutdown, interface, accept_self_packets, is_dr, localhost, router_id):
        if localhost:  # No sockets will be used in the integration tests
            return

        if pipeline is None:
            raise ValueError("No pipeline provided")
        if shutdown is None:
            raise ValueError("No shutdown event provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")

        #  Creates socket and binds it to interface
        self.is_dr = is_dr
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Joins multicast groups and listens to packets from the network
        flag = False
        Socket.join_multicast_group(s, interface, conf.ALL_OSPF_ROUTERS_IPV6, conf.VERSION_IPV6)
        while not shutdown.is_set():
            if is_dr.is_set() != flag:  # Interface state has just changed to or from DR/BDR
                if is_dr.is_set():  # DR/BDR
                    Socket.join_multicast_group(s, interface, conf.ALL_DR_IPV6, conf.VERSION_IPV6)
                else:  # Non-DR/BDR
                    Socket.leave_multicast_group(s, interface, conf.ALL_DR_IPV6, conf.VERSION_IPV6)
                flag = is_dr.is_set()
            s.settimeout(0.1)
            try:
                data = s.recvfrom(conf.MTU)  # Does not include IP header
                #packet_bytes = Socket.remove_extension_pseudo_headers(data[0], interface, router_id)
                packet_bytes = data[0]
                source_ip_address = data[1][0].split('%')[0]
                link_local_address = utils.Utils.interface_name_to_ipv6_link_local_address(interface)
                global_address = utils.Utils.interface_name_to_ipv6_global_address(interface)
                #  If packet is not from itself OR if packets from itself are allowed
                if (source_ip_address not in [link_local_address, global_address]) | accept_self_packets:
                    pipeline.put([packet_bytes, source_ip_address])
            except socket.timeout:
                pass
        s.close()

    #  Sends the supplied IPv4 packet to the supplied address through the supplied interface
    def send_ipv4(self, packet_bytes, destination_address, interface, localhost):
        if packet_bytes is None:
            raise ValueError("No data to send provided")
        if packet_bytes.strip() == '':
            raise ValueError("Empty data to send provided")
        if destination_address is None:
            raise ValueError("No destination address provided")
        if destination_address.strip() == '':
            raise ValueError("Empty destination address provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")
        packet_bytes = self.is_packet_checksum_valid(packet_bytes, conf.VERSION_IPV4, '', '')

        if localhost:  # Socket will not be used in integration tests
            source_address = utils.Utils.interface_name_to_ipv4_address(interface)
            data = [packet_bytes, source_address, destination_address]
            self.exit_pipeline_v2.put(data)
            return

        #  Creates socket and binds it to interface - Default TTL is 1 and is the required TTL, so it remains unchanged
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Sends packet
        s.sendto(packet_bytes, (destination_address, PORT))
        s.close()

    #  Sends the supplied IPv6 packet to the supplied address through the supplied interface
    def send_ipv6(self, packet_bytes, destination_address, interface, localhost):
        if packet_bytes is None:
            raise ValueError("No data to send provided")
        if packet_bytes.strip() == '':
            raise ValueError("Empty data to send provided")
        if destination_address is None:
            raise ValueError("No destination address provided")
        if destination_address.strip() == '':
            raise ValueError("Empty destination address provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")
        source_address = utils.Utils.interface_name_to_ipv6_link_local_address(interface)
        packet_bytes = self.is_packet_checksum_valid(
            packet_bytes, conf.VERSION_IPV6, source_address, destination_address)
        #packet_bytes = Socket.add_extension_pseudo_headers(packet_bytes, source_address, destination_address)

        if localhost:  # Socket will not be used in integration tests
            data = [packet_bytes, source_address, destination_address]
            self.exit_pipeline_v3.put(data)
            return

        #  Creates socket and binds it to interface - Default TTL is 1 and is the required TTL, so it remains unchanged
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Sends packet
        s.sendto(packet_bytes, (destination_address, PORT))
        s.close()

    #  #  #  #  #  #  #  #  #  #
    #  Multicast group methods  #
    #  #  #  #  #  #  #  #  #  #

    #  Joins provided multicast group
    @staticmethod
    def join_multicast_group(s, interface_name, multicast_address, ospf_version):
        if ospf_version == conf.VERSION_IPV4:
            action = socket.IP_ADD_MEMBERSHIP
        elif ospf_version == conf.VERSION_IPV6:
            action = socket.IPV6_JOIN_GROUP
        else:
            raise ValueError("Invalid OSPF version")
        Socket.join_leave_multicast_group(s, interface_name, multicast_address, action, ospf_version)

    #  Leaves provided multicast group
    @staticmethod
    def leave_multicast_group(s, interface_name, multicast_address, ospf_version):
        if ospf_version == conf.VERSION_IPV4:
            action = socket.IP_DROP_MEMBERSHIP
        elif ospf_version == conf.VERSION_IPV6:
            action = socket.IPV6_LEAVE_GROUP
        else:
            raise ValueError("Invalid OSPF version")
        Socket.join_leave_multicast_group(s, interface_name, multicast_address, action, ospf_version)

    #  Joins or leaves provided multicast group according to provided action
    @staticmethod
    def join_leave_multicast_group(s, interface_name, multicast_address, action, ospf_version):
        if ospf_version == conf.VERSION_IPV4:
            group_address_bits = socket.inet_aton(multicast_address)
            interface_index = socket.if_nametoindex(interface_name)
            membership_parameters = struct.pack(MULTICAST_STRING_FORMAT_IPV4, group_address_bits, interface_index)
            s.setsockopt(socket.IPPROTO_IP, action, membership_parameters)
        else:
            group_address_bits = socket.inet_pton(socket.AF_INET6, multicast_address)
            interface_index = socket.if_nametoindex(interface_name)
            membership_parameters = group_address_bits + struct.pack(MULTICAST_STRING_FORMAT_IPV6, interface_index)
            s.setsockopt(socket.IPPROTO_IPV6, action, membership_parameters)

    #  #  #  #  #  #  #  #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #  #

    #  Processes incoming IPv4 data
    @staticmethod
    def process_ipv4_data(byte_stream):
        if len(byte_stream) < conf.IPV4_HEADER_BASE_LENGTH:  # IPv4 socket returns packets with IP header
            return ValueError("Byte stream too short")
        ospf_packet = byte_stream[conf.IPV4_HEADER_BASE_LENGTH:]  # First bytes in byte array are the IPv4 header

        #  Source IPv4 address starts at 13th byte of IPv4 header
        source_ip_bytes = byte_stream[conf.SOURCE_IPV4_ADDRESS_1ST_BYTE:
                                      conf.SOURCE_IPV4_ADDRESS_1ST_BYTE + conf.IPV4_ADDRESS_BYTE_LENGTH]
        source_ip_address = utils.Utils.decimal_to_ipv4(int.from_bytes(source_ip_bytes, byteorder="big"))

        return [ospf_packet, source_ip_address]

    #  Launches warning if packet checksum is invalid
    @staticmethod
    def is_packet_checksum_valid(packet_bytes, version, source_address, destination_address):
        packet_object = packet.Packet.unpack_packet(packet_bytes)
        # print("Sending packet", packet_object, source_address)
        if not packet_object.is_packet_checksum_valid(source_address, destination_address):
            if version == conf.VERSION_IPV6:
                packet_object.header.source_ipv6_address = source_address
                packet_object.header.destination_ipv6_address = destination_address
            packet_object.set_packet_length()
            packet_object.set_packet_checksum()
            packet_bytes = packet_object.pack_packet()
        return packet_bytes

    #  The Cisco routers being used appear to treat LSAs with unknown types in OSPFv3 as if they all had the same type.
    #  If a router sends a LSA with type 18, and the Cisco router has a LSA from the router with type 17 and an higher
    #  Sequence Number, it drops the new LSA and sends the LSA with type 17 to the router
    #  The following lines append a pseudo-header with constant LS type to all extension LSAs being sent
    '''@staticmethod
    def add_extension_pseudo_headers(packet_bytes, source_address, destination_address):
        if struct.unpack("> B", packet_bytes[1:2])[0] != conf.PACKET_TYPE_LS_UPDATE:
            return packet_bytes  # Nothing to do

        packet_header = packet_bytes[:2] + b'\x00\x00' + packet_bytes[4:12] + b'\x00\x00' + packet_bytes[14:16]
        packet_body_to_process = packet_bytes[conf.OSPFV3_PACKET_HEADER_LENGTH + 4:]  # Number of LSAs field left out
        new_packet_body = packet_bytes[conf.OSPFV3_PACKET_HEADER_LENGTH:conf.OSPFV3_PACKET_HEADER_LENGTH + 4]
        while len(packet_body_to_process) > 0:
            lsa_length = struct.unpack("> H", packet_body_to_process[18:20])[0]
            lsa_bytes = packet_body_to_process[:lsa_length]
            packet_body_to_process = packet_body_to_process[lsa_length:]  # Removes LSA from bytes to process
            if struct.unpack("> B", lsa_bytes[3:4])[0] in [  # Overlay LSA
                conf.LSA_TYPE_EXTENSION_ABR_LSA, conf.LSA_TYPE_EXTENSION_PREFIX_LSA,
                    conf.LSA_TYPE_EXTENSION_ASBR_LSA]:
                advertising_router = utils.Utils.decimal_to_ipv4(struct.unpack("> L", packet_bytes[4:8])[0])
                pseudo_lsa_header = lsa.Lsa()
                pseudo_lsa_header.create_extension_header(  # LS Type is fixed
                    conf.MAX_AGE, conf.OPTIONS_V3, 0, conf.LSA_TYPE_EXTENSION_ABR_LSA, advertising_router,
                    conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
                pseudo_lsa_header = pseudo_lsa_header.pack_header()
                lsa_new_length = (conf.LSA_HEADER_LENGTH + len(lsa_bytes))
                lsa_new_checksum = utils.Utils.create_fletcher_checksum(  # Leaves LS Age out
                    pseudo_lsa_header[2:16] + b'\x00\x00' + struct.pack("> H", lsa_new_length) + lsa_bytes)
                pseudo_lsa_header = pseudo_lsa_header[:16] + struct.pack("> H", lsa_new_checksum) + \
                                    struct.pack("> H", lsa_new_length)  # Restores LS Age bytes
                lsa_bytes = pseudo_lsa_header + lsa_bytes
            new_packet_body += lsa_bytes
        packet_new_length = len(packet_header + new_packet_body)
        packet_header = packet_header[:2] + struct.pack("> H", packet_new_length) + packet_header[4:16]
        packet_new_checksum = utils.Utils.create_checksum_ospfv3(  # Includes packet length
            packet_header + new_packet_body, source_address, destination_address)
        packet_header = packet_header[:12] + struct.pack("> H", packet_new_checksum) + packet_header[14:16]
        return packet_header + new_packet_body

    #  Given a LS Update packet in OSPFv3, return the pseudo headers from any extension LSAs in the packet
    @staticmethod
    def remove_extension_pseudo_headers(packet_bytes, interface, router_id):
        if struct.unpack("> B", packet_bytes[1:2])[0] != conf.PACKET_TYPE_LS_UPDATE:
            return packet_bytes  # Nothing to do

        ls_ack_bytes = b''  # Interface won't be able to acknowledge extension LSAs - It must be done here
        packet_header = packet_bytes[:2] + b'\x00\x00' + packet_bytes[4:12] + b'\x00\x00' + packet_bytes[14:16]
        packet_body_to_process = packet_bytes[conf.OSPFV3_PACKET_HEADER_LENGTH + 4:]
        new_packet_body = packet_bytes[conf.OSPFV3_PACKET_HEADER_LENGTH:conf.OSPFV3_PACKET_HEADER_LENGTH + 4]
        while len(packet_body_to_process) > 0:
            lsa_length = struct.unpack("> H", packet_body_to_process[18:20])[0]
            lsa_bytes = packet_body_to_process[:lsa_length]
            packet_body_to_process = packet_body_to_process[lsa_length:]
            if struct.unpack("> B", lsa_bytes[3:4])[0] in [  # Overlay LSA
                conf.LSA_TYPE_EXTENSION_ABR_LSA, conf.LSA_TYPE_EXTENSION_PREFIX_LSA,
                    conf.LSA_TYPE_EXTENSION_ASBR_LSA]:
                ls_ack_bytes += lsa_bytes[:conf.LSA_HEADER_LENGTH]
                lsa_bytes = lsa_bytes[conf.LSA_HEADER_LENGTH:]
            new_packet_body += lsa_bytes
        packet_new_length = len(packet_header + new_packet_body)
        packet_header = packet_bytes[:2] + struct.pack("> H", packet_new_length) + packet_bytes[4:16]

        #  Sends LS Ack packet with pseudo headers of extension LSAs - Interface does not receive the pseudo headers
        if len(ls_ack_bytes) > 0:  # At least one overlay LSA was received
            area_id = utils.Utils.decimal_to_ipv4(struct.unpack("> L", ls_ack_bytes[4:8])[0])
            ls_ack_packet = packet.Packet()
            source_address = utils.Utils.interface_name_to_ipv6_link_local_address(interface)
            destination_address = conf.ALL_OSPF_ROUTERS_IPV6
            ls_ack_packet.create_header_v3(
                conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, router_id, area_id, 0, source_address, destination_address)
            ls_ack_packet.create_ls_acknowledgement_packet_body(conf.VERSION_IPV6)
            while len(ls_ack_bytes) > 0:
                lsa_header = ls_ack_bytes[:conf.LSA_HEADER_LENGTH]
                ls_ack_packet.add_lsa_header(lsa.Lsa.unpack_header(lsa_header, conf.VERSION_IPV6))
                ls_ack_bytes = ls_ack_bytes[conf.LSA_HEADER_LENGTH:]
            s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))
            s.sendto(ls_ack_packet.pack_packet(), (destination_address, PORT))
            s.close()

        return packet_header + new_packet_body'''
