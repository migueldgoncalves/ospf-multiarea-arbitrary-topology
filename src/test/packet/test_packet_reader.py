import unittest

import packet.packet_reader as packet_reader

'''
This class tests the interface to incoming packet processing
'''


#  Full successful run - Instant
class PacketReaderTest(unittest.TestCase):

    #  Successful run - Instant
    def test_convert_bytes_to_packet_successful(self):
        packet_bytes = b'\x02\x01\x00,\x04\x04\x04\x04\x00\x00\x00\x00\xf6\x98\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\x00\xff\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00'
        hello_packet = packet_reader.PacketReader.convert_bytes_to_packet(packet_bytes)

        #  Packet header checking
        self.assertEqual(2, hello_packet.header.version)
        self.assertEqual(1, hello_packet.header.packet_type)
        self.assertEqual(44, hello_packet.header.length)
        self.assertEqual('4.4.4.4', hello_packet.header.router_id)
        self.assertEqual("0.0.0.0", hello_packet.header.area_id)
        self.assertEqual(62614, hello_packet.header.checksum)
        self.assertEqual(0, hello_packet.header.auth_type)
        self.assertEqual(0, hello_packet.header.authentication)

        #  Packet body checking
        self.assertEqual('255.255.255.0', hello_packet.body.network_mask)
        self.assertEqual(10, hello_packet.body.hello_interval)
        self.assertEqual(2, hello_packet.body.options)
        self.assertEqual(1, hello_packet.body.router_priority)
        self.assertEqual(40, hello_packet.body.router_dead_interval)
        self.assertEqual("0.0.0.0", hello_packet.body.designated_router)
        self.assertEqual("0.0.0.0", hello_packet.body.backup_designated_router)
        self.assertEqual(0, len(hello_packet.body.neighbors))

    #  Successful run - Instant
    def test_get_hello_packet_neighbors(self):
        packet_tuple = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.assertEqual(0, len(packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)))

        packet_tuple = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16843009)
        self.assertEqual(1, len(packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)))
        self.assertEqual('1.1.1.1', packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)[0])

        packet_tuple = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16843009, 33686018)
        self.assertEqual(2, len(packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)))
        self.assertEqual('1.1.1.1', packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)[0])
        self.assertEqual('2.2.2.2', packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)[1])

        packet_tuple = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16843009, 33686018, 50529027)
        self.assertEqual(3, len(packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)))
        self.assertEqual('1.1.1.1', packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)[0])
        self.assertEqual('2.2.2.2', packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)[1])
        self.assertEqual('3.3.3.3', packet_reader.PacketReader.get_hello_packet_neighbors(packet_tuple)[2])
