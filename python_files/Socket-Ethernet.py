import socket

'''
Short program to experiment on sending and receiving Ethernet frames over a network
This program must be run as superuser
'''

HOST_INTERFACE_NAME = "ens33"
MTU = 65565  # Maximum transmission unit - In bytes
ETH_P_ALL = 0x0003  # All Ethernet packets
DATA_TO_SEND = b'11111111111111'
FRAMES_TO_WAIT = 5  # Program will listen to 5 frames


#  Send a frame to the network
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(ETH_P_ALL))
s.bind((HOST_INTERFACE_NAME, ETH_P_ALL))
s.send(DATA_TO_SEND)

#  Listen to frames from the network
frames_captured = 0
while frames_captured < FRAMES_TO_WAIT:
    print("Capturing frame", frames_captured + 1, "...")
    print(s.recvfrom(MTU))
    frames_captured += 1
    print("Frame", frames_captured, "captured")
