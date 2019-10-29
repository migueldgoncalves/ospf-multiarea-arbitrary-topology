import unittest

import packet.header_v2 as header_v2

VERSION = 2
PACKET_TYPE = 1
LENGTH = 44
ROUTER_ID = '3.3.3.3'
AREA_ID = '0.0.0.0'
CHECKSUM = 0
AUTH_TYPE = 0
AUTHENTICATION = 0


class TestPacket(unittest.TestCase):

    def test_print_packet(self):
        packet = header_v2.HeaderV2(VERSION, PACKET_TYPE, LENGTH, ROUTER_ID, AREA_ID, AUTH_TYPE, AUTHENTICATION)
        packet.print_header_packet()
