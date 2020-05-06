import unittest

import packet.packet as packet
import conf.conf as conf

'''
This class tests the interface to packet creation, storage and manipulation
'''


#  Full successful run - Instant
class PacketTest(unittest.TestCase):

    def setUp(self):
        self.packet_type = conf.PACKET_TYPE_HELLO
        self.router_id = '1.1.1.1'
        self.area_id = '2.2.2.2'
        self.auth_type = 1
        self.authentication = 2
        self.instance_id = 3
        self.source_ipv6_address = 'fe80::c001:18ff:fe34:10'
        self.destination_ipv6_address = 'ff02::5'
        self.packet_v2 = packet.Packet()
        self.packet_v2.create_header_v2(
            self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication)
        self.packet_v3 = packet.Packet()
        self.packet_v3.create_header_v3(self.packet_type, self.router_id, self.area_id, self.instance_id,
                                        self.source_ipv6_address, self.destination_ipv6_address)

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
        self.assertEqual(self.source_ipv6_address, self.packet_v3.source_ipv6_address)
        self.assertEqual(self.destination_ipv6_address, self.packet_v3.destination_ipv6_address)

        self.packet_v2.create_header_v2(
            self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication)
        self.packet_v3.create_header_v3(self.packet_type, self.router_id, self.area_id, self.instance_id,
                                        self.source_ipv6_address, self.destination_ipv6_address)
        self.assertIsNone(self.packet_v2.body)
        self.assertIsNone(self.packet_v3.body)

    #  Successful run - Instant
    def test_create_header_invalid_parameters(self):
        with self.assertRaises(ValueError):
            self.packet_v2.create_header_v2(0, self.router_id, self.area_id, self.auth_type, self.authentication)
        with self.assertRaises(ValueError):
            self.packet_v3.create_header_v3(0, self.router_id, self.area_id, self.instance_id, self.source_ipv6_address,
                                            self.destination_ipv6_address)

    # Successful run - Instant
    def test_pack_packet_successful(self):
        packet_v2_bytes = b'\x02\x01\x000\x01\x01\x01\x01\x02\x02\x02\x02\x14\xb3\x00\x01\x00\x00\x00\x00\x00\x00\x00' \
                          b'\x02\xff\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\xde\xde\x01\x01\x00\x00\x00\x00\x01\x01' \
                          b'\x01\x01'
        packet_v3_bytes = b'\x03\x01\x00(\x01\x01\x01\x01\x02\x02\x02\x02;j\x03\x00\x00\x00\x00\x01\x01\x00\x00\x02' \
                          b'\x00\n\x00(\xde\xde\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01'
        self.packet_v2.create_hello_v2_packet_body(
            '255.255.255.0', 10, 2, 1, 40, '222.222.1.1', '0.0.0.0', ('1.1.1.1',))
        self.packet_v3.create_hello_v3_packet_body(1, 10, 2, 1, 40, '222.222.1.1', '0.0.0.0', ('1.1.1.1',))
        self.assertEqual(packet_v2_bytes, self.packet_v2.pack_packet())
        self.assertEqual(packet_v3_bytes, self.packet_v3.pack_packet())

        packet_v2_bytes = b'\x02\x01\x00,\x01\x01\x01\x01\x00\x00\x00\x00\n\xbd\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                          b'\x00\xff\xff\xff\x00\x00\n\x12\x01\x00\x00\x00(\xde\xde\x01\x01\x00\x00\x00\x00'
        packet_v3_bytes = b'\x03\x01\x00$\x01\x01\x01\x01\x00\x00\x00\x00"@\x00\x00\x00\x00\x00\x06\x01\x00\x00\x13' \
                          b'\x00\n\x00(\x01\x01\x01\x01\x00\x00\x00\x00'
        self.packet_v2.create_header_v2(1, '1.1.1.1', '0.0.0.0', 0, 0)
        self.packet_v3.create_header_v3(1, '1.1.1.1', '0.0.0.0', 0, 'fe80::c001:18ff:fe34:10', 'ff02::5')
        self.packet_v2.create_hello_v2_packet_body('255.255.255.0', 10, 18, 1, 40, '222.222.1.1', '0.0.0.0', ())
        self.packet_v3.create_hello_v3_packet_body(6, 10, 19, 1, 40, '1.1.1.1', '0.0.0.0', ())
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
        self.assertEqual(1, self.packet_v2.header.auth_type)
        self.assertEqual(2, self.packet_v2.header.authentication)
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
        self.assertEqual(1, self.packet_v2.header.auth_type)
        self.assertEqual(2, self.packet_v2.header.authentication)
        self.assertEqual(network_mask, self.packet_v2.body.network_mask)

        neighbors = ('1.1.1.1', '2.2.2.2')
        self.packet_v2.create_hello_v2_packet_body(
            network_mask, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v2.header)
        self.assertIsNotNone(self.packet_v2.body)
        self.assertEqual(52, self.packet_v2.header.length)
        self.assertEqual(4267, self.packet_v2.header.checksum)
        self.assertEqual(1, self.packet_v2.header.auth_type)
        self.assertEqual(2, self.packet_v2.header.authentication)
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
        self.assertEqual(15732, self.packet_v3.header.checksum)
        self.assertEqual(3, self.packet_v3.header.instance_id)
        self.assertEqual(interface_id, self.packet_v3.body.interface_id)

        #  Ensure checksum and length are updated when body parameters are updated

        neighbors = ('1.1.1.1',)
        self.packet_v3.create_hello_v3_packet_body(
            interface_id, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v3.header)
        self.assertIsNotNone(self.packet_v3.body)
        self.assertEqual(40, self.packet_v3.header.length)
        self.assertEqual(15210, self.packet_v3.header.checksum)
        self.assertEqual(3, self.packet_v3.header.instance_id)
        self.assertEqual(interface_id, self.packet_v3.body.interface_id)

        neighbors = ('1.1.1.1', '2.2.2.2')
        self.packet_v3.create_hello_v3_packet_body(
            interface_id, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)

        self.assertIsNotNone(self.packet_v3.header)
        self.assertIsNotNone(self.packet_v3.body)
        self.assertEqual(44, self.packet_v3.header.length)
        self.assertEqual(14174, self.packet_v3.header.checksum)
        self.assertEqual(3, self.packet_v3.header.instance_id)
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

        self.packet_v3.set_packet_checksum()
        self.assertEqual(0, self.packet_v3.header.length)
        self.assertEqual(0, self.packet_v3.header.checksum)
        self.assertEqual(self.area_id, self.packet_v3.header.area_id)
        self.assertIsNone(self.packet_v3.body)

    #  Successful run - Instant
    def test_set_packet_length_no_packet_body(self):
        self.packet_v2.set_packet_length()
        self.assertEqual(0, self.packet_v2.header.length)
        self.assertEqual(0, self.packet_v2.header.checksum)
        self.assertEqual(self.area_id, self.packet_v2.header.area_id)
        self.assertIsNone(self.packet_v2.body)

        self.packet_v3.set_packet_length()
        self.assertEqual(0, self.packet_v3.header.length)
        self.assertEqual(0, self.packet_v3.header.checksum)
        self.assertEqual(self.area_id, self.packet_v3.header.area_id)
        self.assertIsNone(self.packet_v3.body)
