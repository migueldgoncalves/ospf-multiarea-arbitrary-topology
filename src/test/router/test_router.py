import unittest
import queue
import threading
import time

import router.router as router
import conf.conf as conf
import area.area as area

'''
This class tests the top-level OSPF operations in the router
'''


#  Full successful run - 12-35 s
class RouterTest(unittest.TestCase):

    command_pipeline_v2 = None
    command_pipeline_v3 = None
    shutdown_event_v2 = None
    shutdown_event_v3 = None
    thread_v2 = None
    thread_v3 = None
    router_v2 = None
    router_v3 = None

    def setUp(self):
        self.command_pipeline_v2 = queue.Queue()
        self.command_pipeline_v3 = queue.Queue()
        self.shutdown_event_v2 = threading.Event()
        self.shutdown_event_v3 = threading.Event()
        self.router_v2 = router.Router(
            conf.VERSION_IPV4, self.command_pipeline_v2, self.shutdown_event_v2)
        self.router_v3 = router.Router(
            conf.VERSION_IPV6, self.command_pipeline_v3, self.shutdown_event_v3)
        self.thread_v2 = threading.Thread(target=self.router_v2.main_loop)
        self.thread_v3 = threading.Thread(target=self.router_v3.main_loop)
        self.thread_v2.start()
        self.thread_v3.start()

    #  Successful run - 2-10 s
    def test_constructor_successful(self):
        self.assertEqual(conf.VERSION_IPV4, self.router_v2.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, self.router_v3.ospf_version)

        self.assertEqual(conf.ROUTER_ID, self.router_v2.router_id)
        self.assertEqual(conf.ROUTER_ID, self.router_v3.router_id)
        self.assertEqual(len(list(set(conf.INTERFACE_AREAS))), len(self.router_v2.areas))
        self.assertEqual(len(list(set(conf.INTERFACE_AREAS))), len(self.router_v3.areas))
        for area_id in conf.INTERFACE_AREAS:
            if (area_id not in self.router_v2.areas) | (area_id not in self.router_v3.areas):
                self.fail("Router is missing one or more areas")
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.interfaces))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.interfaces))
        router_interfaces_v2 = []
        router_interfaces_v3 = []
        for interface_id in self.router_v2.interfaces:
            for area_id in self.router_v2.areas:
                if interface_id in self.router_v2.areas[area_id].interfaces:
                    router_interfaces_v2.append(interface_id)
                    self.assertTrue(self.router_v2.areas[area_id].is_interface_operating(interface_id))
        for interface_id in self.router_v3.interfaces:
            for area_id in self.router_v3.areas:
                if interface_id in self.router_v3.areas[area_id].interfaces:
                    router_interfaces_v3.append(interface_id)
                    self.assertTrue(self.router_v3.areas[area_id].is_interface_operating(interface_id))
        self.assertEqual(set(conf.INTERFACE_NAMES), set(router_interfaces_v2))
        self.assertEqual(set(conf.INTERFACE_NAMES), set(router_interfaces_v3))
        self.assertEqual(conf.MTU, self.router_v2.max_ip_datagram)
        self.assertEqual(conf.MTU, self.router_v3.max_ip_datagram)

        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.packet_pipelines))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.packet_pipelines))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.interface_shutdown_events))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.interface_shutdown_events))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.interface_threads))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.interface_threads))
        for interface_id in self.router_v2.interfaces:
            self.assertFalse(self.router_v2.interface_shutdown_events[interface_id].is_set())
            self.assertTrue(self.router_v2.interface_threads[interface_id].isAlive())
        for interface_id in self.router_v3.interfaces:
            self.assertFalse(self.router_v3.interface_shutdown_events[interface_id].is_set())
            self.assertTrue(self.router_v3.interface_threads[interface_id].isAlive())
        self.assertTrue(self.router_v2.command_pipeline.empty())
        self.assertTrue(self.router_v3.command_pipeline.empty())
        self.assertFalse(self.router_v2.router_shutdown_event.is_set())
        self.assertFalse(self.router_v3.router_shutdown_event.is_set())

    #  Successful run - 10-15 s
    def test_main_loop_successful(self):
        time.sleep(10)  # Ensures neighbor has time to send Hello packets acknowledging this router
        neighbor_id = '1.1.1.1'
        neighbor_v2 = self.router_v2.interfaces[conf.INTERFACE_NAMES[0]][area.INTERFACE_OBJECT].neighbors[neighbor_id]
        neighbor_v3 = self.router_v3.interfaces[conf.INTERFACE_NAMES[0]][area.INTERFACE_OBJECT].neighbors[neighbor_id]
        self.assertTrue(neighbor_v2.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT])
        self.assertTrue(neighbor_v3.neighbor_state not in [conf.NEIGHBOR_STATE_DOWN, conf.NEIGHBOR_STATE_INIT])

    #  Successful run - 0-10 s
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            router.Router(1, self.command_pipeline_v2, self.shutdown_event_v2)
        with self.assertRaises(ValueError):
            router.Router(4, self.command_pipeline_v2, self.shutdown_event_v2)

    def tearDown(self):
        self.shutdown_event_v2.set()
        self.shutdown_event_v3.set()
        self.command_pipeline_v2 = None
        self.command_pipeline_v3 = None
        self.shutdown_event_v2 = None
        self.shutdown_event_v3 = None
        self.thread_v2.join()
        self.thread_v3.join()
        self.thread_v2 = None
        self.thread_v3 = None
        self.router_v2 = None
        self.router_v3 = None
