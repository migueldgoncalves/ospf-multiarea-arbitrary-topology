import unittest

import packet.packet_creator as packet_creator
import general.socket_python as socket_python

'''
This class tests the interface to packet creation
'''

#  Header data
VERSION = 2
PACKET_TYPE = 1
ROUTER_ID = '3.3.3.3'
AREA_ID = '0.0.0.0'
AUTH_TYPE = 0
AUTHENTICATION = 0

#  Hello packet data
NETWORK_MASK = '255.255.255.0'
HELLO_INTERVAL = 10
OPTIONS = 2  # Option External Routing must be set
ROUTER_PRIORITY = 0
ROUTER_DEAD_INTERVAL = 40
DESIGNATED_ROUTER = '0.0.0.0'
BACKUP_DESIGNATED_ROUTER = '0.0.0.0'
NEIGHBORS = ('1.1.1.1',)

DESTINATION_ADDRESS = "224.0.0.5"
SOURCE_INTERFACE = "ens33"


#  Full successful run - Instant
class PacketCreatorTest(unittest.TestCase):
    packet_creator = None
    socket = None

    def setUp(self):
        parameters = [VERSION, PACKET_TYPE, ROUTER_ID, AREA_ID, AUTH_TYPE, AUTHENTICATION]
        self.packet_creator = packet_creator.PacketCreator(parameters)
        self.socket = socket_python.Socket()

    def test_create_hello_v2_packet_successful(self):
        hello_packet = self.packet_creator.create_hello_v2_packet(NETWORK_MASK, HELLO_INTERVAL, OPTIONS,
                                                            ROUTER_PRIORITY, ROUTER_DEAD_INTERVAL, DESIGNATED_ROUTER,
                                                            BACKUP_DESIGNATED_ROUTER, NEIGHBORS)
        self.socket.send_ipv4(hello_packet, DESTINATION_ADDRESS, SOURCE_INTERFACE)
