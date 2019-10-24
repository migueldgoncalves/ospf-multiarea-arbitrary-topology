import socket
import struct

'''
This class performs the socket operations in the router
'''

ALL_OSPF_ROUTERS = '224.0.0.5'
ALL_DESIGNATED_ROUTERS = '224.0.0.6'
MTU = 65565  # Maximum transmission unit - In bytes
OSPF_PROTOCOL_NUMBER = 89
PACKETS_TO_WAIT = 5  # Program will wait for 5 packets
PORT = 0  # Has no effect and should be 0 - Still must be included
MULTICAST_STRING_FORMAT = "4sL"  # Required when joining multicast groups
ENCODING = "UTF-8"


class Socket:

    shutdown_flag = 0  # Signals the socket thread to terminate
    is_dr = False  # If router is a DR router

    #  Will listen to packets in the network until signaled to stop
    def receive_ipv4(self, buffer, interface, accept_self_packets, is_dr):
        self.is_dr = is_dr
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, OSPF_PROTOCOL_NUMBER)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(interface + '\0').encode(ENCODING))

        #  Join multicast group(s)
        group_address_bits = socket.inet_aton(ALL_OSPF_ROUTERS)
        membership_parameters = struct.pack(MULTICAST_STRING_FORMAT, group_address_bits, socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_parameters)

        if is_dr:
            group_address_bits = socket.inet_aton(ALL_DESIGNATED_ROUTERS)
            membership_parameters = struct.pack(MULTICAST_STRING_FORMAT, group_address_bits, socket.INADDR_ANY)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_parameters)

        #  Listen to packets from the network
        while not self.shutdown_flag:
            data = s.recvfrom(MTU)
            if data[1][0] != socket.gethostbyname(socket.gethostname()):
                buffer.append(data)
        s.close()
        return ''

    #  Will listen to packets in the network until signaled to stop
    def receive_ipv6(self, buffer, interface, accept_self_packets, is_dr):
        return 0

    def send_ipv4(self, packet, destination_address, source_interface):
        return 0

    def send_ipv6(self, packet, destination_address, source_interface):
        return 0

    def shutdown(self):
        self.shutdown_flag = 1
