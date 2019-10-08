import socket
import os

'''
Short program to experiment on sending and receiving Ethernet packets over a network
This program must be run as superuser
'''

ROUTER_INT_IP = '222.222.1.1'
HOST_INTERFACE_NAME = "ens33"
MTU = 1500  # Maximum transmission unit - In bytes
PING_SUCCESSFUL = 0  # Ping command returns 0 if successful
OSPF_PROTOCOL_NUMBER = 89
ETH_P_ALL = 0x0003  # All Ethernet packets
DATA_TO_SEND = b'11111111111111'
PACKETS_TO_WAIT = 5  # Program will listen to 5 packets
MAX_PORT = 65565


#  Test connection with router
if os.system("ping -c 1 " + ROUTER_INT_IP) != PING_SUCCESSFUL:
    print("Router could not be reached - Exiting...")
    exit()
else:
    print("Router successfully reached")

#  Send a packet to the network
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(ETH_P_ALL))
s.bind((HOST_INTERFACE_NAME, ETH_P_ALL))
s.send(DATA_TO_SEND)

#  Listen to packets from the network
packets_listened = 0
while packets_listened < PACKETS_TO_WAIT:
    print(s.recvfrom(MAX_PORT))
    packets_listened += 1
