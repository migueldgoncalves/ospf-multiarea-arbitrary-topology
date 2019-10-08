import socket
import os

'''
Short program to experiment on sending and receiving OSPF packets over a network
This version is dedicated to IPv4
This program must be run as superuser
'''

ROUTER_INT_IP = '222.222.1.1'
HOST_INT_IP = '222.222.1.2'
HOST_INTERFACE_NAME = "ens33"
MTU = 1500  # Maximum transmission unit - In bytes
PING_SUCCESSFUL = 0  # Ping command returns 0 if successful
OSPF_PROTOCOL_NUMBER = 89
DATA_TO_SEND = b'11111111111111'
PACKETS_TO_WAIT = 5  # Program will wait for 5 packets
MAX_PORT = 65565
PORT = 0  # Has no effect and should be 0 - Still must be included


#  Test connection with router
if os.system("ping -c 1 " + ROUTER_INT_IP) != PING_SUCCESSFUL:
    print("Router could not be reached - Exiting...")
    exit()
else:
    print("Router successfully reached")

#  Send a packet to the router
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, OSPF_PROTOCOL_NUMBER)
s.bind((HOST_INT_IP, 0))
# s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)  # Not used because the standard IP header will be kept
s.sendto(DATA_TO_SEND, (ROUTER_INT_IP, PORT))

#  Listen to packets from the network
packets_listened = 0
while packets_listened < PACKETS_TO_WAIT:
    print(s.recv(MTU))
    print(s.recvfrom(MAX_PORT))
    packets_listened += 1
