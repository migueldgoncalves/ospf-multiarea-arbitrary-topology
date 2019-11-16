import unittest

import packet.packet_reader as packet_reader

'''
This class tests the interface to incoming packet processing
'''


#  Full successful run - Instant
class PacketReaderTest(unittest.TestCase):

    #  Successful run - Instant
    def test_convert_bytes_to_packet_successful(self):
        packet_bytes = b'\x02\x01\x00,\x03\x03\x03\x03\x00\x00\x00\x00\xf6\x98\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\x00\xff\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00'
        hello_packet = packet_reader.PacketReader.convert_bytes_to_packet(packet_bytes)
        self.assertEqual(2, hello_packet.version)
