import unittest

import router.router as router
import conf.conf as conf

'''
This class tests the top-level OSPF operations in the router
'''


#  Full successful run - 6-20 s
class RouterTest(unittest.TestCase):

    router_v2 = None
    router_v3 = None

    def setUp(self):
        self.router_v2 = router.Router(conf.VERSION_IPV4)
        self.router_v3 = router.Router(conf.VERSION_IPV6)

    #  Successful run - 6-10 s
    def test_constructor_v2_successful(self):
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

        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.pipelines))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.pipelines))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.shutdown_events))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.shutdown_events))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v2.threads))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(self.router_v3.threads))
        for interface_id in self.router_v2.interfaces:
            self.assertFalse(self.router_v2.shutdown_events[interface_id].is_set())
            self.assertTrue(self.router_v2.threads[interface_id].isAlive())
        for interface_id in self.router_v3.interfaces:
            self.assertFalse(self.router_v3.shutdown_events[interface_id].is_set())
            self.assertTrue(self.router_v3.threads[interface_id].isAlive())

    #  Successful run - 0-10 s
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            router.Router(1)
        with self.assertRaises(ValueError):
            router.Router(4)

    def tearDown(self):
        self.router_v2.shutdown_router()
        self.router_v3.shutdown_router()
        self.router_v2 = None
        self.router_v3 = None
