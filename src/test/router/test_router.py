import unittest
import threading
import time
import multiprocessing

import router.router as router
import conf.conf as conf
import area.area as area

'''
This class tests the top-level OSPF operations in the router
'''


#  Full successful run - 60-62 s
class RouterTest(unittest.TestCase):

    def setUp(self):
        self.shutdown_event = None
        self.r = None
        self.thread = None

    #  Successful run - 40 s
    def test_constructor_successful(self):
        self.constructor_successful(conf.VERSION_IPV4)
        self.constructor_successful(conf.VERSION_IPV6)

    def constructor_successful(self, version):
        self.router_set_up(version)
        self.assertEqual(version, self.r.ospf_version)

        self.assertEqual(conf.ROUTER_ID, self.r.router_id)
        self.assertEqual(len(list(set(conf.INTERFACE_AREAS))), len(self.r.area_ids))
        for area_id in conf.INTERFACE_AREAS:
            if area_id not in self.r.area_ids:
                self.fail("Router is missing one or more areas")
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.r.interfaces))
        router_interfaces = []
        for interface_id in self.r.interfaces:
            for area_id in self.r.area_ids:
                if interface_id in self.r.areas[area_id].interfaces:
                    router_interfaces.append(interface_id)
                    self.assertTrue(self.r.areas[area_id].is_interface_operating(interface_id))
        self.assertEqual(set(conf.INTERFACE_NAMES), set(router_interfaces))
        self.assertEqual(conf.MTU, self.r.max_ip_datagram)

        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.r.packet_pipelines))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.r.socket_shutdown_events))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.r.socket_processes))
        for interface_id in self.r.interfaces:
            self.assertFalse(self.r.socket_shutdown_events[interface_id].is_set())
            self.assertTrue(self.r.socket_processes[interface_id].is_alive())
        self.assertFalse(self.r.router_shutdown_event.is_set())

        time.sleep(15)  # Waits for the router LSDB to stabilize
        for area_id in self.r.area_ids:
            router_lsa = self.r.areas[area_id].database.get_lsdb([], None)[0]
            time.sleep(2)
            ls_age = router_lsa.header.ls_age
            self.assertTrue(ls_age > 0)
            time.sleep(2)
            self.assertTrue(router_lsa.header.ls_age > ls_age)

        self.router_tear_down()

    #  Successful run - 20-22 s
    def test_main_loop_successful(self):
        self.main_loop_successful(conf.VERSION_IPV4)
        self.main_loop_successful(conf.VERSION_IPV6)

    def main_loop_successful(self, version):
        self.router_set_up(version)
        time.sleep(10)  # Ensures neighbor has time to send Hello packets acknowledging this router
        neighbor_id = '1.1.1.1'
        neighbor = self.r.interfaces[conf.INTERFACE_NAMES[0]][area.INTERFACE_OBJECT].neighbors[neighbor_id]
        self.assertTrue(neighbor.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT])
        self.router_tear_down()

    #  Successful run - Instant
    def test_constructor_invalid_parameters(self):
        new_router = router.Router()
        with self.assertRaises(ValueError):
            new_router.set_up(
                conf.ROUTER_ID, 1, self.shutdown_event, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False,
                multiprocessing.Queue(), multiprocessing.Event())
        with self.assertRaises(ValueError):
            new_router.set_up(
                conf.ROUTER_ID, 4, self.shutdown_event, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False,
                multiprocessing.Queue(), multiprocessing.Event())

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

    def router_set_up(self, version):
        self.shutdown_event = threading.Event()
        self.r = router.Router()
        self.thread = threading.Thread(target=self.r.set_up, args=(
            conf.ROUTER_ID, version, self.shutdown_event, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False,
            multiprocessing.Queue(), multiprocessing.Event()))
        self.thread.start()
        time.sleep(0.2)

    def router_tear_down(self):
        self.shutdown_event.set()
        self.thread.join()


if __name__ == '__main__':
    unittest.main()
