import unittest
import time

import neighbor.neighbor as neighbor
import conf.conf as conf

'''
This class tests the neighbor operations in the router
'''

#  TODO: Implement validation and testing of None parameters


#  Full successful run - 91 s
class TestNeighbor(unittest.TestCase):
    neighbor_id = '0.0.0.0'
    neighbor_interface_id = 0
    neighbor_ipv4_address = '0.0.0.0'
    neighbor_ipv6_address = '::'
    neighbor_options = 0
    neighbor_dr = '0.0.0.0'
    neighbor_bdr = '0.0.0.0'
    neighbor_v2 = None
    neighbor_v3 = None

    start_time = 0

    def setUp(self):
        self.start_time = int(time.perf_counter())
        time.sleep(1)  # Difference between current time of test and current time of neighbor timer will be 1 s

        self.neighbor_id = '1.1.1.1'
        self.neighbor_interface_id = 1
        self.neighbor_ipv4_address = '222.222.1.1'
        self.neighbor_ipv6_address = '1::1'
        self.neighbor_options = 2
        self.neighbor_dr = '0.0.0.0'
        self.neighbor_bdr = '0.0.0.0'
        self.neighbor_v2 = neighbor.Neighbor(self.neighbor_id, 0, self.neighbor_ipv4_address, self.neighbor_options,
                                             self.neighbor_dr, self.neighbor_bdr)
        self.neighbor_v3 = neighbor.Neighbor(self.neighbor_id, self.neighbor_interface_id, self.neighbor_ipv6_address,
                                             self.neighbor_options, self.neighbor_dr, self.neighbor_bdr)

    #  Successful run - 1 s
    def test_constructor_successful(self):
        self.assertEqual(self.neighbor_id, self.neighbor_v2.neighbor_id)
        self.assertEqual(self.neighbor_ipv4_address, self.neighbor_v2.neighbor_ip_address)
        self.assertEqual(self.neighbor_options, self.neighbor_v2.neighbor_options)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.neighbor_v2.neighbor_state)
        self.assertEqual(self.neighbor_dr, self.neighbor_v2.neighbor_dr)
        self.assertEqual(self.neighbor_bdr, self.neighbor_v2.neighbor_bdr)

        self.assertEqual(self.neighbor_id, self.neighbor_v3.neighbor_id)
        self.assertEqual(self.neighbor_interface_id, self.neighbor_v3.neighbor_interface_id)
        self.assertEqual(self.neighbor_ipv6_address, self.neighbor_v3.neighbor_ip_address)
        self.assertEqual(self.neighbor_options, self.neighbor_v3.neighbor_options)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.neighbor_v3.neighbor_state)
        self.assertEqual(self.neighbor_dr, self.neighbor_v3.neighbor_dr)
        self.assertEqual(self.neighbor_bdr, self.neighbor_v3.neighbor_bdr)

        self.assertIsNotNone(self.neighbor_v2.inactivity_timer)
        self.assertIsNotNone(self.neighbor_v3.inactivity_timer)
        self.assertTrue(self.neighbor_v2.inactivity_timer.initial_time > self.start_time)
        self.assertTrue(self.neighbor_v3.inactivity_timer.initial_time > self.start_time)

        self.assertTrue(self.neighbor_v2.thread.isAlive())
        self.assertTrue(self.neighbor_v3.thread.isAlive())

        self.assertFalse(self.neighbor_v2.reset.is_set())
        self.assertFalse(self.neighbor_v3.reset.is_set())
        self.assertFalse(self.neighbor_v2.timeout.is_set())
        self.assertFalse(self.neighbor_v3.timeout.is_set())
        self.assertFalse(self.neighbor_v2.shutdown.is_set())
        self.assertFalse(self.neighbor_v3.shutdown.is_set())

    #  Successful run - 1 s
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            neighbor.Neighbor('', self.neighbor_interface_id, self.neighbor_ipv4_address, self.neighbor_options,
                              self.neighbor_dr, self.neighbor_bdr)
        with self.assertRaises(ValueError):
            neighbor.Neighbor(self.neighbor_id, self.neighbor_interface_id, self.neighbor_ipv6_address, -1,
                              self.neighbor_dr, self.neighbor_bdr)

    #  Successful run - 42 s
    def test_is_expired(self):
        self.assertFalse(self.neighbor_v2.is_expired())
        time.sleep(conf.ROUTER_DEAD_INTERVAL + 1)
        self.assertTrue(self.neighbor_v2.is_expired())

        self.assertFalse(self.neighbor_v2.reset.is_set())
        self.assertTrue(self.neighbor_v2.timeout.is_set())
        self.assertFalse(self.neighbor_v2.shutdown.is_set())

    #  Successful run - 42 s
    def test_reset_timer(self):
        self.assertFalse(self.neighbor_v2.is_expired())
        time.sleep(conf.ROUTER_DEAD_INTERVAL / 2)
        self.neighbor_v2.reset_timer()
        time.sleep((conf.ROUTER_DEAD_INTERVAL / 2) + 1)
        self.assertFalse(self.neighbor_v2.is_expired())

        self.assertFalse(self.neighbor_v2.reset.is_set())
        self.assertFalse(self.neighbor_v2.timeout.is_set())
        self.assertFalse(self.neighbor_v2.shutdown.is_set())

    #  Successful run - 2 s
    def test_delete_neighbor(self):
        self.assertFalse(self.neighbor_v2.shutdown.is_set())
        self.neighbor_v2.delete_neighbor()
        time.sleep(1)
        self.assertFalse(self.neighbor_v2.reset.is_set())
        self.assertTrue(self.neighbor_v2.timeout.is_set())
        self.assertTrue(self.neighbor_v2.shutdown.is_set())

    #  Successful run - 1 s
    def test_get_ospf_version(self):
        self.assertEqual(conf.VERSION_IPV4, self.neighbor_v2.get_ospf_version())
        self.assertEqual(conf.VERSION_IPV6, self.neighbor_v3.get_ospf_version())

        self.neighbor_v2.neighbor_ip_address = ''
        self.neighbor_v3.neighbor_ip_address = ''
        with self.assertRaises(ValueError):
            self.neighbor_v2.get_ospf_version()
        with self.assertRaises(ValueError):
            self.neighbor_v3.get_ospf_version()

    #  Successful run - 1 s
    def test_parameter_validation_successful(self):
        #  Correct neighbor ID
        self.assertTrue(self.neighbor_v2.parameter_validation('0.0.0.0', self.neighbor_options))
        self.assertTrue(self.neighbor_v2.parameter_validation('255.255.255.255', self.neighbor_options))

        #  Correct neighbor options
        self.assertTrue(self.neighbor_v2.parameter_validation(self.neighbor_id, 0))
        self.assertTrue(self.neighbor_v2.parameter_validation(self.neighbor_id, conf.MAX_VALUE_8_BITS))

    #  Successful run - 1 s
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid neighbor ID
        self.assertEqual(
            self.neighbor_v2.parameter_validation('', self.neighbor_options), (False, "Invalid neighbor ID"))

        #  Invalid neighbor options
        self.assertEqual(
            self.neighbor_v2.parameter_validation(self.neighbor_id, -1), (False, "Invalid neighbor options"))
        self.assertEqual(self.neighbor_v2.parameter_validation(self.neighbor_id, conf.MAX_VALUE_8_BITS + 1),
                         (False, "Invalid neighbor options"))
        self.assertEqual(self.neighbor_v2.parameter_validation(self.neighbor_id, 'Invalid parameter'),
                         (False, "Invalid parameter type"))

    def tearDown(self):
        self.neighbor_v2.delete_neighbor()
        self.neighbor_v3.delete_neighbor()
        self.neighbor_v2 = None
        self.neighbor_v3 = None
