import unittest
import threading
import time
import multiprocessing
import copy

import router.router as router
import conf.conf as conf
import area.area as area
import router.kernel_table as kernel_table
import area.lsdb as lsdb
import lsa.lsa as lsa

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
                multiprocessing.Queue(), multiprocessing.Event(), conf.INTERFACE_COSTS)
        with self.assertRaises(ValueError):
            new_router.set_up(
                conf.ROUTER_ID, 4, multiprocessing.Event(), conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False,
                multiprocessing.Queue(), multiprocessing.Event(), conf.INTERFACE_COSTS)

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

    #  Successful run - Instant
    def test_clean_unconnected_routers(self):
        #  Setup
        router_id_1 = '1.1.1.1'
        router_id_2 = '2.2.2.2'
        router_id_3 = '3.3.3.3'
        router_id_4 = '4.4.4.4'
        router_ip_1_1 = '222.222.1.1'
        router_ip_1_2 = '222.222.2.1'
        router_ip_2 = '222.222.1.2'
        router_ip_3 = '222.222.1.3'
        router_ip_4 = '222.222.2.4'
        network_prefix_1 = '222.222.1.0'
        network_prefix_2 = '222.222.2.0'
        options = conf.OPTIONS_V2
        cost = 10
        network_mask = '255.255.255.0'
        area_1 = '1.1.1.1'
        area_2 = '2.2.2.2'

        #  Case 1

        router_lsa_1 = lsa.Lsa()
        router_lsa_2 = lsa.Lsa()
        router_lsa_3 = lsa.Lsa()
        network_lsa_1 = lsa.Lsa()

        router_lsa_1.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_ROUTER, router_id_1, router_id_1,
                                   conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        router_lsa_2.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_ROUTER, router_id_2, router_id_2,
                                   conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        router_lsa_3.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_ROUTER, router_id_3, router_id_3,
                                   conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        network_lsa_1.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_NETWORK, conf.DEFAULT_LINK_STATE_ID,
                                    router_ip_1_1, conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        router_lsa_1.create_router_lsa_body(False, False, True, options, conf.VERSION_IPV4)
        router_lsa_2.create_router_lsa_body(False, False, True, options, conf.VERSION_IPV4)
        router_lsa_3.create_router_lsa_body(False, False, True, options, conf.VERSION_IPV4)
        network_lsa_1.create_network_lsa_body(
            network_mask, options, [router_id_1, router_id_2, router_id_3], conf.VERSION_IPV4)
        router_lsa_1.add_link_info_v2(
            router_ip_1_1, router_ip_1_1, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, cost)
        router_lsa_2.add_link_info_v2(router_ip_1_1, router_ip_2, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, cost)
        router_lsa_3.add_link_info_v2(router_ip_1_1, router_ip_3, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, cost)

        database = lsdb.Lsdb(conf.VERSION_IPV4, conf.BACKBONE_AREA)
        for query_lsa in [router_lsa_1, router_lsa_2, router_lsa_3, network_lsa_1]:
            database.add_lsa(query_lsa, None)
        lsdb_dict = {conf.BACKBONE_AREA: database}

        self.assertTrue(router.Router.is_router_connected(router_id_1, lsdb_dict, conf.VERSION_IPV4))
        self.assertTrue(router.Router.is_router_connected(router_id_2, lsdb_dict, conf.VERSION_IPV4))
        self.assertTrue(router.Router.is_router_connected(router_id_3, lsdb_dict, conf.VERSION_IPV4))
        self.assertFalse(router.Router.is_router_connected('10.10.10.10', lsdb_dict, conf.VERSION_IPV4))
        lsdb_dict = router.Router.clean_unconnected_routers(copy.deepcopy(lsdb_dict), None, conf.VERSION_IPV4)
        self.assertEqual(4, len(lsdb_dict[conf.BACKBONE_AREA].get_lsdb([], None)))

        router_lsa_3.body.links = []
        router_lsa_3.add_link_info_v2(network_prefix_1, network_mask, conf.LINK_TO_STUB_NETWORK, conf.DEFAULT_TOS, cost)
        network_lsa_1.body.attached_routers = [router_id_1, router_id_2]
        database = lsdb.Lsdb(conf.VERSION_IPV4, conf.BACKBONE_AREA)
        for query_lsa in [router_lsa_1, router_lsa_2, router_lsa_3, network_lsa_1]:
            database.add_lsa(query_lsa, None)
        lsdb_dict = {conf.BACKBONE_AREA: database}

        self.assertTrue(router.Router.is_router_connected(router_id_1, lsdb_dict, conf.VERSION_IPV4))
        self.assertTrue(router.Router.is_router_connected(router_id_2, lsdb_dict, conf.VERSION_IPV4))
        self.assertFalse(router.Router.is_router_connected(router_id_3, lsdb_dict, conf.VERSION_IPV4))
        lsdb_dict = router.Router.clean_unconnected_routers(copy.deepcopy(lsdb_dict), None, conf.VERSION_IPV4)
        self.assertNotEqual(len(database.get_lsdb([], None)), len(lsdb_dict[conf.BACKBONE_AREA].get_lsdb([], None)))
        self.assertEqual(3, len(lsdb_dict[conf.BACKBONE_AREA].get_lsdb([], None)))
        self.assertEqual(2, len(lsdb_dict[conf.BACKBONE_AREA].router_lsa_list))
        self.assertEqual(1, len(lsdb_dict[conf.BACKBONE_AREA].network_lsa_list))

        #  Case 2

        router_lsa_1_1 = lsa.Lsa()
        router_lsa_1_2 = lsa.Lsa()
        router_lsa_2 = lsa.Lsa()
        router_lsa_3 = lsa.Lsa()
        router_lsa_4 = lsa.Lsa()
        network_lsa_1 = lsa.Lsa()
        network_lsa_2 = lsa.Lsa()

        router_lsa_1_1.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_ROUTER, router_id_1, router_id_1,
                                     conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        router_lsa_1_2.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_ROUTER, router_id_1, router_id_1,
                                     conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        router_lsa_2.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_ROUTER, router_id_2, router_id_2,
                                   conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        router_lsa_3.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_ROUTER, router_id_3, router_id_3,
                                   conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        router_lsa_4.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_ROUTER, router_id_4, router_id_4,
                                   conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        network_lsa_1.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_NETWORK, router_ip_3, router_id_3,
                                    conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        network_lsa_2.create_header(conf.INITIAL_LS_AGE, options, conf.LSA_TYPE_NETWORK, router_ip_4, router_id_4,
                                    conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        router_lsa_1_1.create_router_lsa_body(False, False, True, options, conf.VERSION_IPV4)
        router_lsa_1_2.create_router_lsa_body(False, False, True, options, conf.VERSION_IPV4)
        router_lsa_2.create_router_lsa_body(False, False, True, options, conf.VERSION_IPV4)
        router_lsa_3.create_router_lsa_body(False, False, True, options, conf.VERSION_IPV4)
        router_lsa_4.create_router_lsa_body(False, False, True, options, conf.VERSION_IPV4)
        network_lsa_1.create_network_lsa_body(
            network_mask, options, [router_id_1, router_id_2, router_id_3], conf.VERSION_IPV4)
        network_lsa_2.create_network_lsa_body(network_mask, options, [router_id_1, router_id_4], conf.VERSION_IPV4)
        router_lsa_1_1.add_link_info_v2(
            router_ip_3, router_ip_1_1, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, cost)
        router_lsa_1_2.add_link_info_v2(
            router_ip_4, router_ip_1_2, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, cost)
        router_lsa_2.add_link_info_v2(router_ip_3, router_ip_2, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, cost)
        router_lsa_3.add_link_info_v2(router_ip_3, router_ip_3, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, cost)
        router_lsa_4.add_link_info_v2(router_ip_4, router_ip_4, conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, cost)

        database_1 = lsdb.Lsdb(conf.VERSION_IPV4, area_1)
        database_2 = lsdb.Lsdb(conf.VERSION_IPV4, area_2)
        for query_lsa in [router_lsa_1_1, router_lsa_2, router_lsa_3, network_lsa_1]:
            database_1.add_lsa(query_lsa, None)
        for query_lsa in [router_lsa_1_2, router_lsa_4, network_lsa_2]:
            database_2.add_lsa(query_lsa, None)
        lsdb_dict = {area_1: database_1, area_2: database_2}

        self.assertTrue(router.Router.is_router_connected(router_id_1, lsdb_dict, conf.VERSION_IPV4))
        self.assertTrue(router.Router.is_router_connected(router_id_2, lsdb_dict, conf.VERSION_IPV4))
        self.assertTrue(router.Router.is_router_connected(router_id_3, lsdb_dict, conf.VERSION_IPV4))
        self.assertTrue(router.Router.is_router_connected(router_id_4, lsdb_dict, conf.VERSION_IPV4))
        self.assertFalse(router.Router.is_router_connected('10.10.10.10', lsdb_dict, conf.VERSION_IPV4))
        lsdb_dict = router.Router.clean_unconnected_routers(copy.deepcopy(lsdb_dict), None, conf.VERSION_IPV4)
        self.assertEqual(4, len(lsdb_dict[area_1].get_lsdb([], None)))
        self.assertEqual(3, len(lsdb_dict[area_2].get_lsdb([], None)))

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
            multiprocessing.Queue(), multiprocessing.Event(), conf.INTERFACE_COSTS))
        router_thread.start()
        time.sleep(0.1)
        test_thread = threading.Thread(target=test_to_run, args=(version, test_passed, r))
        test_thread.start()

        test_thread.join()
        router_thread.join()


if __name__ == '__main__':
    unittest.main()
