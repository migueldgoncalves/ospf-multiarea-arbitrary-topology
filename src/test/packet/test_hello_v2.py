import unittest

import packet.hello_v2 as hello_v2
import conf.conf as conf
import general.utils as utils

'''
This class tests the OSPFv2 Hello packet class and its operations
'''


#  Full successful run - Instant
class TestHelloV2(unittest.TestCase):

    utils = utils.Utils()
    interface_name = conf.INTERFACE_NAMES[0]

    network_mask = ''
    hello_interval = 0
    options = 0
    router_priority = 0
    router_dead_interval = 0
    designated_router = ''
    backup_designated_router = ''
    neighbors = ()
    packet_body = None

    def setUp(self):
        self.network_mask = self.utils.get_ipv4_network_mask_from_interface_name(self.interface_name)
        self.hello_interval = conf.HELLO_INTERVAL
        self.options = conf.OPTIONS
        self.router_priority = conf.ROUTER_PRIORITY
        self.router_dead_interval = conf.ROUTER_DEAD_INTERVAL
        self.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.neighbors = ('1.1.1.1', '2.2.2.2')

        self.packet_body = hello_v2.HelloV2(self.network_mask, self.hello_interval, self.options, self.router_priority,
                                            self.router_dead_interval, self.designated_router,
                                            self.backup_designated_router, self.neighbors)

    #  Successful run - Instant
    def test_hello_constructor_successful(self):
        expected_network_mask = self.utils.get_ipv4_network_mask_from_interface_name(self.interface_name)
        self.assertEqual(expected_network_mask, self.packet_body.network_mask)
        self.assertEqual(conf.HELLO_INTERVAL, self.packet_body.hello_interval)
        self.assertEqual(conf.OPTIONS, self.packet_body.options)
        self.assertEqual(conf.ROUTER_PRIORITY, self.packet_body.router_priority)
        self.assertEqual(conf.ROUTER_DEAD_INTERVAL, self.packet_body.router_dead_interval)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.packet_body.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.packet_body.backup_designated_router)
        self.assertEqual(self.neighbors, self.packet_body.neighbors)

    #  Successful run - Instant
    def test_hello_constructor_invalid_parameters(self):
        invalid_network_mask = ''
        with self.assertRaises(ValueError):
            hello_v2.HelloV2(invalid_network_mask, self.hello_interval, self.options, self.router_priority,
                             self.router_dead_interval, self.designated_router, self.backup_designated_router,
                             self.neighbors)
        invalid_hello_interval = -1
        with self.assertRaises(ValueError):
            hello_v2.HelloV2(self.network_mask, invalid_hello_interval, self.options, self.router_priority,
                             self.router_dead_interval, self.designated_router, self.backup_designated_router,
                             self.neighbors)
        invalid_options = -1
        with self.assertRaises(ValueError):
            hello_v2.HelloV2(self.network_mask, self.hello_interval, invalid_options, self.router_priority,
                             self.router_dead_interval, self.designated_router, self.backup_designated_router,
                             self.neighbors)
        invalid_router_priority = -1
        with self.assertRaises(ValueError):
            hello_v2.HelloV2(self.network_mask, self.hello_interval, self.options, invalid_router_priority,
                             self.router_dead_interval, self.designated_router, self.backup_designated_router,
                             self.neighbors)
        invalid_router_dead_interval = -1
        with self.assertRaises(ValueError):
            hello_v2.HelloV2(self.network_mask, self.hello_interval, self.options, self.router_priority,
                             invalid_router_dead_interval, self.designated_router, self.backup_designated_router,
                             self.neighbors)
        invalid_designated_router = ''
        with self.assertRaises(ValueError):
            hello_v2.HelloV2(self.network_mask, self.hello_interval, self.options, self.router_priority,
                             self.router_dead_interval, invalid_designated_router, self.backup_designated_router,
                             self.neighbors)
        invalid_backup_designated_router = ''
        with self.assertRaises(ValueError):
            hello_v2.HelloV2(self.network_mask, self.hello_interval, self.options, self.router_priority,
                             self.router_dead_interval, self.designated_router, invalid_backup_designated_router,
                             self.neighbors)
        invalid_neighbors = ('', '')
        with self.assertRaises(ValueError):
            hello_v2.HelloV2(self.network_mask, invalid_hello_interval, self.options, self.router_priority,
                             self.router_dead_interval, self.designated_router, self.backup_designated_router,
                             invalid_neighbors)

    #  Successful run - Instant
    def test_pack_packet(self):
        packet_body = b'\xff\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01' \
                      b'\x02\x02\x02\x02'
        self.assertEqual(packet_body, self.packet_body.pack_packet())

    #  Successful run - Instant
    def test_get_format_string(self):
        format_string = hello_v2.BASE_FORMAT_STRING
        neighbors = ()
        packet_body = hello_v2.HelloV2(self.network_mask, self.hello_interval, self.options, self.router_priority,
                                       self.router_dead_interval, self.designated_router, self.backup_designated_router,
                                       neighbors)
        self.assertEqual(format_string, packet_body.get_format_string())

        format_string = hello_v2.BASE_FORMAT_STRING + hello_v2.EXTRA_FORMAT_STRING
        neighbors = ('1.1.1.1',)
        packet_body = hello_v2.HelloV2(self.network_mask, self.hello_interval, self.options, self.router_priority,
                                       self.router_dead_interval, self.designated_router, self.backup_designated_router,
                                       neighbors)
        self.assertEqual(format_string, packet_body.get_format_string())

        format_string = hello_v2.BASE_FORMAT_STRING + hello_v2.EXTRA_FORMAT_STRING + hello_v2.EXTRA_FORMAT_STRING
        neighbors = ('1.1.1.1', '2.2.2.2')
        packet_body = hello_v2.HelloV2(self.network_mask, self.hello_interval, self.options, self.router_priority,
                                       self.router_dead_interval, self.designated_router, self.backup_designated_router,
                                       neighbors)
        self.assertEqual(format_string, packet_body.get_format_string())

    #  Successful run - Instant
    def test_parameter_validation_successful(self):
        #  Correct network mask
        self.assertTrue(self.packet_body.parameter_validation(
            '0.0.0.0', self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors))
        self.assertTrue(self.packet_body.parameter_validation(
            '255.255.255.255', self.hello_interval, self.options, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors))

        #  TODO: Continue test

    #  TODO: Create test for invalid parameters in parameter validation

    def tearDown(self):
        self.network_mask = ''
        self.hello_interval = 0
        self.options = 0
        self.router_priority = 0
        self.router_dead_interval = 0
        self.designated_router = ''
        self.backup_designated_router = ''
        self.neighbors = ()
        self.packet_body = None
