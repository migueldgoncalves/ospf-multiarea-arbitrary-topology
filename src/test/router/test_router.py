import unittest
import threading
import time
import multiprocessing

import router.router as router
import conf.conf as conf
import area.area as area
import router.kernel_table as kernel_table

'''
This class tests the top-level OSPF operations in the router
'''


#  Full successful run - 36-37 s
class RouterTest(unittest.TestCase):

    #  Successful run - 36-37 s
    def test_successful_execution(self):
        test_passed = multiprocessing.Event()
        RouterTest.execute_test(self.successful_execution, 35, test_passed)
        if not test_passed.is_set():
            self.fail()

    def successful_execution(self, version, test_passed, r):
        self.assertEqual(version, r.ospf_version)

        self.assertEqual(conf.ROUTER_ID, r.router_id)
        self.assertEqual(len(list(set(conf.INTERFACE_AREAS))), len(r.area_ids))
        for area_id in conf.INTERFACE_AREAS:
            if area_id not in r.area_ids:
                self.fail("Router is missing one or more areas")
        time.sleep(0.1)  # Allows interface threads to start
        self.assertEqual(len(conf.INTERFACE_NAMES), len(r.interfaces))
        router_interfaces = []
        for interface_id in r.interfaces:
            for area_id in r.area_ids:
                if interface_id in r.areas[area_id].interfaces:
                    router_interfaces.append(interface_id)
                    self.assertTrue(r.areas[area_id].is_interface_operating(interface_id))
        self.assertEqual(set(conf.INTERFACE_NAMES), set(router_interfaces))
        self.assertEqual(conf.MTU, r.max_ip_datagram)

        self.assertEqual(len(conf.INTERFACE_NAMES), len(r.packet_pipelines))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(r.socket_shutdown_events))
        self.assertEqual(len(conf.INTERFACE_NAMES), len(r.socket_processes))
        for interface_id in r.interfaces:
            self.assertFalse(r.socket_shutdown_events[interface_id].is_set())
            self.assertTrue(r.socket_processes[interface_id].is_alive())
        self.assertFalse(r.router_shutdown_event.is_set())

        time.sleep(20)  # Waits for the router LSDB and kernel routing table to stabilize
        self.assertEqual(10, len(kernel_table.KernelTable.get_all_ospf_routes()))
        for area_id in r.area_ids:
            #  Method returns copy of LSDB, fetching it twice is necessary
            ls_age = r.areas[area_id].database.get_lsdb([], None)[0].header.ls_age
            self.assertTrue(ls_age > 0)
            time.sleep(2)
            self.assertTrue(r.areas[area_id].database.get_lsdb([], None)[0].header.ls_age > ls_age)
        neighbor_id = '1.1.1.1'
        neighbor = r.interfaces[conf.INTERFACE_NAMES[0]][area.INTERFACE_OBJECT].neighbors[neighbor_id]
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, neighbor.neighbor_state)

        test_passed.set()

    #  Successful run - Instant
    def test_constructor_invalid_parameters(self):
        new_router = router.Router()
        with self.assertRaises(ValueError):
            new_router.set_up(
                conf.ROUTER_ID, 1, multiprocessing.Event(), conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False,
                multiprocessing.Queue(), multiprocessing.Event())
        with self.assertRaises(ValueError):
            new_router.set_up(
                conf.ROUTER_ID, 4, multiprocessing.Event(), conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False,
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

    #  Starts process which runs router and test in separate threads, waits specified time and performs process shutdown
    @staticmethod
    def execute_test(test_to_run, time_to_wait, test_passed):
        kernel_table.KernelTable.delete_all_ospf_routes(0)

        shutdown_event = multiprocessing.Event()
        process_v2 = multiprocessing.Process(target=RouterTest.run_test_threads, args=(
            conf.VERSION_IPV4, test_to_run, shutdown_event, test_passed))
        process_v3 = multiprocessing.Process(target=RouterTest.run_test_threads, args=(
            conf.VERSION_IPV6, test_to_run, shutdown_event, test_passed))
        process_v2.start()
        process_v3.start()

        time.sleep(time_to_wait)  # All asserts should be passed during this time
        shutdown_event.set()

        process_v2.join()
        process_v3.join()

    #  Runs router in one thread and test in another
    @staticmethod
    def run_test_threads(version, test_to_run, shutdown, test_passed):
        r = router.Router()
        router_thread = threading.Thread(target=r.set_up, args=(
            conf.ROUTER_ID, version, shutdown, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False,
            multiprocessing.Queue(), multiprocessing.Event()))
        router_thread.start()
        time.sleep(0.1)
        test_thread = threading.Thread(target=test_to_run, args=(version, test_passed, r))
        test_thread.start()

        test_thread.join()
        router_thread.join()


if __name__ == '__main__':
    unittest.main()
