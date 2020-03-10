import unittest

import packet.packet as packet
import conf.conf as conf

'''
This class tests the interface to packet creation, storage and manipulation
'''


#  Full successful run - Instant
class PacketTest(unittest.TestCase):
    packet_type = 0
    router_id = '0.0.0.0'
    area_id = '0.0.0.0'
    auth_type = 0
    authentication = 0
    instance_id = 0
    packet_v2 = None
    packet_v3 = None

    def setUp(self):
        self.packet_type = conf.PACKET_TYPE_HELLO
        self.router_id = '1.1.1.1'
        self.area_id = '2.2.2.2'
        self.auth_type = 1
        self.authentication = 2
        self.instance_id = 3
        self.packet_v2 = packet.Packet()
        self.packet_v2.create_header_v2(
            self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication)
        self.packet_v3 = packet.Packet()
        self.packet_v3.create_header_v3(self.packet_type, self.router_id, self.area_id, self.instance_id)

    #  Successful run - Instant
    def test_create_header_successful(self):
        self.assertIsNotNone(self.packet_v2.header)
        self.assertIsNotNone(self.packet_v3.header)
        self.assertIsNone(self.packet_v2.body)
        self.assertIsNone(self.packet_v3.body)

        self.assertEqual(self.packet_type, self.packet_v2.header.packet_type)
        self.assertEqual(self.packet_type, self.packet_v3.header.packet_type)
        self.assertEqual(self.authentication, self.packet_v2.header.authentication)
        self.assertEqual(self.instance_id, self.packet_v3.header.instance_id)

        self.packet_v2.create_header_v2(
            self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication)
        self.packet_v3.create_header_v3(self.packet_type, self.router_id, self.area_id, self.instance_id)
        self.assertIsNone(self.packet_v2.body)
        self.assertIsNone(self.packet_v3.body)

    #  Successful run - Instant
    def test_create_header_invalid_parameters(self):
        with self.assertRaises(ValueError):
            self.packet_v2.create_header_v2(0, self.router_id, self.area_id, self.auth_type, self.authentication)
        with self.assertRaises(ValueError):
            self.packet_v3.create_header_v3(0, self.router_id, self.area_id, self.instance_id)

    # Successful run - Instant
    def test_pack_packet_successful(self):
        network_mask = '255.255.255.0'
        hello_interval = 10
        options = 2
        router_priority = 1
        router_dead_interval = 40
        designated_router = '222.222.1.1'
        backup_designated_router = '0.0.0.0'
        neighbors = ('1.1.1.1',)
        interface_id = 1
        self.packet_v2.create_hello_v2_packet_body(
            network_mask, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)
        self.packet_v3.create_hello_v3_packet_body(
            interface_id, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        packet_v2_bytes = b''
        packet_v3_bytes = b''

        self.assertEqual(packet_v2_bytes, self.packet_v2.pack_packet())
        self.assertEqual(packet_v3_bytes, self.packet_v3.pack_packet())

    #  Successful run - Instant
    def test_unpack_hello_packet_successful(self):
        packet_bytes = b'\x02\x01\x00,\x01\x01\x01\x01\x00\x00\x00\x00\n\xbd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\xff\xff\xff\x00\x00\n\x12\x01\x00\x00\x00(\xde\xde\x01\x01\x00\x00\x00\x00'
        hello_packet = packet.Packet.unpack_packet(packet_bytes)

        #  OSPFv2 packet header checking
        self.assertEqual(2, hello_packet.header.version)
        self.assertEqual(1, hello_packet.header.packet_type)
        self.assertEqual(44, hello_packet.header.length)
        self.assertEqual('1.1.1.1', hello_packet.header.router_id)
        self.assertEqual("0.0.0.0", hello_packet.header.area_id)
        self.assertEqual(2749, hello_packet.header.checksum)
        self.assertEqual(0, hello_packet.header.auth_type)
        self.assertEqual(0, hello_packet.header.authentication)

        #  OSPFv2 packet body checking
        self.assertEqual('255.255.255.0', hello_packet.body.network_mask)
        self.assertEqual(10, hello_packet.body.hello_interval)
        self.assertEqual(18, hello_packet.body.options)
        self.assertEqual(1, hello_packet.body.router_priority)
        self.assertEqual(40, hello_packet.body.router_dead_interval)
        self.assertEqual('222.222.1.1', hello_packet.body.designated_router)
        self.assertEqual('0.0.0.0', hello_packet.body.backup_designated_router)
        self.assertEqual(0, len(hello_packet.body.neighbors))

        packet_bytes = b'\x03\x01\x00$\x01\x01\x01\x01\x00\x00\x00\x00"@\x00\x00\x00\x00\x00\x06\x01\x00\x00\x13\x00' \
                       b'\n\x00(\x01\x01\x01\x01\x00\x00\x00\x00'
        hello_packet = packet.Packet.unpack_packet(packet_bytes)

        #  OSPFv3 packet header checking
        self.assertEqual(3, hello_packet.header.version)
        self.assertEqual(1, hello_packet.header.packet_type)
        self.assertEqual(36, hello_packet.header.length)
        self.assertEqual('1.1.1.1', hello_packet.header.router_id)
        self.assertEqual('0.0.0.0', hello_packet.header.area_id)
        self.assertEqual(8768, hello_packet.header.checksum)
        self.assertEqual(0, hello_packet.header.instance_id)

        #  OSPFv3 packet body checking
        self.assertEqual(6, hello_packet.body.interface_id)
        self.assertEqual(1, hello_packet.body.router_priority)
        self.assertEqual(19, hello_packet.body.options)
        self.assertEqual(10, hello_packet.body.hello_interval)
        self.assertEqual(40, hello_packet.body.router_dead_interval)
        self.assertEqual('1.1.1.1', hello_packet.body.designated_router)
        self.assertEqual('0.0.0.0', hello_packet.body.backup_designated_router)

    #  Successful run - Instant
    def unpack_packet_invalid_parameters(self):
        packet_bytes = b'\x01\x01\x00,\x01\x01\x01\x01\x00\x00\x00\x00\n\xbd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\xff\xff\xff\x00\x00\n\x12\x01\x00\x00\x00(\xde\xde\x01\x01\x00\x00\x00\x00'
        with self.assertRaises(ValueError):
            packet.Packet.unpack_packet(packet_bytes)
        packet_bytes = b'\x02\x06\x00,\x01\x01\x01\x01\x00\x00\x00\x00\n\xbd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\xff\xff\xff\x00\x00\n\x12\x01\x00\x00\x00(\xde\xde\x01\x01\x00\x00\x00\x00'
        with self.assertRaises(ValueError):
            packet.Packet.unpack_packet(packet_bytes)
        packet_bytes = b'\x01\x01\x00,\x01\x01\x01\x01\x00\x00\x00\x00\n\xbd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        with self.assertRaises(ValueError):
            packet.Packet.unpack_packet(packet_bytes)
        with self.assertRaises(ValueError):
            packet.Packet.unpack_packet(b'')

    #  Successful run - Instant
    def test_create_hello_v2_packet_body_successful(self):
        network_mask = '255.255.255.0'
        hello_interval = 10
        options = 2
        router_priority = 1
        router_dead_interval = 40
        designated_router = '222.222.1.1'
        backup_designated_router = '0.0.0.0'
        neighbors = ()
        self.packet_v2.create_hello_v2_packet_body(
            network_mask, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v2.header)
        self.assertIsNotNone(self.packet_v2.body)
        self.assertEqual(44, self.packet_v2.header.length)
        self.assertEqual(5817, self.packet_v2.header.checksum)
        self.assertEqual(network_mask, self.packet_v2.body.network_mask)

        #  Ensure checksum and length are updated when body parameters are updated

        neighbors = ('1.1.1.1',)
        self.packet_v2.create_hello_v2_packet_body(
            network_mask, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v2.header)
        self.assertIsNotNone(self.packet_v2.body)
        self.assertEqual(48, self.packet_v2.header.length)
        self.assertEqual(5299, self.packet_v2.header.checksum)
        self.assertEqual(network_mask, self.packet_v2.body.network_mask)

        neighbors = ('1.1.1.1', '2.2.2.2')
        self.packet_v2.create_hello_v2_packet_body(
            network_mask, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v2.header)
        self.assertIsNotNone(self.packet_v2.body)
        self.assertEqual(52, self.packet_v2.header.length)
        self.assertEqual(4267, self.packet_v2.header.checksum)
        self.assertEqual(network_mask, self.packet_v2.body.network_mask)

    #  Successful run - Instant
    def test_create_hello_v2_packet_body_invalid_parameters(self):
        with self.assertRaises(ValueError):
            self.packet_v2.create_hello_v2_packet_body('', 0, '', 0, 0, '', '', ('',))
        with self.assertRaises(ValueError):
            self.packet_v2.create_hello_v3_packet_body(1, 10, 2, 1, 40, '222.222.1.1', '222.222.1.2', ())
        self.assertEqual(0, self.packet_v2.header.length)
        self.assertEqual(0, self.packet_v2.header.checksum)
        self.assertEqual(self.area_id, self.packet_v2.header.area_id)
        self.assertIsNone(self.packet_v2.body)

        self.packet_v2.header = None
        with self.assertRaises(ValueError):
            self.packet_v2.create_hello_v2_packet_body('255.255.255.0', 10, 2, 1, 40, '222.222.1.1', '222.222.1.2', ())
        self.assertIsNone(self.packet_v2.header)
        self.assertIsNone(self.packet_v2.body)

    #  Successful run - Instant
    def test_create_hello_v3_packet_body_successful(self):
        interface_id = 1
        hello_interval = 10
        options = 2
        router_priority = 1
        router_dead_interval = 40
        designated_router = '222.222.1.1'
        backup_designated_router = '0.0.0.0'
        neighbors = ()
        self.packet_v3.create_hello_v3_packet_body(
            interface_id, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v3.header)
        self.assertIsNotNone(self.packet_v3.body)
        self.assertEqual(36, self.packet_v3.header.length)
        self.assertEqual(4800, self.packet_v3.header.checksum)
        self.assertEqual(interface_id, self.packet_v3.body.interface_id)

        #  Ensure checksum and length are updated when body parameters are updated

        neighbors = ('1.1.1.1',)
        self.packet_v3.create_hello_v3_packet_body(
            interface_id, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v3.header)
        self.assertIsNotNone(self.packet_v3.body)
        self.assertEqual(40, self.packet_v3.header.length)
        self.assertEqual(4282, self.packet_v3.header.checksum)
        self.assertEqual(interface_id, self.packet_v3.body.interface_id)

        neighbors = ('1.1.1.1', '2.2.2.2')
        self.packet_v3.create_hello_v3_packet_body(
            interface_id, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v3.header)
        self.assertIsNotNone(self.packet_v3.body)
        self.assertEqual(44, self.packet_v3.header.length)
        self.assertEqual(3250, self.packet_v3.header.checksum)
        self.assertEqual(interface_id, self.packet_v3.body.interface_id)

    #  Successful run - Instant
    def test_create_hello_v3_packet_body_invalid_parameters(self):
        with self.assertRaises(ValueError):
            self.packet_v3.create_hello_v3_packet_body(0, 0, '', 0, 0, '', '', ('',))
        with self.assertRaises(ValueError):
            self.packet_v3.create_hello_v2_packet_body('255.255.255.0', 10, 2, 1, 40, '222.222.1.1', '222.222.1.2', ())
        self.assertEqual(0, self.packet_v3.header.length)
        self.assertEqual(0, self.packet_v3.header.checksum)
        self.assertEqual(self.area_id, self.packet_v3.header.area_id)
        self.assertIsNone(self.packet_v3.body)

        self.packet_v3.header = None
        with self.assertRaises(ValueError):
            self.packet_v3.create_hello_v3_packet_body(0, 10, 2, 1, 40, '222.222.1.1', '222.222.1.2', ())
        self.assertIsNone(self.packet_v3.header)
        self.assertIsNone(self.packet_v3.body)

    #  Successful run - Instant
    def test_set_packet_checksum_no_packet_body(self):
        self.packet_v2.set_packet_checksum()
        self.assertEqual(0, self.packet_v2.header.length)
        self.assertEqual(0, self.packet_v2.header.checksum)
        self.assertEqual(self.area_id, self.packet_v2.header.area_id)
        self.assertIsNone(self.packet_v2.body)

    #  Successful run - Instant
    def test_set_packet_length_no_packet_body(self):
        self.packet_v2.set_packet_length()
        self.assertEqual(0, self.packet_v2.header.length)
        self.assertEqual(0, self.packet_v2.header.checksum)
        self.assertEqual(self.area_id, self.packet_v2.header.area_id)
        self.assertIsNone(self.packet_v2.body)

    def tearDown(self):
        self.packet_type = 0
        self.router_id = ''
        self.area_id = ''
        self.auth_type = 0
        self.authentication = 0
        self.packet_v2 = None
