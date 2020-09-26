import unittest
import time

import area.area as area
import conf.conf as conf

'''
This class tests the area operations in the router
'''


#  Full successful run - 12-13 s
class AreaTest(unittest.TestCase):

    def setUp(self):
        self.area_id = '0.0.0.0'
        self.external_routing_capable = True
        self.area_v2 = area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, self.area_id, self.external_routing_capable,
                                 conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False, False)
        self.area_v3 = area.Area(conf.ROUTER_ID, conf.VERSION_IPV6, self.area_id, self.external_routing_capable,
                                 conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False, False)

    #  Successful run - 1 s
    def test_constructor_successful(self):
        self.assertEqual(conf.ROUTER_ID, self.area_v2.router_id)
        self.assertEqual(conf.ROUTER_ID, self.area_v3.router_id)
        self.assertEqual(conf.VERSION_IPV4, self.area_v2.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, self.area_v3.ospf_version)
        self.assertEqual(self.area_id, self.area_v2.area_id)
        self.assertEqual(self.area_id, self.area_v3.area_id)
        self.assertEqual(self.external_routing_capable, self.area_v2.external_routing_capable)
        self.assertEqual(self.external_routing_capable, self.area_v3.external_routing_capable)
        self.assertEqual(1, len(self.area_v2.database.get_lsdb(self.area_v2.get_interfaces(), None)))
        self.assertEqual(2, len(self.area_v3.database.get_lsdb(self.area_v3.get_interfaces(), None)))
        self.assertEqual(1, self.area_v2.database.get_lsdb(self.area_v2.get_interfaces(), None)[0].header.ls_type)
        self.assertEqual(0x2001, self.area_v3.database.get_lsdb(self.area_v3.get_interfaces(), None)[0].header.ls_type)
        self.assertEqual(0x2009, self.area_v3.database.get_lsdb(self.area_v3.get_interfaces(), None)[1].header.ls_type)

        interfaces_v2 = self.area_v2.interfaces
        interfaces_v3 = self.area_v3.interfaces
        self.assertEqual(1, len(interfaces_v2))
        self.assertEqual(1, len(interfaces_v3))
        self.assertTrue(conf.INTERFACE_NAMES[0] in interfaces_v2)
        self.assertTrue(conf.INTERFACE_NAMES[0] in interfaces_v3)
        interface_objects_v2 = interfaces_v2[conf.INTERFACE_NAMES[0]]
        interface_objects_v3 = interfaces_v3[conf.INTERFACE_NAMES[0]]
        self.assertTrue(4, len(interface_objects_v2))
        self.assertTrue(4, len(interface_objects_v3))
        interface_v2 = interface_objects_v2[area.INTERFACE_OBJECT]
        interface_v3 = interface_objects_v3[area.INTERFACE_OBJECT]
        self.assertEqual(conf.INTERFACE_NAMES[0], interface_v2.physical_identifier)
        self.assertEqual(conf.INTERFACE_NAMES[0], interface_v3.physical_identifier)
        thread_v2 = interface_objects_v2[area.INTERFACE_THREAD]
        thread_v3 = interface_objects_v3[area.INTERFACE_THREAD]
        self.assertTrue(thread_v2.isAlive())
        self.assertTrue(thread_v3.isAlive())
        self.assertTrue(self.area_v2.is_interface_operating(conf.INTERFACE_NAMES[0]))
        self.assertTrue(self.area_v3.is_interface_operating(conf.INTERFACE_NAMES[0]))
        pipeline_v2 = interface_objects_v2[area.PIPELINE]
        pipeline_v3 = interface_objects_v3[area.PIPELINE]
        self.assertTrue(pipeline_v2.empty())
        self.assertTrue(pipeline_v3.empty())
        shutdown_event_v2 = interface_objects_v2[area.SHUTDOWN_EVENT]
        shutdown_event_v3 = interface_objects_v3[area.SHUTDOWN_EVENT]
        self.assertFalse(shutdown_event_v2.is_set())
        self.assertFalse(shutdown_event_v3.is_set())

    #  Successful run - 1 s
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, 1, self.area_id, self.external_routing_capable, conf.INTERFACE_NAMES,
                      conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, 4, self.area_id, self.external_routing_capable, conf.INTERFACE_NAMES,
                      conf.INTERFACE_AREAS, False, False)

        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, '', self.external_routing_capable, conf.INTERFACE_NAMES,
                      conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, '        ', self.external_routing_capable,
                      conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, 'An invalid IP address', self.external_routing_capable,
                      conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, '0', self.external_routing_capable, conf.INTERFACE_NAMES,
                      conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, '0.', self.external_routing_capable, conf.INTERFACE_NAMES,
                      conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, '0.0.0', self.external_routing_capable, conf.INTERFACE_NAMES,
                      conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, '0.0.0.', self.external_routing_capable, conf.INTERFACE_NAMES,
                      conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, '0.0.0.0.', self.external_routing_capable,
                      conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False, False)
        with self.assertRaises(ValueError):
            area.Area(conf.ROUTER_ID, conf.VERSION_IPV4, '0.0.0.0.0', self.external_routing_capable,
                      conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False, False)

    #  Successful run - 1 s
    def test_create_interface_twice(self):
        self.area_v2.create_interface(conf.INTERFACE_NAMES[0])  # Interface is already created on startup
        self.area_v3.create_interface(conf.INTERFACE_NAMES[0])
        self.assertTrue(self.area_v2.is_interface_operating(conf.INTERFACE_NAMES[0]))
        self.assertTrue(self.area_v3.is_interface_operating(conf.INTERFACE_NAMES[0]))

    #  Successful run - 1 s
    def test_create_interface_invalid_interface_id(self):
        with self.assertRaises(ValueError):
            self.area_v2.create_interface('Invalid interface')
        with self.assertRaises(ValueError):
            self.area_v3.create_interface('Invalid interface')

    #  Successful run - 2 s
    def test_start_interface_after_shutdown(self):
        interface_objects_v2 = self.area_v2.interfaces[conf.INTERFACE_NAMES[0]]
        interface_objects_v3 = self.area_v3.interfaces[conf.INTERFACE_NAMES[0]]
        thread_v2 = interface_objects_v2[area.INTERFACE_THREAD]
        thread_v3 = interface_objects_v3[area.INTERFACE_THREAD]

        time.sleep(1)  # Required for successful interface shutdown
        self.area_v2.shutdown_interface(conf.INTERFACE_NAMES[0])
        self.area_v3.shutdown_interface(conf.INTERFACE_NAMES[0])
        self.assertFalse(thread_v2.isAlive())
        self.assertFalse(thread_v3.isAlive())
        self.assertFalse(self.area_v2.is_interface_operating(conf.INTERFACE_NAMES[0]))
        self.assertFalse(self.area_v3.is_interface_operating(conf.INTERFACE_NAMES[0]))

        self.area_v2.start_interface(conf.INTERFACE_NAMES[0])
        self.area_v3.start_interface(conf.INTERFACE_NAMES[0])
        #  New thread is assigned to interface on startup - Getting thread again is necessary
        thread_v2 = self.area_v2.interfaces[conf.INTERFACE_NAMES[0]][area.INTERFACE_THREAD]
        thread_v3 = self.area_v3.interfaces[conf.INTERFACE_NAMES[0]][area.INTERFACE_THREAD]
        self.assertTrue(self.area_v2.is_interface_operating(conf.INTERFACE_NAMES[0]))
        self.assertTrue(self.area_v3.is_interface_operating(conf.INTERFACE_NAMES[0]))
        self.assertTrue(thread_v2.isAlive())
        self.assertTrue(thread_v3.isAlive())

    #  Successful run - 1 s
    def test_start_interface_twice(self):
        self.area_v2.start_interface(conf.INTERFACE_NAMES[0])
        self.area_v3.start_interface(conf.INTERFACE_NAMES[0])
        self.assertTrue(self.area_v2.is_interface_operating(conf.INTERFACE_NAMES[0]))
        self.assertTrue(self.area_v3.is_interface_operating(conf.INTERFACE_NAMES[0]))

    #  Successful run - 1 s
    def test_start_interface_invalid_interface_id(self):
        with self.assertRaises(KeyError):
            self.area_v2.start_interface('Invalid interface')
        with self.assertRaises(KeyError):
            self.area_v3.start_interface('Invalid interface')

    #  Successful run - 2 s
    def test_shutdown_interface_twice(self):
        time.sleep(1)  # Required for successful interface shutdown
        self.area_v2.shutdown_interface(conf.INTERFACE_NAMES[0])
        self.area_v3.shutdown_interface(conf.INTERFACE_NAMES[0])
        self.area_v2.shutdown_interface(conf.INTERFACE_NAMES[0])
        self.area_v3.shutdown_interface(conf.INTERFACE_NAMES[0])
        self.assertFalse(self.area_v2.is_interface_operating(conf.INTERFACE_NAMES[0]))
        self.assertFalse(self.area_v3.is_interface_operating(conf.INTERFACE_NAMES[0]))

    #  Successful run - 1 s
    def test_shutdown_interface_invalid_interface_id(self):
        with self.assertRaises(KeyError):
            self.area_v2.shutdown_interface('Invalid interface')
        with self.assertRaises(KeyError):
            self.area_v3.shutdown_interface('Invalid interface')

    #  Successful run - 1 s
    def test_is_interface_operating_invalid_interface_id(self):
        with self.assertRaises(KeyError):
            self.area_v2.is_interface_operating('Invalid interface')
        with self.assertRaises(KeyError):
            self.area_v3.is_interface_operating('Invalid interface')

    def tearDown(self):
        time.sleep(1)  # Required for successful tear down
        self.area_v2.shutdown_area()
        self.area_v3.shutdown_area()
