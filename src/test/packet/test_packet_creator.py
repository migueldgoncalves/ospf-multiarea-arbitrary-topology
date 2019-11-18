import unittest

import packet.packet_creator as packet_creator
import conf.conf as conf

'''
This class tests the interface to packet creation, storage and manipulation
'''


#  Full successful run - Instant
class PacketCreatorTest(unittest.TestCase):
    packet_type = 0
    router_id = ''
    area_id = ''
    auth_type = 0
    authentication = 0
    packet_creator_v2 = None

    def setUp(self):
        self.packet_type = conf.PACKET_TYPE_HELLO
        self.router_id = conf.ROUTER_ID
        self.area_id = conf.BACKBONE_AREA
        self.auth_type = conf.NULL_AUTHENTICATION
        self.authentication = conf.DEFAULT_AUTH
        parameters = [conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type,
                      self.authentication]
        self.packet_creator_v2 = packet_creator.PacketCreator(parameters)

    #  Successful run - Instant
    def test_constructor_successful(self):
        self.assertIsNotNone(self.packet_creator_v2.header)
        self.assertIsNone(self.packet_creator_v2.body)
        self.assertEqual(self.area_id, self.packet_creator_v2.header.area_id)
        self.assertEqual(0, self.packet_creator_v2.header.length)
        self.assertEqual(0, self.packet_creator_v2.header.checksum)

        packet_creator_v3 = packet_creator.PacketCreator([conf.VERSION_IPV6])
        self.assertIsNone(packet_creator_v3.header)
        self.assertIsNone(packet_creator_v3.body)

    #  Successful run - Instant
    def test_constructor_invalid_parameters(self):
        invalid_version = 0
        with self.assertRaises(ValueError):
            packet_creator.PacketCreator([invalid_version])
        invalid_version = 'Invalid version'
        with self.assertRaises(ValueError):
            packet_creator.PacketCreator([invalid_version])
        with self.assertRaises(ValueError):
            packet_creator.PacketCreator(invalid_version)

    #  Successful run - Instant
    def test_create_hello_v2_packet_successful(self):
        network_mask = '0.0.0.0'
        hello_interval = conf.HELLO_INTERVAL
        options = conf.OPTIONS
        router_priority = conf.ROUTER_PRIORITY
        router_dead_interval = conf.ROUTER_DEAD_INTERVAL
        designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        neighbors = ()
        hello_packet = self.packet_creator_v2.\
            create_hello_v2_packet(network_mask, hello_interval, options, router_priority, router_dead_interval,
                                   designated_router, backup_designated_router, neighbors)

        self.assertEqual(hello_packet, self.packet_creator_v2.header.pack_header() +
                         self.packet_creator_v2.body.pack_packet())
        self.assertEqual(44, self.packet_creator_v2.header.length)
        self.assertEqual(62873, self.packet_creator_v2.header.checksum)
        self.assertEqual(network_mask, self.packet_creator_v2.body.network_mask)

        #  Ensure checksum and length are updated when body parameters are updated

        neighbors = ('1.1.1.1',)
        hello_packet = self.packet_creator_v2.\
            create_hello_v2_packet(network_mask, hello_interval, options, router_priority, router_dead_interval,
                                   designated_router, backup_designated_router, neighbors)

        self.assertEqual(hello_packet, self.packet_creator_v2.header.pack_header() +
                         self.packet_creator_v2.body.pack_packet())
        self.assertEqual(48, self.packet_creator_v2.header.length)
        self.assertEqual(62355, self.packet_creator_v2.header.checksum)
        self.assertEqual(network_mask, self.packet_creator_v2.body.network_mask)

        neighbors = ('1.1.1.1', '2.2.2.2')
        hello_packet = self.packet_creator_v2.\
            create_hello_v2_packet(network_mask, hello_interval, options, router_priority, router_dead_interval,
                                   designated_router, backup_designated_router, neighbors)

        self.assertEqual(hello_packet, self.packet_creator_v2.header.pack_header() +
                         self.packet_creator_v2.body.pack_packet())
        self.assertEqual(52, self.packet_creator_v2.header.length)
        self.assertEqual(61323, self.packet_creator_v2.header.checksum)
        self.assertEqual(network_mask, self.packet_creator_v2.body.network_mask)

    #  Successful run - Instant
    def test_create_hello_v2_packet_invalid_parameters(self):
        self.assertEqual(b'', self.packet_creator_v2.create_hello_v2_packet('', 0, '', 0, 0, '', '', ('',)))
        self.assertEqual(0, self.packet_creator_v2.header.length)
        self.assertEqual(0, self.packet_creator_v2.header.checksum)
        self.assertEqual(self.area_id, self.packet_creator_v2.header.area_id)
        self.assertIsNone(self.packet_creator_v2.body)

    #  Successful run - Instant
    def test_set_packet_checksum_no_packet_body(self):
        self.packet_creator_v2.set_packet_checksum()
        self.assertEqual(0, self.packet_creator_v2.header.length)
        self.assertEqual(0, self.packet_creator_v2.header.checksum)
        self.assertEqual(self.area_id, self.packet_creator_v2.header.area_id)
        self.assertIsNone(self.packet_creator_v2.body)

    #  Successful run - Instant
    def test_set_packet_length_no_packet_body(self):
        self.packet_creator_v2.set_packet_length()
        self.assertEqual(0, self.packet_creator_v2.header.length)
        self.assertEqual(0, self.packet_creator_v2.header.checksum)
        self.assertEqual(self.area_id, self.packet_creator_v2.header.area_id)
        self.assertIsNone(self.packet_creator_v2.body)

    def tearDown(self):
        self.packet_type = 0
        self.router_id = ''
        self.area_id = ''
        self.auth_type = 0
        self.authentication = 0
        self.packet_creator_v2 = None
