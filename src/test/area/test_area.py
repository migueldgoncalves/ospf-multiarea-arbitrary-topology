import unittest
import time

import area.area as area
import conf.conf as conf

'''
This class tests the area operations in the router
'''

AREA_ID = '0.0.0.0'
EXTERNAL_ROUTING_CAPABLE = True
INTERFACE_NAME = 'ens33'
INVALID_INTERFACE_NAME = 'Invalid interface'


#  Full successful run - 30 s
class AreaTest(unittest.TestCase):

    area = None

    def setUp(self):
        self.area = area.Area(AREA_ID, EXTERNAL_ROUTING_CAPABLE)

    #  Successful run - 23 s
    #  This smaller tests conflicted with each other when separate - Therefore they are joined in a single larger test
    def test_area_creation(self):

        #  Class constructor arguments

        self.assertEqual(AREA_ID, self.area.area_id)
        self.assertEqual(EXTERNAL_ROUTING_CAPABLE, self.area.external_routing_capable)

        #  Base successful operation

        interfaces = self.area.interfaces
        self.assertEqual(1, len(interfaces))
        self.assertTrue(INTERFACE_NAME in self.area.interfaces)
        interface_objects = interfaces[INTERFACE_NAME]
        self.assertTrue(4, len(interface_objects))
        interface = interface_objects[area.INTERFACE_OBJECT]
        self.assertEqual(INTERFACE_NAME, interface.physical_identifier)
        thread = interface_objects[area.INTERFACE_THREAD]
        self.assertTrue(thread.isAlive())
        shutdown_event = interface_objects[area.SHUTDOWN_EVENT]
        self.assertFalse(shutdown_event.is_set())

        time.sleep(2 * conf.HELLO_INTERVAL)  # Allows for Hello packets to be sent

        #  Successful interface startup after shutdown

        interface_thread = self.area.interfaces[INTERFACE_NAME][area.INTERFACE_THREAD]
        self.assertTrue(self.area.is_interface_operating(INTERFACE_NAME))
        self.assertTrue(interface_thread.isAlive())

        self.area.shutdown_interface(INTERFACE_NAME)
        time.sleep(1)
        self.assertFalse(self.area.is_interface_operating(INTERFACE_NAME))
        self.assertFalse(interface_thread.isAlive())

        self.area.start_interface(INTERFACE_NAME)
        #  New thread is assigned to interface on startup - Getting thread again is necessary
        interface_thread = self.area.interfaces[INTERFACE_NAME][area.INTERFACE_THREAD]
        time.sleep(1)
        self.assertTrue(self.area.is_interface_operating(INTERFACE_NAME))
        self.assertTrue(interface_thread.isAlive())

        #  Create interface twice

        self.area.create_interface(INTERFACE_NAME)  # Interface is already created on startup
        self.assertTrue(self.area.is_interface_operating(INTERFACE_NAME))

        #  Invalid Area ID

        with self.assertRaises(ValueError):
            area.Area('', EXTERNAL_ROUTING_CAPABLE)
        with self.assertRaises(ValueError):
            area.Area('        ', EXTERNAL_ROUTING_CAPABLE)
        with self.assertRaises(ValueError):
            area.Area('An invalid IP address', EXTERNAL_ROUTING_CAPABLE)
        with self.assertRaises(ValueError):
            area.Area('0', EXTERNAL_ROUTING_CAPABLE)
        with self.assertRaises(ValueError):
            area.Area('0.', EXTERNAL_ROUTING_CAPABLE)
        with self.assertRaises(ValueError):
            area.Area('0.0.0', EXTERNAL_ROUTING_CAPABLE)
        with self.assertRaises(ValueError):
            area.Area('0.0.0.', EXTERNAL_ROUTING_CAPABLE)
        with self.assertRaises(ValueError):
            area.Area('0.0.0.0.', EXTERNAL_ROUTING_CAPABLE)
        with self.assertRaises(ValueError):
            area.Area('0.0.0.0.0', EXTERNAL_ROUTING_CAPABLE)

    #  Successful run - 1 s
    def test_create_interface_invalid_interface_id(self):
        with self.assertRaises(ValueError):
            self.area.create_interface(INVALID_INTERFACE_NAME)

    #  Successful run - 1 s
    def test_start_interface_twice(self):
        self.area.start_interface(INTERFACE_NAME)
        self.assertTrue(self.area.is_interface_operating(INTERFACE_NAME))

    #  Successful run - 1 s
    def test_start_interface_invalid_interface_id(self):
        with self.assertRaises(KeyError):
            self.area.start_interface(INVALID_INTERFACE_NAME)

    #  Successful run - 2 s
    def test_shutdown_interface_twice(self):
        time.sleep(1)  # Required for successful interface shutdown
        self.area.shutdown_interface(INTERFACE_NAME)
        self.area.shutdown_interface(INTERFACE_NAME)
        self.assertFalse(self.area.is_interface_operating(INTERFACE_NAME))

    #  Successful run - 1 s
    def test_shutdown_interface_invalid_interface_id(self):
        with self.assertRaises(KeyError):
            self.area.shutdown_interface(INVALID_INTERFACE_NAME)

    #  Successful run - 1 s
    def test_is_interface_operating_invalid_interface_id(self):
        with self.assertRaises(KeyError):
            self.area.is_interface_operating(INVALID_INTERFACE_NAME)

    def tearDown(self):
        time.sleep(1)  # Required for successful tear down
        self.area.shutdown_area()
        self.area = None
