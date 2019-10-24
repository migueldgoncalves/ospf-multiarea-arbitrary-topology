import socket
import struct

'''
Short program to experiment on sending and receiving OSPF multicast packets over a network
This version is dedicated to IPv6
This program must be run as superuser
'''

ALL_OSPF_ROUTERS = 'ff02::5'
MTU = 65565  # Maximum transmission unit - In bytes
OSPF_PROTOCOL_NUMBER = 89
DATA_TO_SEND = b'11111111111111'
PACKETS_TO_WAIT = 5  # Program will wait for 5 packets
PORT = 0  # Has no effect and should be 0 - Still must be included
MULTICAST_STRING_FORMAT = "=I"  # Required when joining multicast groups
INTERFACE_NAME = "ens33"
ENCODING = "UTF-8"


#  Send a packet to the router - Default TTL is 1 and it is what is required, so it remains unchanged
s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, OSPF_PROTOCOL_NUMBER)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(INTERFACE_NAME + '\0').encode(ENCODING))
s.sendto(DATA_TO_SEND, (ALL_OSPF_ROUTERS, PORT))

#  Join a multicast group
group_address_bits = socket.inet_pton(socket.AF_INET6, ALL_OSPF_ROUTERS)
membership_parameters = group_address_bits + struct.pack(MULTICAST_STRING_FORMAT, socket.INADDR_ANY)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, membership_parameters)

#  Listen to packets from the network
packets_captured = 0
while packets_captured < PACKETS_TO_WAIT:
    print("Capturing packet", packets_captured + 1, "...")
    print(s.recvfrom(MTU))
    packets_captured += 1
    print("Packet", packets_captured, "captured")
