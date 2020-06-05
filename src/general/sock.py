import socket
import struct

import conf.conf as conf
import general.utils as utils

'''
This class performs the socket operations in the router
'''

PORT = 0  # Has no effect and should be 0 - Still must be included
MULTICAST_STRING_FORMAT_IPV4 = "4sL"  # Required when joining multicast groups (4s - 4 letter string; L - Signed long)
MULTICAST_STRING_FORMAT_IPV6 = "=I"  # Required when joining multicast groups (= - Native byte order; I - Unsigned int)
ENCODING = "UTF-8"


class Socket:

    def __init__(self):
        self.is_dr = False  # If router is DR/BDR - Global parameter only needed for testing purposes

    #  Listens to IPv4 packets in the network until signaled to stop
    def receive_ipv4(self, pipeline, shutdown, interface, accept_self_packets, is_dr, localhost, network):
        if pipeline is None:
            raise ValueError("No pipeline provided")
        if shutdown is None:
            raise ValueError("No shutdown event provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")
        #  If router is operating on localhost, a list of IP addresses in the network is required
        if localhost & (network is None):
            raise ValueError("No interface IP addresses provided")

        #  Creates socket and binds it to interface
        self.is_dr = is_dr
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Joins multicast group(s)
        group_address_bits = socket.inet_aton(conf.ALL_OSPF_ROUTERS_IPV4)
        membership_parameters = struct.pack(MULTICAST_STRING_FORMAT_IPV4, group_address_bits, socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_parameters)
        if self.is_dr:
            group_address_bits = socket.inet_aton(conf.ALL_DR_IPV4)
            membership_parameters = struct.pack(MULTICAST_STRING_FORMAT_IPV4, group_address_bits, socket.INADDR_ANY)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_parameters)

        #  Listens to packets from the network
        while not shutdown.is_set():
            s.settimeout(0.1)
            try:
                data = s.recvfrom(conf.MTU)  # Includes IP header
                array = Socket.process_ipv4_data(data[0])  # [packet_byte_stream, source_ip_address]
                #  If packet is not from itself OR if packets from itself are allowed
                if (array[1] != utils.Utils.get_ipv4_address_from_interface_name(interface)) | accept_self_packets:
                    if not localhost:
                        pipeline.put(array)
                    #  If router is operating on localhost and packet comes from the network
                    elif localhost & (array[1] in network):
                        pipeline.put(array)
            except socket.timeout:
                pass  # Required since program will block until packet is received
        s.close()

    #  Listens to IPv6 packets in the network until signaled to stop
    def receive_ipv6(self, pipeline, shutdown, interface, accept_self_packets, is_dr, localhost, network):
        if pipeline is None:
            raise ValueError("No pipeline provided")
        if shutdown is None:
            raise ValueError("No shutdown event provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")
        #  If router is operating on localhost, a list of IP addresses in the network is required
        if localhost & (network is None):
            raise ValueError("No interface IP addresses provided")

        #  Creates socket and binds it to interface
        self.is_dr = is_dr
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Joins multicast group(s)
        group_address_bits = socket.inet_pton(socket.AF_INET6, conf.ALL_OSPF_ROUTERS_IPV6)
        membership_parameters = group_address_bits + struct.pack(MULTICAST_STRING_FORMAT_IPV6, socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, membership_parameters)
        if self.is_dr:
            group_address_bits = socket.inet_pton(socket.AF_INET6, conf.ALL_DR_IPV6)
            membership_parameters = group_address_bits + struct.pack(MULTICAST_STRING_FORMAT_IPV6, socket.INADDR_ANY)
            s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, membership_parameters)

        #  Listens to packets from the network
        while not shutdown.is_set():
            s.settimeout(0.1)
            try:
                data = s.recvfrom(conf.MTU)  # Does not include IP header
                packet_bytes = data[0]
                source_ip_address = data[1][0].split('%')[0]
                link_local_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(interface)
                global_address = utils.Utils.get_ipv6_global_address_from_interface_name(interface)
                #  If packet is not from itself OR if packets from itself are allowed
                if (source_ip_address not in [link_local_address, global_address]) | accept_self_packets:
                    if not localhost:
                        pipeline.put([packet_bytes, source_ip_address])
                    #  If router is operating on localhost and packet comes from the network
                    elif localhost & (source_ip_address in network):
                        pipeline.put([packet_bytes, source_ip_address])
            except socket.timeout:
                pass
        s.close()

    #  Sends the supplied IPv4 packet to the supplied address through the supplied interface
    def send_ipv4(self, packet, destination_address, interface):
        if packet is None:
            raise ValueError("No data to send provided")
        if packet.strip() == '':
            raise ValueError("Empty data to send provided")
        if destination_address is None:
            raise ValueError("No destination address provided")
        if destination_address.strip() == '':
            raise ValueError("Empty destination address provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")

        #  Creates socket and binds it to interface - Default TTL is 1 and is the required TTL, so it remains unchanged
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Sends packet
        s.sendto(packet, (destination_address, PORT))
        s.close()

    #  Sends the supplied IPv6 packet to the supplied address through the supplied interface
    def send_ipv6(self, packet, destination_address, interface):
        if packet is None:
            raise ValueError("No data to send provided")
        if packet.strip() == '':
            raise ValueError("Empty data to send provided")
        if destination_address is None:
            raise ValueError("No destination address provided")
        if destination_address.strip() == '':
            raise ValueError("Empty destination address provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")

        #  Creates socket and binds it to interface - Default TTL is 1 and is the required TTL, so it remains unchanged
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, conf.OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Sends packet
        s.sendto(packet, (destination_address, PORT))
        s.close()

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
