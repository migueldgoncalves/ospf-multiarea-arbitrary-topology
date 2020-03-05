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
        self.network_mask = self.utils.get_ipv4_network_mask_from_interface_name(self.interface_name)
        self.hello_interval = conf.HELLO_INTERVAL
        self.options = conf.OPTIONS
        self.router_priority = conf.ROUTER_PRIORITY
        self.router_dead_interval = conf.ROUTER_DEAD_INTERVAL
        self.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.neighbors = ('1.1.1.1', '2.2.2.2')
        self.interface_id = 1

        self.packet_body_v2 = hello.Hello(
            self.network_mask, self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4)
        self.packet_body_v3 = hello.Hello(
            '0.0.0.0', self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors, self.interface_id, conf.VERSION_IPV6)

    #  Successful run - Instant
    def test_hello_constructor_v2_successful(self):
        expected_network_mask = self.utils.get_ipv4_network_mask_from_interface_name(self.interface_name)
        self.assertEqual(expected_network_mask, self.packet_body_v2.network_mask)
        self.assertEqual(conf.HELLO_INTERVAL, self.packet_body_v2.hello_interval)
        self.assertEqual(conf.OPTIONS, self.packet_body_v2.options)
        self.assertEqual(conf.ROUTER_PRIORITY, self.packet_body_v2.router_priority)
        self.assertEqual(conf.ROUTER_DEAD_INTERVAL, self.packet_body_v2.router_dead_interval)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.packet_body_v2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.packet_body_v2.backup_designated_router)
        self.assertEqual(self.neighbors, self.packet_body_v2.neighbors)
        self.assertEqual(conf.VERSION_IPV4, self.packet_body_v2.version)

    #  Successful run - Instant
    def test_hello_constructor_v3_successful(self):
        self.assertEqual(conf.HELLO_INTERVAL, self.packet_body_v3.hello_interval)
        self.assertEqual(conf.OPTIONS, self.packet_body_v3.options)
        self.assertEqual(conf.ROUTER_PRIORITY, self.packet_body_v3.router_priority)
        self.assertEqual(conf.ROUTER_DEAD_INTERVAL, self.packet_body_v3.router_dead_interval)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.packet_body_v3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.packet_body_v3.backup_designated_router)
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

    #  Successful run - Instant
    def test_pack_packet(self):
        packet_body = b'\xff\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01' \
                      b'\x02\x02\x02\x02'
        self.assertEqual(packet_body, self.packet_body_v2.pack_packet())

    #  Successful run - Instant
    def test_get_format_string(self):
        format_string = hello.OSPFV2_BASE_FORMAT_STRING[2:]
        neighbors = ()
        packet_body = hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                                  self.router_dead_interval, self.designated_router, self.backup_designated_router,
                                  neighbors, 0, conf.VERSION_IPV4)
        self.assertEqual(format_string, packet_body.get_format_string(len(neighbors), conf.VERSION_IPV4))

        format_string = hello.OSPFV2_BASE_FORMAT_STRING[2:] + hello.EXTRA_FORMAT_STRING
        neighbors = ('1.1.1.1',)
        packet_body = hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                                  self.router_dead_interval, self.designated_router, self.backup_designated_router,
                                  neighbors, 0, conf.VERSION_IPV4)
        self.assertEqual(format_string, packet_body.get_format_string(len(neighbors), conf.VERSION_IPV4))

        format_string = hello.OSPFV2_BASE_FORMAT_STRING[2:] + hello.EXTRA_FORMAT_STRING + hello.EXTRA_FORMAT_STRING
        neighbors = ('1.1.1.1', '2.2.2.2')
        packet_body = hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                                  self.router_dead_interval, self.designated_router, self.backup_designated_router,
                                  neighbors, 0, conf.VERSION_IPV4)
        self.assertEqual(format_string, packet_body.get_format_string(len(neighbors), conf.VERSION_IPV4))

        format_string = hello.OSPFV2_BASE_FORMAT_STRING[2:] + hello.EXTRA_FORMAT_STRING + hello.EXTRA_FORMAT_STRING + \
            hello.EXTRA_FORMAT_STRING
        neighbors = ('1.1.1.1', '2.2.2.2', '4.4.4.4')
        packet_body = hello.Hello(self.network_mask, self.hello_interval, self.options, self.router_priority,
                                  self.router_dead_interval, self.designated_router, self.backup_designated_router,
                                  neighbors, 0, conf.VERSION_IPV4)
        self.assertEqual(format_string, packet_body.get_format_string(len(neighbors), conf.VERSION_IPV4))

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
        self.assertTrue(self.packet_body_v2.parameter_validation(
            self.network_mask, self.hello_interval, conf.MAX_VALUE_8_BITS, self.router_priority,
            self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors, 0,
            conf.VERSION_IPV4))

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
            self.network_mask, self.hello_interval, self.options, self.router_priority, conf.MAX_VALUE_32_BITS,
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
            self.network_mask, self.hello_interval, conf.MAX_VALUE_8_BITS + 1, self.router_priority,
            self.router_dead_interval, self.designated_router, self.backup_designated_router, self.neighbors, 0,
            conf.VERSION_IPV4), (False, "Invalid packet options"))
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
            self.network_mask, self.hello_interval, self.options, self.router_priority, conf.MAX_VALUE_32_BITS + 1,
            self.designated_router, self.backup_designated_router, self.neighbors, 0, conf.VERSION_IPV4),
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
            self.designated_router, self.backup_designated_router, self.neighbors, -1, conf.VERSION_IPV4),
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
