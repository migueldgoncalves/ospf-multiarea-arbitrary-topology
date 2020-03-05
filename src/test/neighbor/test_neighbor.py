import unittest
import time

import neighbor.neighbor as neighbor
import conf.conf as conf

'''
This class tests the neighbor operations in the router
'''

#  TODO: Implement validation and testing of None parameters

NEIGHBOR_IPV6_ADDRESS = '1::1'


#  Full successful run - 90 s
class TestNeighbor(unittest.TestCase):
    neighbor_id = '0.0.0.0'
    neighbor_interface_id = 0
    neighbor_ipv6_address = '::'
    neighbor_options = 0
    neighbor = None
    neighbor_dr = '0.0.0.0'
    neighbor_bdr = '0.0.0.0'

    start_time = 0

    def setUp(self):
        self.start_time = int(time.perf_counter())
        time.sleep(1)  # Difference between current time of test and current time of neighbor timer will be 1 s

        self.neighbor_id = '1.1.1.1'
        self.neighbor_interface_id = 1
        self.neighbor_ipv6_address = NEIGHBOR_IPV6_ADDRESS
        self.neighbor_options = conf.OPTIONS
        self.neighbor = neighbor.Neighbor(self.neighbor_id, self.neighbor_interface_id, self.neighbor_ipv6_address,
                                          self.neighbor_options, self.neighbor_dr, self.neighbor_bdr)

    #  Successful run - 1 s
    def test_constructor_successful(self):
        self.assertEqual(self.neighbor_id, self.neighbor.neighbor_id)
        self.assertEqual(self.neighbor_options, self.neighbor.neighbor_options)

        self.assertIsNotNone(self.neighbor.inactivity_timer)
        self.assertTrue(self.neighbor.inactivity_timer.initial_time > self.start_time)

        self.assertTrue(self.neighbor.thread.isAlive())

        self.assertFalse(self.neighbor.reset.is_set())
        self.assertFalse(self.neighbor.timeout.is_set())
        self.assertFalse(self.neighbor.shutdown.is_set())

    #  Successful run - 1 s
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            neighbor.Neighbor('', self.neighbor_interface_id, self.neighbor_ipv6_address, self.neighbor_options,
                              self.neighbor_dr, self.neighbor_bdr)
        with self.assertRaises(ValueError):
            neighbor.Neighbor(self.neighbor_id, self.neighbor_interface_id, self.neighbor_ipv6_address, -1,
                              self.neighbor_dr, self.neighbor_bdr)

    #  Successful run - 42 s
    def test_is_expired(self):
        self.assertFalse(self.neighbor.is_expired())
        time.sleep(conf.ROUTER_DEAD_INTERVAL + 1)
        self.assertTrue(self.neighbor.is_expired())

        self.assertFalse(self.neighbor.reset.is_set())
        self.assertTrue(self.neighbor.timeout.is_set())
        self.assertFalse(self.neighbor.shutdown.is_set())

    #  Successful run - 40-42 s
    def test_reset_timer(self):
        self.assertFalse(self.neighbor.is_expired())
        time.sleep(conf.ROUTER_DEAD_INTERVAL / 2)
        self.neighbor.reset_timer()
        time.sleep(conf.ROUTER_DEAD_INTERVAL / 2)
        self.assertFalse(self.neighbor.is_expired())

        self.assertFalse(self.neighbor.reset.is_set())
        self.assertFalse(self.neighbor.timeout.is_set())
        self.assertFalse(self.neighbor.shutdown.is_set())

    #  Successful run - 2 s
    def test_delete_neighbor(self):
        self.assertFalse(self.neighbor.shutdown.is_set())
        self.neighbor.delete_neighbor()
        time.sleep(1)
        self.assertFalse(self.neighbor.reset.is_set())
        self.assertTrue(self.neighbor.timeout.is_set())
        self.assertTrue(self.neighbor.shutdown.is_set())

    #  Successful run - 1 s
    def test_parameter_validation_successful(self):
        #  Correct neighbor ID
        self.assertTrue(self.neighbor.parameter_validation('0.0.0.0', self.neighbor_options))
        self.assertTrue(self.neighbor.parameter_validation('255.255.255.255', self.neighbor_options))

        #  Correct neighbor options
        self.assertTrue(self.neighbor.parameter_validation(self.neighbor_id, 0))
        self.assertTrue(self.neighbor.parameter_validation(self.neighbor_id, conf.MAX_VALUE_8_BITS))

    #  Successful run - 1 s
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid neighbor ID
        self.assertEqual(self.neighbor.parameter_validation('', self.neighbor_options), (False, "Invalid neighbor ID"))

        #  Invalid neighbor options
        self.assertEqual(self.neighbor.parameter_validation(self.neighbor_id, -1), (False, "Invalid neighbor options"))
        self.assertEqual(self.neighbor.parameter_validation(self.neighbor_id, conf.MAX_VALUE_8_BITS + 1),
                         (False, "Invalid neighbor options"))
        self.assertEqual(self.neighbor.parameter_validation(self.neighbor_id, 'Invalid parameter'),
                         (False, "Invalid parameter type"))

    def tearDown(self):
        self.neighbor_id = 0
        self.neighbor_options = 0
        self.neighbor.delete_neighbor()
        self.neighbor = None
