import unittest
import time

import neighbor.neighbor as neighbor
import conf.conf as conf

'''
This class tests the neighbor operations in the router
'''

#  TODO: Implement validation and testing of None parameters


#  Full successful run - 105-106 s
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
                                             self.neighbor_options, self.neighbor_dr, self.neighbor_bdr, conf.ROUTER_ID)
        self.neighbor_v3 = neighbor.Neighbor(self.neighbor_id, self.neighbor_priority, self.neighbor_interface_id,
                                             self.neighbor_ipv6_address, self.neighbor_options, self.neighbor_dr,
                                             self.neighbor_bdr, conf.ROUTER_ID)

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

        for query_neighbor in [self.neighbor_v2, self.neighbor_v3]:

            self.assertIsNotNone(query_neighbor.inactivity_timer)
            self.assertIsNotNone(query_neighbor.dd_packet_retransmit_timer)
            self.assertIsNotNone(query_neighbor.ls_request_retransmit_timer)
            self.assertIsNotNone(query_neighbor.ls_update_retransmit_timer)
            self.assertTrue(query_neighbor.inactivity_timer.initial_time > self.start_time)

            self.assertTrue(query_neighbor.inactivity_thread.isAlive())
            self.assertIsNone(query_neighbor.dd_packet_retransmit_thread)
            self.assertIsNone(query_neighbor.ls_request_retransmit_thread)
            self.assertIsNone(query_neighbor.ls_update_retransmit_thread)

            self.assertFalse(query_neighbor.reset.is_set())
            self.assertFalse(query_neighbor.inactivity_timeout.is_set())
            self.assertFalse(query_neighbor.inactivity_shutdown.is_set())
            self.assertFalse(query_neighbor.dd_packet_retransmit_timeout.is_set())
            self.assertFalse(query_neighbor.ls_request_retransmit_timeout.is_set())
            self.assertFalse(query_neighbor.ls_update_retransmit_timeout.is_set())
            self.assertFalse(query_neighbor.dd_packet_retransmit_shutdown.is_set())
            self.assertFalse(query_neighbor.ls_request_retransmit_shutdown.is_set())
            self.assertFalse(query_neighbor.ls_update_retransmit_shutdown.is_set())

    #  Successful run - 1 s
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            neighbor.Neighbor('', self.neighbor_priority, self.neighbor_interface_id, self.neighbor_ipv4_address,
                              self.neighbor_options, self.neighbor_dr, self.neighbor_bdr, conf.ROUTER_ID)
        with self.assertRaises(ValueError):
            neighbor.Neighbor(self.neighbor_id, self.neighbor_priority, self.neighbor_interface_id,
                              self.neighbor_ipv6_address, -1, self.neighbor_dr, self.neighbor_bdr, conf.ROUTER_ID)

    #  Successful run - 42 s
    def test_is_expired(self):
        self.assertFalse(self.neighbor_v2.is_expired())
        time.sleep(conf.ROUTER_DEAD_INTERVAL + 1)
        self.assertTrue(self.neighbor_v2.is_expired())

        self.assertFalse(self.neighbor_v2.reset.is_set())
        self.assertTrue(self.neighbor_v2.inactivity_timeout.is_set())
        self.assertFalse(self.neighbor_v2.inactivity_shutdown.is_set())

    #  Successful run - 42 s
    def test_reset_inactivity_timer(self):
        self.assertFalse(self.neighbor_v2.is_expired())
        time.sleep(conf.ROUTER_DEAD_INTERVAL / 2)
        self.neighbor_v2.reset_inactivity_timer()
        time.sleep((conf.ROUTER_DEAD_INTERVAL / 2) + 1)
        self.assertFalse(self.neighbor_v2.is_expired())

        self.assertFalse(self.neighbor_v2.reset.is_set())
        self.assertFalse(self.neighbor_v2.inactivity_timeout.is_set())
        self.assertFalse(self.neighbor_v2.inactivity_shutdown.is_set())

    #  Successful run - 15 s
    def test_retransmission_timer(self):
        for i in range(2):
            for query_neighbor in [self.neighbor_v2, self.neighbor_v3]:
                self.assertFalse(query_neighbor.is_retransmission_time(neighbor.DB_DESCRIPTION))
                self.assertFalse(query_neighbor.is_retransmission_time(neighbor.LS_REQUEST))
                self.assertFalse(query_neighbor.is_retransmission_time(neighbor.LS_UPDATE))
                query_neighbor.start_retransmission_timer(neighbor.DB_DESCRIPTION)
                query_neighbor.start_retransmission_timer(neighbor.LS_REQUEST)
                query_neighbor.start_retransmission_timer(neighbor.LS_UPDATE)
                self.assertFalse(query_neighbor.is_retransmission_time(neighbor.DB_DESCRIPTION))
                self.assertFalse(query_neighbor.is_retransmission_time(neighbor.LS_REQUEST))
                self.assertFalse(query_neighbor.is_retransmission_time(neighbor.LS_UPDATE))
                self.assertFalse(query_neighbor.dd_packet_retransmit_timeout.is_set())
                self.assertFalse(query_neighbor.ls_request_retransmit_timeout.is_set())
                self.assertFalse(query_neighbor.ls_update_retransmit_timeout.is_set())
                self.assertTrue(query_neighbor.dd_packet_retransmit_thread.isAlive())
                self.assertTrue(query_neighbor.ls_request_retransmit_thread.isAlive())
                self.assertTrue(query_neighbor.ls_update_retransmit_thread.isAlive())

            time.sleep(5)
            for query_neighbor in [self.neighbor_v2, self.neighbor_v3]:
                self.assertTrue(query_neighbor.is_retransmission_time(neighbor.DB_DESCRIPTION))
                self.assertTrue(query_neighbor.is_retransmission_time(neighbor.LS_REQUEST))
                self.assertTrue(query_neighbor.is_retransmission_time(neighbor.LS_UPDATE))
                self.assertFalse(query_neighbor.dd_packet_retransmit_timeout.is_set())  # Flag cleared by start method
                self.assertFalse(query_neighbor.ls_request_retransmit_timeout.is_set())
                self.assertFalse(query_neighbor.ls_update_retransmit_timeout.is_set())

                if i == 0:
                    query_neighbor.stop_retransmission_timer(neighbor.DB_DESCRIPTION)
                    query_neighbor.stop_retransmission_timer(neighbor.LS_REQUEST)
                    query_neighbor.stop_retransmission_timer(neighbor.LS_UPDATE)
                    time.sleep(1)
                    self.assertFalse(query_neighbor.dd_packet_retransmit_thread.isAlive())
                    self.assertFalse(query_neighbor.ls_request_retransmit_thread.isAlive())
                    self.assertFalse(query_neighbor.ls_update_retransmit_thread.isAlive())
                    query_neighbor.dd_packet_retransmit_timeout.set()
                    query_neighbor.ls_request_retransmit_timeout.set()
                    query_neighbor.ls_update_retransmit_timeout.set()
                    self.assertFalse(query_neighbor.is_retransmission_time(neighbor.DB_DESCRIPTION))
                    self.assertFalse(query_neighbor.is_retransmission_time(neighbor.LS_REQUEST))
                    self.assertFalse(query_neighbor.is_retransmission_time(neighbor.LS_UPDATE))

    #  Successful run - 2 s
    def test_delete_neighbor(self):
        self.assertFalse(self.neighbor_v2.inactivity_shutdown.is_set())
        self.neighbor_v2.delete_neighbor()
        time.sleep(1)
        self.assertFalse(self.neighbor_v2.reset.is_set())
        self.assertTrue(self.neighbor_v2.inactivity_timeout.is_set())
        self.assertTrue(self.neighbor_v2.inactivity_shutdown.is_set())

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
