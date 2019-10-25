import socket
import struct

'''
This class performs the socket operations in the router
'''

ALL_OSPF_ROUTERS_IPV4 = '224.0.0.5'
ALL_DESIGNATED_ROUTERS_IPV4 = '224.0.0.6'
ALL_OSPF_ROUTERS_IPV6 = 'ff02::5'
ALL_DESIGNATED_ROUTERS_IPV6 = 'ff02::6'

MTU = 65565  # Maximum transmission unit - In bytes
OSPF_PROTOCOL_NUMBER = 89
PORT = 0  # Has no effect and should be 0 - Still must be included
MULTICAST_STRING_FORMAT_IPV4 = "4sL"  # Required when joining multicast groups (4s - 4 letter string; L - Signed long)
MULTICAST_STRING_FORMAT_IPV6 = "=I"  # Required when joining multicast groups (= - Native byte order; I - Unsigned int)
ENCODING = "UTF-8"


class Socket:

    is_dr = False  # If router is a DR router - Only needed for testing purposes

    #  Listen to IPv4 packets in the network until signaled to stop
    def receive_ipv4(self, pipeline, shutdown, interface, accept_self_packets, is_dr):
        if pipeline is None:
            raise ValueError("No pipeline provided")
        if shutdown is None:
            raise ValueError("No shutdown event provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")

        #  Create socket and binds it to interface
        self.is_dr = is_dr
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Join multicast group(s)
        group_address_bits = socket.inet_aton(ALL_OSPF_ROUTERS_IPV4)
        membership_parameters = struct.pack(MULTICAST_STRING_FORMAT_IPV4, group_address_bits, socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_parameters)
        if self.is_dr:
            group_address_bits = socket.inet_aton(ALL_DESIGNATED_ROUTERS_IPV4)
            membership_parameters = struct.pack(MULTICAST_STRING_FORMAT_IPV4, group_address_bits, socket.INADDR_ANY)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_parameters)

        #  Listen to packets from the network
        while not shutdown.is_set():
            data = s.recvfrom(MTU)
            #  If packet is not from itself OR if packets from itself are allowed
            if (data[1][0] != socket.gethostbyname(socket.gethostname())) | accept_self_packets:
                pipeline.put(data[0])
        s.close()

    #  Listen to IPv6 to packets in the network until signaled to stop
    def receive_ipv6(self, pipeline, shutdown, interface, accept_self_packets, is_dr):
        if pipeline is None:
            raise ValueError("No pipeline provided")
        if shutdown is None:
            raise ValueError("No shutdown event provided")
        if interface is None:
            raise ValueError("No interface to bind provided")
        if interface.strip() == '':
            raise ValueError("Empty interface to bind provided")

        #  Create socket and binds it to interface
        self.is_dr = is_dr
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Join multicast group(s)
        group_address_bits = socket.inet_pton(socket.AF_INET6, ALL_OSPF_ROUTERS_IPV6)
        membership_parameters = group_address_bits + struct.pack(MULTICAST_STRING_FORMAT_IPV6, socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, membership_parameters)
        if self.is_dr:
            group_address_bits = socket.inet_pton(socket.AF_INET6, ALL_DESIGNATED_ROUTERS_IPV6)
            membership_parameters = group_address_bits + struct.pack(MULTICAST_STRING_FORMAT_IPV6, socket.INADDR_ANY)
            s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, membership_parameters)

        #  Listen to packets from the network
        while not shutdown.is_set():
            data = s.recvfrom(MTU)
            #  If packet is not from itself OR if packets from itself are allowed
            if (data[1][0].split()[0] != socket.getaddrinfo(socket.gethostname(), PORT,
                                                            socket.AF_INET6)[0][4][0]) | accept_self_packets:
                pipeline.put(data[0])
        s.close()

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

        #  Create socket and bind it to interface - Default TTL is 1 and it is what is required, so it remains unchanged
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Send packet
        s.sendto(packet, (destination_address, PORT))
        s.close()

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

        #  Create socket and bind it to interface - Default TTL is 1 and it is what is required, so it remains unchanged
        s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Send packet
        s.sendto(packet, (destination_address, PORT))
        s.close()

