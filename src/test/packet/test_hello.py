import unittest

import packet.hello as hello
import conf.conf as conf
import general.utils as utils

'''
This class tests the OSPF Hello packet class and its operations
'''


#  Full successful run - Instant
class TestHello(unittest.TestCase):
    utils = utils.Utils()
    interface_name = conf.INTERFACE_NAMES[0]

    network_mask = '0.0.0.0'
    hello_interval = 0
    options = 0
    router_priority = 0
    router_dead_interval = 0
    designated_router = '0.0.0.0'
    backup_designated_router = '0.0.0.0'
    neighbors = ()
    interface_id = 0
    packet_body_v2 = None
    packet_body_v3 = None

    def setUp(self):
        self.network_mask = '255.255.255.0'
        self.hello_interval = 10
        self.options = 2
        self.router_priority = 3
        self.router_dead_interval = 40
        self.designated_router = '3.3.3.3'
        self.backup_designated_router = '4.4.4.4'
        self.neighbors = ('1.1.1.1', '2.2.2.2')
        self.interface_id = 1

        self.packet_body_v2 = hello.Hello(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4)
        self.packet_body_v3 = hello.Hello(
            '', self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, self.interface_id, conf.VERSION_IPV6)

    #  Successful run - Instant
    def test_hello_constructor_v2_successful(self):
        self.assertEqual(self.network_mask, self.packet_body_v2.network_mask)
        self.assertEqual(self.hello_interval, self.packet_body_v2.hello_interval)
        self.assertEqual(self.options, self.packet_body_v2.options)
        self.assertEqual(self.router_priority, self.packet_body_v2.router_priority)
        self.assertEqual(self.router_dead_interval, self.packet_body_v2.router_dead_interval)
        self.assertEqual(self.designated_router, self.packet_body_v2.designated_router)
        self.assertEqual(self.backup_designated_router, self.packet_body_v2.backup_designated_router)
        self.assertEqual(self.neighbors, self.packet_body_v2.neighbors)
        self.assertEqual(conf.VERSION_IPV4, self.packet_body_v2.version)

    #  Successful run - Instant
    def test_hello_constructor_v3_successful(self):
        self.assertEqual(self.hello_interval, self.packet_body_v3.hello_interval)
        self.assertEqual(self.options, self.packet_body_v3.options)
        self.assertEqual(self.router_priority, self.packet_body_v3.router_priority)
        self.assertEqual(self.router_dead_interval, self.packet_body_v3.router_dead_interval)
        self.assertEqual(self.designated_router, self.packet_body_v3.designated_router)
        self.assertEqual(self.backup_designated_router, self.packet_body_v3.backup_designated_router)
        self.assertEqual(self.neighbors, self.packet_body_v3.neighbors)
        self.assertEqual(self.interface_id, self.packet_body_v3.interface_id)
        self.assertEqual(conf.VERSION_IPV6, self.packet_body_v3.version)

    #  Successful run - Instant
    def test_hello_constructor_invalid_parameters(self):
        invalid_network_mask = ''
        with self.assertRaises(ValueError):
            hello.Hello(invalid_network_mask, self.hello_interval, self.options, self.router_priority,
                        self.router_dead_interval, self.designated_router, self.backup_designated_router,
                        self.neighbors, 0, conf.VERSION_IPV4)
        invalid_hello_interval = -1
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, invalid_hello_interval, self.options, self.router_priority,
                        self.router_dead_interval, self.designated_router, self.backup_designated_router,
                        self.neighbors, 0, conf.VERSION_IPV4)
        invalid_options = -1
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, self.hello_interval, invalid_options, self.router_priority,
                        self.router_dead_interval, self.designated_router, self.backup_designated_router,
                        self.neighbors, 0, conf.VERSION_IPV4)
        invalid_router_priority = -1
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, self.hello_interval, self.options, invalid_router_priority,
                        self.router_dead_interval, self.designated_router, self.backup_designated_router,
                        self.neighbors, 0, conf.VERSION_IPV4)
        invalid_router_dead_interval = -1
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                        invalid_router_dead_interval, self.designated_router, self.backup_designated_router,
                        self.neighbors, 0, conf.VERSION_IPV4)
        invalid_designated_router = ''
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                        self.router_dead_interval, invalid_designated_router, self.backup_designated_router,
                        self.neighbors, 0, conf.VERSION_IPV4)
        invalid_backup_designated_router = ''
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                        self.router_dead_interval, self.designated_router, invalid_backup_designated_router,
                        self.neighbors, 0, conf.VERSION_IPV4)
        invalid_neighbors = ('', '')
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, invalid_hello_interval, self.options, self.router_priority,
                        self.router_dead_interval, self.designated_router, self.backup_designated_router,
                        invalid_neighbors, 0, conf.VERSION_IPV4)
        invalid_interface_id = -1
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                        self.router_dead_interval, self.designated_router, self.backup_designated_router,
                        invalid_neighbors, invalid_interface_id, conf.VERSION_IPV6)
        invalid_ospf_version = 1
        with self.assertRaises(ValueError):
            hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                        self.router_dead_interval, self.designated_router, self.backup_designated_router,
                        invalid_neighbors, 0, invalid_ospf_version)

    #  Successful run - Instant
    def test_pack_packet(self):
        packet_body_bytes = b'\xff\xff\xff\x00\x00\n\x02\x03\x00\x00\x00(\x03\x03\x03\x03\x04\x04\x04\x04\x01\x01\x01' \
                            b'\x01\x02\x02\x02\x02'
        self.assertEqual(packet_body_bytes, self.packet_body_v2.pack_packet_body())
        packet_body_bytes = b'\x00\x00\x00\x01\x03\x00\x00\x02\x00\n\x00(\x03\x03\x03\x03\x04\x04\x04\x04\x01\x01\x01' \
                            b'\x01\x02\x02\x02\x02'
        self.assertEqual(packet_body_bytes, self.packet_body_v3.pack_packet_body())

    #  Successful run - Instant
    def test_unpack_packet(self):
        packet_body_bytes = b'\xff\xff\xff\x00\x00\n\x02\x03\x00\x00\x00(\x03\x03\x03\x03\x04\x04\x04\x04\x01\x01\x01' \
                            b'\x01\x02\x02\x02\x02'
        unpacked_body = hello.Hello.unpack_packet_body(packet_body_bytes, conf.VERSION_IPV4)
        self.assertEqual(self.network_mask, unpacked_body.network_mask)
        self.assertEqual(self.hello_interval, unpacked_body.hello_interval)
        self.assertEqual(self.options, unpacked_body.options)
        self.assertEqual(self.router_priority, unpacked_body.router_priority)
        self.assertEqual(self.router_dead_interval, unpacked_body.router_dead_interval)
        self.assertEqual(self.designated_router, unpacked_body.designated_router)
        self.assertEqual(self.backup_designated_router, unpacked_body.backup_designated_router)
        self.assertEqual(self.neighbors, unpacked_body.neighbors)

        packet_body_bytes = b'\x00\x00\x00\x01\x03\x00\x00\x02\x00\n\x00(\x03\x03\x03\x03\x04\x04\x04\x04\x01\x01\x01' \
                            b'\x01\x02\x02\x02\x02'
        unpacked_body = hello.Hello.unpack_packet_body(packet_body_bytes, conf.VERSION_IPV6)
        self.assertEqual(self.interface_id, unpacked_body.interface_id)
        self.assertEqual(self.router_priority, unpacked_body.router_priority)
        self.assertEqual(self.options, unpacked_body.options)
        self.assertEqual(self.hello_interval, unpacked_body.hello_interval)
        self.assertEqual(self.router_dead_interval, unpacked_body.router_dead_interval)
        self.assertEqual(self.designated_router, unpacked_body.designated_router)
        self.assertEqual(self.backup_designated_router, unpacked_body.backup_designated_router)
        self.assertEqual(self.neighbors, unpacked_body.neighbors)

    #  Successful run - Instant
    def test_get_format_string(self):
        neighbors = 0
        format_string_v2 = hello.OSPFV2_BASE_FORMAT_STRING
        format_string_v3 = hello.OSPFV3_BASE_FORMAT_STRING
        self.assertEqual(format_string_v2, hello.Hello.get_format_string(neighbors, conf.VERSION_IPV4))
        self.assertEqual(format_string_v3, hello.Hello.get_format_string(neighbors, conf.VERSION_IPV6))

        neighbors = 1
        format_string_v2 = hello.OSPFV2_BASE_FORMAT_STRING + hello.EXTRA_FORMAT_STRING
        format_string_v3 = hello.OSPFV3_BASE_FORMAT_STRING + hello.EXTRA_FORMAT_STRING
        self.assertEqual(format_string_v2, hello.Hello.get_format_string(neighbors, conf.VERSION_IPV4))
        self.assertEqual(format_string_v3, hello.Hello.get_format_string(neighbors, conf.VERSION_IPV6))

        neighbors = 2
        format_string_v2 = hello.OSPFV2_BASE_FORMAT_STRING + hello.EXTRA_FORMAT_STRING + hello.EXTRA_FORMAT_STRING
        format_string_v3 = hello.OSPFV3_BASE_FORMAT_STRING + hello.EXTRA_FORMAT_STRING + hello.EXTRA_FORMAT_STRING
        self.assertEqual(format_string_v2, hello.Hello.get_format_string(neighbors, conf.VERSION_IPV4))
        self.assertEqual(format_string_v3, hello.Hello.get_format_string(neighbors, conf.VERSION_IPV6))

        neighbors = 3
        format_string_v2 = hello.OSPFV2_BASE_FORMAT_STRING + hello.EXTRA_FORMAT_STRING + \
            hello.EXTRA_FORMAT_STRING + hello.EXTRA_FORMAT_STRING
        format_string_v3 = hello.OSPFV3_BASE_FORMAT_STRING + hello.EXTRA_FORMAT_STRING + \
            hello.EXTRA_FORMAT_STRING + hello.EXTRA_FORMAT_STRING
        self.assertEqual(format_string_v2, hello.Hello.get_format_string(neighbors, conf.VERSION_IPV4))
        self.assertEqual(format_string_v3, hello.Hello.get_format_string(neighbors, conf.VERSION_IPV6))

        with self.assertRaises(ValueError):
            hello.Hello.get_format_string(-1, conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            hello.Hello.get_format_string(neighbors, 1)

    #  Successful run - Instant
    def test_get_hello_packet_neighbor_number(self):
        body_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.assertEqual(0, hello.Hello.get_hello_packet_neighbor_number(body_bytes))
        body_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.assertEqual(1, hello.Hello.get_hello_packet_neighbor_number(body_bytes))
        body_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                     b'\x00\x00\x00\x00\x00'
        self.assertEqual(2, hello.Hello.get_hello_packet_neighbor_number(body_bytes))
        body_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                     b'\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.assertEqual(3, hello.Hello.get_hello_packet_neighbor_number(body_bytes))
        body_bytes = b'\x00'
        with self.assertRaises(ValueError):
            hello.Hello.get_hello_packet_neighbor_number(body_bytes)

    #  Successful run - Instant
    def test_get_hello_packet_neighbors(self):
        neighbor_tuple = ()
        self.assertEqual(0, len(hello.Hello.get_hello_packet_neighbors(neighbor_tuple)))

        neighbor_tuple = (16843009,)
        neighbor_identifiers = hello.Hello.get_hello_packet_neighbors(neighbor_tuple)
        self.assertEqual(1, len(neighbor_identifiers))
        self.assertEqual('1.1.1.1', neighbor_identifiers[0])

        neighbor_tuple = (16843009, 33686018)
        neighbor_identifiers = hello.Hello.get_hello_packet_neighbors(neighbor_tuple)
        self.assertEqual(2, len(neighbor_identifiers))
        self.assertEqual('1.1.1.1', neighbor_identifiers[0])
        self.assertEqual('2.2.2.2', neighbor_identifiers[1])

        neighbor_tuple = (16843009, 33686018, 50529027)
        neighbor_identifiers = hello.Hello.get_hello_packet_neighbors(neighbor_tuple)
        self.assertEqual(3, len(neighbor_identifiers))
        self.assertEqual('1.1.1.1', neighbor_identifiers[0])
        self.assertEqual('2.2.2.2', neighbor_identifiers[1])
        self.assertEqual('3.3.3.3', neighbor_identifiers[2])

    #  Successful run - Instant
    def test_parameter_validation_successful(self):
        #  Correct network mask
        self.assertTrue(self.packet_body_v2.parameter_validation(
            '0.0.0.0', self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            '255.255.255.255', self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))

        #  Correct Hello interval
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, 0, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, conf.MAX_VALUE_16_BITS, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))

        #  Correct packet options
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, 0, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v3.parameter_validation(
            self.network_mask, self.hello_interval, 0, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV6))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, conf.MAX_VALUE_8_BITS, self.router_priority,
            self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors, 0,
            conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, conf.MAX_VALUE_24_BITS, self.router_priority,
            self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors, 0,
            conf.VERSION_IPV6))

        #  Correct router priority
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, 0, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, conf.MAX_VALUE_8_BITS, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))

        #  Correct router dead interval
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, 0,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, 0,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV6))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, conf.MAX_VALUE_32_BITS,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, conf.MAX_VALUE_16_BITS,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))

        #  Correct Designated Router
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            '0.0.0.0', self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            '255.255.255.255', self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))

        #  Correct Backup Designated Router
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, '0.0.0.0', self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, '255.255.255.255', self.neighbors, 0, conf.VERSION_IPV4))

        #  Correct neighbors
        neighbors = ()
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, neighbors, 0, conf.VERSION_IPV4))
        neighbors = ('1.1.1.1',)
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, neighbors, 0, conf.VERSION_IPV4))
        neighbors = ('1.1.1.1', '2.2.2.2')
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, neighbors, 0, conf.VERSION_IPV4))
        neighbors = ('1.1.1.1', '2.2.2.2', '4.4.4.4')
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, neighbors, 0, conf.VERSION_IPV4))

        #  Correct interface ID
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV6))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, conf.MAX_VALUE_32_BITS,
            conf.VERSION_IPV6))

        #  Correct OSPF version
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4))
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV6))

    #  Successful run - Instant
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid network mask
        self.assertEqual(self.packet_body_v2.parameter_validation(
            '', self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid network mask"))

        #  Invalid Hello interval
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, -1, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid Hello interval"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, conf.MAX_VALUE_16_BITS + 1, self.options, self.router_priority,
            self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid Hello interval"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, 'Invalid parameter', self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid parameter type"))

        #  Invalid packet options
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, -1, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid packet options"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, -1, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV6),
            (False, "Invalid packet options"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, conf.MAX_VALUE_8_BITS + 1, self.router_priority,
            self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors, 0,
            conf.VERSION_IPV4), (False, "Invalid packet options"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, conf.MAX_VALUE_24_BITS + 1, self.router_priority,
            self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors, 0,
            conf.VERSION_IPV6), (False, "Invalid packet options"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, 'Invalid parameter', self.router_priority,
            self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors, 0,
            conf.VERSION_IPV4), (False, "Invalid parameter type"))

        #  Invalid router priority
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, -1, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid router priority"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, conf.MAX_VALUE_8_BITS + 1, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid router priority"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, 'Invalid parameter', self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid parameter type"))

        #  Invalid router dead interval
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, -1,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid router dead interval"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, -1,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV6),
            (False, "Invalid router dead interval"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, conf.MAX_VALUE_32_BITS + 1,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid router dead interval"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, conf.MAX_VALUE_16_BITS + 1,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV6),
            (False, "Invalid router dead interval"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, 'Invalid parameter',
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid parameter type"))

        #  Invalid Designated Router
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval, '',
            self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid Designated Router"))

        #  Invalid Backup Designated Router
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, '', self.neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid Backup Designated Router"))

        #  Invalid neighbors
        neighbors = ('',)
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid Neighbor(s)"))
        neighbors = ('', '')
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid Neighbor(s)"))
        neighbors = ('', '', '')
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, neighbors, 0, conf.VERSION_IPV4),
            (False, "Invalid Neighbor(s)"))

        #  Invalid interface ID
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, -1, conf.VERSION_IPV6),
            (False, "Invalid interface ID"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, conf.MAX_VALUE_32_BITS + 1,
            conf.VERSION_IPV6),
            (False, "Invalid interface ID"))

        #  Invalid OSPF version
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, 1),
            (False, "Invalid OSPF version"))
        self.assertEqual(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, 4),
            (False, "Invalid OSPF version"))

    def tearDown(self):
        self.network_mask = ''
        self.hello_interval = 0
        self.options = 0
        self.router_priority = 0
        self.router_dead_interval = 0
        self.designated_router = ''
        self.backup_designated_router = ''
        self.neighbors = ()
        self.interface_id = 0
        self.packet_body_v2 = None
        self.packet_body_v3 = None
