import unittest
import threading
import time

import router.router as router
import conf.conf as conf
import area.area as area

'''
This class tests the top-level OSPF operations in the router
'''


#  Full successful run - 35-40 s
class RouterTest(unittest.TestCase):

    def setUp(self):
        self.shutdown_event_v2 = None
        self.shutdown_event_v3 = None
        self.router_v2 = None
        self.router_v3 = None
        self.thread_v2 = None
        self.thread_v3 = None

    #  Successful run - 25 s
    def test_constructor_successful(self):
        self.router_set_up()
        self.assertEqual(conf.VERSION_IPV4, self.router_v2.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, self.router_v3.ospf_version)

        self.assertEqual(conf.ROUTER_ID, self.router_v2.router_id)
        self.assertEqual(conf.ROUTER_ID, self.router_v3.router_id)
        self.assertEqual(len(list(set(conf.INTERFACE_AREAS))), len(self.router_v2.area_ids))
        self.assertEqual(len(list(set(conf.INTERFACE_AREAS))), len(self.router_v3.area_ids))
        for area_id in conf.INTERFACE_AREAS:
            if (area_id not in self.router_v2.area_ids) | (area_id not in self.router_v3.area_ids):
                self.fail("Router is missing one or more areas")
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.interfaces))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.interfaces))
        router_interfaces_v2 = []
        router_interfaces_v3 = []
        for interface_id in self.router_v2.interfaces:
            for area_id in self.router_v2.area_ids:
                if interface_id in self.router_v2.areas[area_id].interfaces:
                    router_interfaces_v2.append(interface_id)
                    self.assertTrue(self.router_v2.areas[area_id].is_interface_operating(interface_id))
        for interface_id in self.router_v3.interfaces:
            for area_id in self.router_v3.area_ids:
                if interface_id in self.router_v3.areas[area_id].interfaces:
                    router_interfaces_v3.append(interface_id)
                    self.assertTrue(self.router_v3.areas[area_id].is_interface_operating(interface_id))
        self.assertEqual(set(conf.INTERFACE_NAMES), set(router_interfaces_v2))
        self.assertEqual(set(conf.INTERFACE_NAMES), set(router_interfaces_v3))
        self.assertEqual(conf.MTU, self.router_v2.max_ip_datagram)
        self.assertEqual(conf.MTU, self.router_v3.max_ip_datagram)

        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.packet_pipelines))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.packet_pipelines))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.socket_shutdown_events))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.socket_shutdown_events))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.socket_threads))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.socket_threads))
        for interface_id in self.router_v2.interfaces:
            self.assertFalse(self.router_v2.socket_shutdown_events[interface_id].is_set())
            self.assertTrue(self.router_v2.socket_threads[interface_id].isAlive())
        for interface_id in self.router_v3.interfaces:
            self.assertFalse(self.router_v3.socket_shutdown_events[interface_id].is_set())
            self.assertTrue(self.router_v3.socket_threads[interface_id].isAlive())
        self.assertFalse(self.router_v2.router_shutdown_event.is_set())
        self.assertFalse(self.router_v3.router_shutdown_event.is_set())

        time.sleep(15)  # Waits for the router LSDB to stabilize
        for r in [self.router_v2, self.router_v3]:
            for area_id in r.area_ids:
                router_lsa = r.areas[area_id].database.get_lsdb([], None)[0]
                time.sleep(2)
                ls_age = router_lsa.header.ls_age
                self.assertTrue(ls_age > 0)
                time.sleep(2)
                self.assertTrue(router_lsa.header.ls_age > ls_age)

        self.router_tear_down()

    #  Successful run - 10-15 s
    def test_main_loop_successful(self):
        self.router_set_up()
        time.sleep(10)  # Ensures neighbor has time to send Hello packets acknowledging this router
        neighbor_id = '1.1.1.1'
        neighbor_v2 = self.router_v2.interfaces[conf.INTERFACE_NAMES[0]][area.INTERFACE_OBJECT].neighbors[neighbor_id]
        neighbor_v3 = self.router_v3.interfaces[conf.INTERFACE_NAMES[0]][area.INTERFACE_OBJECT].neighbors[neighbor_id]
        self.assertTrue(neighbor_v2.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT])
        self.assertTrue(neighbor_v3.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT])
        self.router_tear_down()

    #  Successful run - Instant
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            router.Router(
                conf.ROUTER_ID, 1, self.shutdown_event_v2, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False)
        with self.assertRaises(ValueError):
            router.Router(
                conf.ROUTER_ID, 4, self.shutdown_event_v2, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False)

    #  Successful run - Instant
    def test_get_unique_values(self):
        self.assertEqual(['0.0.0.0'], router.Router.get_unique_values(['0.0.0.0']))
        self.assertEqual(['0.0.0.0'], router.Router.get_unique_values(['0.0.0.0', '0.0.0.0']))
        self.assertEqual(2, len(router.Router.get_unique_values(['0.0.0.0', '0.0.0.0', '1.1.1.1'])))
        for area_id in ['0.0.0.0', '1.1.1.1']:
            self.assertTrue(area_id in router.Router.get_unique_values(['0.0.0.0', '0.0.0.0', '1.1.1.1']))
        self.assertEqual(2, len(router.Router.get_unique_values(['0.0.0.0', '0.0.0.0', '1.1.1.1', '1.1.1.1'])))
        for area_id in ['0.0.0.0', '1.1.1.1']:
            self.assertTrue(area_id in router.Router.get_unique_values(['0.0.0.0', '0.0.0.0', '1.1.1.1', '1.1.1.1']))
        self.assertEqual(3, len(router.Router.get_unique_values(
            ['0.0.0.0', '0.0.0.0', '1.1.1.1', '1.1.1.1', '2.2.2.2'])))
        for area_id in ['0.0.0.0', '1.1.1.1', '2.2.2.2']:
            self.assertTrue(area_id in router.Router.get_unique_values(
                ['0.0.0.0', '0.0.0.0', '1.1.1.1', '1.1.1.1', '2.2.2.2']))

    #  Successful run - Instant
    def test_is_abr(self):
        self.assertFalse(router.Router.is_abr([]))
        self.assertFalse(router.Router.is_abr(['0.0.0.0']))
        self.assertFalse(router.Router.is_abr(['1.1.1.1']))
        self.assertFalse(router.Router.is_abr(['0.0.0.0', '0.0.0.0']))
        self.assertFalse(router.Router.is_abr(['1.1.1.1', '1.1.1.1']))
        self.assertFalse(router.Router.is_abr(['0.0.0.0', '0.0.0.0', '0.0.0.0']))
        self.assertFalse(router.Router.is_abr(['1.1.1.1', '1.1.1.1', '1.1.1.1']))
        self.assertTrue(router.Router.is_abr(['0.0.0.0', '1.1.1.1']))
        self.assertTrue(router.Router.is_abr(['1.1.1.1', '0.0.0.0']))
        self.assertTrue(router.Router.is_abr(['1.1.1.1', '0.0.0.0', '0.0.0.0']))
        self.assertTrue(router.Router.is_abr(['0.0.0.0', '1.1.1.1', '0.0.0.0']))
        self.assertTrue(router.Router.is_abr(['0.0.0.0', '0.0.0.0', '1.1.1.1']))
        self.assertTrue(router.Router.is_abr(['0.0.0.0', '1.1.1.1', '1.1.1.1']))
        self.assertTrue(router.Router.is_abr(['1.1.1.1', '0.0.0.0', '1.1.1.1']))
        self.assertTrue(router.Router.is_abr(['1.1.1.1', '1.1.1.1', '0.0.0.0']))
        self.assertTrue(router.Router.is_abr(['0.0.0.1', '1.1.1.1', '0.0.0.0']))

    #  #  #  #  #  #  #  #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #  #

    def router_set_up(self):
        self.shutdown_event_v2 = threading.Event()
        self.shutdown_event_v3 = threading.Event()
        self.router_v2 = router.Router(conf.ROUTER_ID, conf.VERSION_IPV4, self.shutdown_event_v2, conf.INTERFACE_NAMES,
                                       conf.INTERFACE_AREAS, False)
        self.router_v3 = router.Router(conf.ROUTER_ID, conf.VERSION_IPV6, self.shutdown_event_v3, conf.INTERFACE_NAMES,
                                       conf.INTERFACE_AREAS, False)
        self.thread_v2 = threading.Thread(target=self.router_v2.main_loop)
        self.thread_v3 = threading.Thread(target=self.router_v3.main_loop)
        self.thread_v2.start()
        self.thread_v3.start()

    def router_tear_down(self):
        self.shutdown_event_v2.set()
        self.shutdown_event_v3.set()
        self.thread_v2.join()
        self.thread_v3.join()
