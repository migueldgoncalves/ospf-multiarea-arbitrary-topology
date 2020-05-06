import unittest
import time

import neighbor.neighbor as neighbor
import conf.conf as conf

'''
This class tests the neighbor operations in the router
'''

#  TODO: Implement validation and testing of None parameters


#  Full successful run - 90 s
class TestNeighbor(unittest.TestCase):

    def setUp(self):
        self.start_time = int(time.perf_counter())
        time.sleep(1)  # Difference between current time of test and current time of neighbor timer will be 1 s

        self.neighbor_id = '1.1.1.1'
        self.neighbor_priority = 1
        self.neighbor_interface_id = 2
        self.neighbor_ipv4_address = '222.222.1.1'
        self.neighbor_ipv6_address = '1::1'
        self.neighbor_options = 3
        self.neighbor_dr = '1.1.1.1'
        self.neighbor_bdr = '2.2.2.2'
        self.neighbor_v2 = neighbor.Neighbor(self.neighbor_id, self.neighbor_priority, 0, self.neighbor_ipv4_address,
                                             self.neighbor_options, self.neighbor_dr, self.neighbor_bdr)
        self.neighbor_v3 = neighbor.Neighbor(self.neighbor_id, self.neighbor_priority, self.neighbor_interface_id,
                                             self.neighbor_ipv6_address, self.neighbor_options, self.neighbor_dr,
                                             self.neighbor_bdr)

    #  Successful run - 1 s
    def test_constructor_successful(self):
        self.assertEqual(self.neighbor_id, self.neighbor_v2.neighbor_id)
        self.assertEqual(self.neighbor_priority, self.neighbor_v2.neighbor_priority)
        self.assertEqual(self.neighbor_ipv4_address, self.neighbor_v2.neighbor_ip_address)
        self.assertEqual(self.neighbor_options, self.neighbor_v2.neighbor_options)
        self.assertEqual(conf.NEIGHBOR_STATE_DOWN, self.neighbor_v2.neighbor_state)
        self.assertEqual(self.neighbor_dr, self.neighbor_v2.neighbor_dr)
        self.assertEqual(self.neighbor_bdr, self.neighbor_v2.neighbor_bdr)

        self.assertEqual(self.neighbor_id, self.neighbor_v3.neighbor_id)
        self.assertEqual(self.neighbor_priority, self.neighbor_v3.neighbor_priority)
        self.assertEqual(self.neighbor_interface_id, self.neighbor_v3.neighbor_interface_id)
        self.assertEqual(self.neighbor_ipv6_address, self.neighbor_v3.neighbor_ip_address)
        self.assertEqual(self.neighbor_options, self.neighbor_v3.neighbor_options)
        self.assertEqual(conf.NEIGHBOR_STATE_DOWN, self.neighbor_v3.neighbor_state)
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
            neighbor.Neighbor('', self.neighbor_priority, self.neighbor_interface_id, self.neighbor_ipv4_address,
                              self.neighbor_options, self.neighbor_dr, self.neighbor_bdr)
        with self.assertRaises(ValueError):
            neighbor.Neighbor(self.neighbor_id, self.neighbor_priority, self.neighbor_interface_id,
                              self.neighbor_ipv6_address, -1, self.neighbor_dr, self.neighbor_bdr)

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
    def test_parameter_validation_successful(self):
        #  Correct neighbor ID
        self.assertEqual((True, ''), self.neighbor_v2.parameter_validation('0.0.0.0', self.neighbor_options))
        self.assertEqual((True, ''), self.neighbor_v2.parameter_validation('255.255.255.255', self.neighbor_options))

        #  Correct neighbor options
        self.assertEqual((True, ''), self.neighbor_v2.parameter_validation(self.neighbor_id, 0))
        self.assertEqual((True, ''), self.neighbor_v2.parameter_validation(self.neighbor_id, conf.MAX_VALUE_8_BITS))

    #  Successful run - 1 s
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid neighbor ID
        self.assertEqual(
            (False, "Invalid neighbor ID"), self.neighbor_v2.parameter_validation('', self.neighbor_options))

        #  Invalid neighbor options
        self.assertEqual(
            (False, "Invalid neighbor options"), self.neighbor_v2.parameter_validation(self.neighbor_id, -1))
        self.assertEqual((False, "Invalid neighbor options"),
                         self.neighbor_v2.parameter_validation(self.neighbor_id, conf.MAX_VALUE_8_BITS + 1))
        self.assertEqual((False, "Invalid parameter type"),
                         self.neighbor_v2.parameter_validation(self.neighbor_id, 'Invalid parameter'))

    def tearDown(self):
        self.neighbor_v2.delete_neighbor()
        self.neighbor_v3.delete_neighbor()
