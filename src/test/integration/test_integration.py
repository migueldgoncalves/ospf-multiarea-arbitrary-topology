import unittest
import threading
import time
import copy
import multiprocessing
import os
from datetime import datetime

import router.router as router
import conf.conf as conf
import area.area as area
import general.utils as utils
import packet.packet as packet

'''
This class tests integration between 2 router processes running inside the same machine
'''

#  More interfaces and routers can be added as required
INTERFACES_R1 = [['veth1_1', '111.111.1.1/24', '1001:db8:cafe:1::1/64', 'fe80:1::1/64', conf.BACKBONE_AREA]]
INTERFACES_R2 = [['veth2_1', '111.111.1.2/24', '1001:db8:cafe:1::2/64', 'fe80:2::1/64', conf.BACKBONE_AREA]]
INTERFACE_LIST = [INTERFACES_R1, INTERFACES_R2]  # Add new routers here


#  Full successful run - 226 s
class IntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        for interfaces in INTERFACE_LIST:
            for interface_data in interfaces:
                interface = interface_data[0]
                ipv4_address = interface_data[1]
                ipv6_global_address = interface_data[2]
                ipv6_link_local_address = interface_data[3]
                os.system("ip link add " + interface + " type veth")
                os.system("ip link set " + interface + " up")
                os.system("ip addr add " + ipv4_address + " dev " + interface)
                os.system("ip addr add " + ipv6_global_address + " dev " + interface)
                os.system("ip addr add " + ipv6_link_local_address + " dev " + interface)

    #  Successful run - 100 s
    def test_one_router(self):
        self.one_router(conf.VERSION_IPV4)
        self.one_router(conf.VERSION_IPV6)

    def one_router(self, version):
        router_ids = ['1.1.1.1']
        interfaces = [[INTERFACES_R1[0][0]]]
        areas = [[INTERFACES_R1[0][4]]]
        network = IntegrationTest.create_network(router_ids, interfaces, areas, version)
        router_1 = network[0][0]
        interface_object = router_1.interfaces[interfaces[0][0]][area.INTERFACE_OBJECT]

        time.sleep(0.1)
        self.assertEqual(router_ids[0], router_1.router_id)
        self.assertEqual(1, len(router_1.interfaces))
        if version == conf.VERSION_IPV4:
            ip_address = utils.Utils.interface_name_to_ipv4_address(interfaces[0][0])
            self.assertEqual(ip_address, interface_object.ipv4_address)
        elif version == conf.VERSION_IPV6:
            ip_address = utils.Utils.interface_name_to_ipv6_link_local_address(interfaces[0][0])
            self.assertEqual(ip_address, interface_object.ipv6_address)
        else:
            raise ValueError("Invalid OSPF version")
        self.assertEqual(conf.INTERFACE_STATE_WAITING, interface_object.state)
        self.assertEqual(0, len(interface_object.neighbors))
        if version == conf.VERSION_IPV4:
            self.assertTrue(1, len(interface_object.lsdb.get_lsdb([interface_object], None)))
            router_lsa = interface_object.lsdb.get_lsa(
                conf.LSA_TYPE_ROUTER, router_ids[0], router_ids[0], [interface_object])
            self.assertIsNotNone(router_lsa)
            self.assertEqual(1, router_lsa.body.link_number)
            self.assertEqual(1, len(router_lsa.body.links))
            self.assertEqual(
                [utils.Utils.interface_name_to_ipv4_prefix_and_length(interfaces[0][0])[0],
                 utils.Utils.interface_name_to_ipv4_network_mask(interfaces[0][0]),
                 conf.LINK_TO_STUB_NETWORK, conf.DEFAULT_TOS, interface_object.cost], router_lsa.body.links[0])
        else:
            self.assertTrue(3, len(interface_object.lsdb.get_lsdb([interface_object], None)))
            router_lsa = interface_object.lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, router_ids[0], [interface_object])
            self.assertIsNotNone(router_lsa)
            self.assertEqual(conf.OPTIONS_V3, router_lsa.body.options)
            self.assertEqual(0, len(router_lsa.body.links))
        self.assertFalse(router_lsa.body.bit_v)
        self.assertFalse(router_lsa.body.bit_e)
        self.assertFalse(router_lsa.body.bit_b)
        self.assertEqual(version, router_lsa.body.version)
        if version == conf.VERSION_IPV6:
            link_lsa = interface_object.lsdb.get_lsa(
                conf.LSA_TYPE_LINK, interface_object.ospf_identifier, router_ids[0], [interface_object])
            self.assertIsNotNone(link_lsa)
            self.assertEqual(conf.ROUTER_PRIORITY, link_lsa.body.router_priority)
            self.assertEqual(conf.OPTIONS_V3, link_lsa.body.options)
            self.assertEqual(interface_object.ipv6_address, link_lsa.body.link_local_address)
            self.assertEqual(1, link_lsa.body.prefix_number)
            self.assertEqual(1, len(link_lsa.body.prefixes))
            prefix_data = utils.Utils.interface_name_to_ipv6_prefix_and_length(interfaces[0][0])
            self.assertEqual([prefix_data[1], conf.PREFIX_OPTIONS, prefix_data[0]], link_lsa.body.prefixes[0])
            intra_area_prefix_lsa = interface_object.lsdb.get_lsa(
                conf.LSA_TYPE_INTRA_AREA_PREFIX, 0, router_ids[0], [interface_object])
            self.assertIsNotNone(intra_area_prefix_lsa)
            self.assertEqual(1, intra_area_prefix_lsa.body.prefix_number)
            self.assertEqual(0x2001, intra_area_prefix_lsa.body.referenced_ls_type)
            self.assertEqual('0.0.0.0', intra_area_prefix_lsa.body.referenced_link_state_id)
            self.assertEqual(router_ids[0], intra_area_prefix_lsa.body.referenced_advertising_router)
            self.assertEqual(1, len(intra_area_prefix_lsa.body.prefixes))
            self.assertEqual([prefix_data[1], conf.PREFIX_OPTIONS, interface_object.cost, prefix_data[0]],
                             intra_area_prefix_lsa.body.prefixes[0])

        time.sleep(50)
        self.assertEqual(conf.INTERFACE_STATE_DR, interface_object.state)
        if version == conf.VERSION_IPV4:
            self.assertEqual(ip_address, interface_object.designated_router)
        else:
            self.assertEqual(router_ids[0], interface_object.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, interface_object.backup_designated_router)
        self.assertEqual(0, len(interface_object.neighbors))
        if version == conf.VERSION_IPV4:
            self.assertEqual(1, len(interface_object.lsdb.get_lsdb([interface_object], None)))
            router_lsa = interface_object.lsdb.get_lsa(
                conf.LSA_TYPE_ROUTER, router_ids[0], router_ids[0], [interface_object])
            self.assertEqual(1, len(router_lsa.body.links))
        else:
            self.assertEqual(3, len(interface_object.lsdb.get_lsdb([interface_object], None)))
            router_lsa = interface_object.lsdb.get_lsa(conf.LSA_TYPE_ROUTER, 0, router_ids[0], [interface_object])
            self.assertEqual(0, len(router_lsa.body.links))
            link_lsa = interface_object.lsdb.get_lsa(
                conf.LSA_TYPE_LINK, interface_object.ospf_identifier, router_ids[0], [interface_object])
            self.assertEqual(1, len(link_lsa.body.prefixes))
            intra_area_prefix_lsa = interface_object.lsdb.get_lsa(
                conf.LSA_TYPE_INTRA_AREA_PREFIX, 0, router_ids[0], [interface_object])
            self.assertEqual(1, len(intra_area_prefix_lsa.body.prefixes))

        self.shutdown_network(network)

    #  Successful run - 126 s
    def test_two_routers(self):
        self.two_routers(conf.VERSION_IPV4)
        self.two_routers(conf.VERSION_IPV6)

    def two_routers(self, version):
        router_ids = ['1.1.1.1', '2.2.2.2']
        interfaces = [[INTERFACES_R1[0][0]], [INTERFACES_R2[0][0]]]
        areas = [[INTERFACES_R1[0][4]], [INTERFACES_R2[0][4]]]  # One element for each router interface
        network = IntegrationTest.create_network(router_ids, interfaces, areas, version)
        routers = network[0]
        router_1 = routers[0]
        router_2 = routers[1]
        interface_object_1 = router_1.interfaces[interfaces[0][0]][area.INTERFACE_OBJECT]
        interface_object_2 = router_2.interfaces[interfaces[1][0]][area.INTERFACE_OBJECT]
        interface_array = [interface_object_1, interface_object_2]

        time.sleep(0.1)
        self.assertEqual(4, len(network))
        self.assertEqual(2, len(routers))
        self.assertEqual('1.1.1.1', router_1.router_id)
        self.assertEqual('2.2.2.2', router_2.router_id)
        self.assertEqual(1, len(router_1.interfaces))
        self.assertEqual(1, len(router_2.interfaces))
        if version == conf.VERSION_IPV4:
            ip_address_1 = utils.Utils.interface_name_to_ipv4_address(INTERFACES_R1[0][0])
            ip_address_2 = utils.Utils.interface_name_to_ipv4_address(INTERFACES_R2[0][0])
            self.assertEqual(ip_address_1, interface_object_1.ipv4_address)
            self.assertEqual(ip_address_2, interface_object_2.ipv4_address)
            self.assertEqual(1, len(interface_object_1.lsdb.get_lsdb([interface_object_1], None)))
            self.assertEqual(1, len(interface_object_2.lsdb.get_lsdb([interface_object_2], None)))
        elif version == conf.VERSION_IPV6:
            ip_address_1 = utils.Utils.interface_name_to_ipv6_link_local_address(INTERFACES_R1[0][0])
            ip_address_2 = utils.Utils.interface_name_to_ipv6_link_local_address(INTERFACES_R2[0][0])
            self.assertEqual(ip_address_1, interface_object_1.ipv6_address)
            self.assertEqual(ip_address_2, interface_object_2.ipv6_address)
            self.assertEqual(3, len(interface_object_1.lsdb.get_lsdb([interface_object_1], None)))
            self.assertEqual(3, len(interface_object_2.lsdb.get_lsdb([interface_object_2], None)))
        else:
            raise ValueError("Invalid OSPF version")
        self.assertEqual(conf.INTERFACE_STATE_WAITING, interface_object_1.state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, interface_object_2.state)

        time.sleep(12)
        self.assertEqual(1, len(interface_object_1.neighbors))
        self.assertEqual(1, len(interface_object_2.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, interface_object_1.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, interface_object_2.neighbors['1.1.1.1'].neighbor_state)

        time.sleep(50)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, interface_object_1.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, interface_object_2.state)
        self.assertEqual(1, len(interface_object_1.neighbors))
        self.assertEqual(1, len(interface_object_2.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, interface_object_1.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, interface_object_2.neighbors['1.1.1.1'].neighbor_state)
        for interface_obj in interface_array:
            if version == conf.VERSION_IPV4:
                self.assertEqual(3, len(interface_obj.lsdb.get_lsdb([interface_obj], None)))
                self.assertEqual(2, len(interface_obj.lsdb.router_lsa_list))
                self.assertEqual(1, len(interface_obj.lsdb.network_lsa_list))
            else:
                self.assertEqual(6, len(interface_obj.lsdb.get_lsdb([interface_obj], None)))
                self.assertEqual(2, len(interface_obj.lsdb.router_lsa_list))
                self.assertEqual(1, len(interface_obj.lsdb.network_lsa_list))
                self.assertEqual(1, len(interface_obj.lsdb.intra_area_prefix_lsa_list))
                self.assertEqual(2, len(interface_obj.link_local_lsa_list))
                remaining_router_ids = copy.deepcopy(router_ids)
                for link_lsa in interface_obj.link_local_lsa_list:
                    for interface_obj_2 in interface_array:
                        if link_lsa.header.advertising_router == interface_obj_2.router_id:
                            link_local_address = utils.Utils.interface_name_to_ipv6_link_local_address(
                                interface_obj_2.physical_identifier)
                            self.assertEqual(link_local_address, link_lsa.body.link_local_address)
                            self.assertEqual(1, link_lsa.body.prefix_number)
                            self.assertEqual(1, len(link_lsa.body.prefixes))
                            prefix_data = utils.Utils.interface_name_to_ipv6_prefix_and_length(
                                interface_obj_2.physical_identifier)
                            self.assertEqual([prefix_data[1], conf.PREFIX_OPTIONS, prefix_data[0]],
                                             link_lsa.body.prefixes[0])
                            remaining_router_ids.remove(interface_obj_2.router_id)
                if len(remaining_router_ids) > 0:
                    self.fail("Router does not have all Link-LSAs in the network")
                intra_area_prefix_lsa = interface_obj.lsdb.intra_area_prefix_lsa_list[0]
                self.assertEqual(interface_object_2.router_id, intra_area_prefix_lsa.header.advertising_router)
                self.assertEqual(1, intra_area_prefix_lsa.body.prefix_number)
                self.assertEqual(1, len(intra_area_prefix_lsa.body.prefixes))
                prefix_data = utils.Utils.interface_name_to_ipv6_prefix_and_length(interface_obj.physical_identifier)
                self.assertEqual([prefix_data[1], conf.PREFIX_OPTIONS, conf.INTERFACE_COST, prefix_data[0]],
                                 intra_area_prefix_lsa.body.prefixes[0])
            remaining_router_ids = copy.deepcopy(router_ids)
            for router_lsa in interface_obj.lsdb.router_lsa_list:
                for interface_obj_2 in interface_array:
                    if router_lsa.header.advertising_router == interface_obj_2.router_id:
                        self.assertEqual(1, len(router_lsa.body.links))
                        if version == conf.VERSION_IPV4:
                            self.assertEqual([interface_object_2.ipv4_address, interface_obj_2.ipv4_address,
                                              conf.LINK_TO_TRANSIT_NETWORK, conf.DEFAULT_TOS, conf.INTERFACE_COST],
                                             router_lsa.body.links[0])
                        else:
                            self.assertEqual([conf.LINK_TO_TRANSIT_NETWORK, conf.INTERFACE_COST,
                                              interface_obj_2.ospf_identifier, interface_object_2.ospf_identifier,
                                              interface_object_2.router_id], router_lsa.body.links[0])
                        remaining_router_ids.remove(interface_obj_2.router_id)
            if len(remaining_router_ids) > 0:
                self.fail("Router does not have all Router-LSAs in the network")
            network_lsa = interface_obj.lsdb.network_lsa_list[0]
            self.assertEqual(interface_object_2.router_id, network_lsa.header.advertising_router)
            self.assertTrue(all(item in network_lsa.body.attached_routers for item in router_ids))

        self.shutdown_network(network)

    #  #  #  #  #  #  #  #  #  #  #  #
    #  Auxiliary methods and classes  #
    #  #  #  #  #  #  #  #  #  #  #  #

    #  Creates a virtual network
    @staticmethod
    def create_network(router_ids, interfaces, areas, version):
        routers = []
        threads = []
        for i in range(len(router_ids)):
            router_id = router_ids[i]
            router_interfaces = interfaces[i]
            router_areas = areas[i]
            router_shutdown = threading.Event()
            routers.append(router.Router())
            threads.append(threading.Thread(target=routers[i].set_up, args=(
                router_id, version, router_shutdown, router_interfaces, router_areas, True, multiprocessing.Queue(),
                multiprocessing.Event())))
            threads[i].start()
            time.sleep(0.5)  # Gives CPU to router thread

        entry_pipelines = {}
        exit_pipelines = {}
        for r in routers:
            for i in r.packet_pipelines:
                entry_pipelines[i] = r.packet_pipelines[i]
            for i in r.interfaces:
                if version == conf.VERSION_IPV4:  # OSPFv2
                    exit_pipelines[i] = r.interfaces[i][area.INTERFACE_OBJECT].socket.exit_pipeline_v2
                else:  # OSPFv3
                    exit_pipelines[i] = r.interfaces[i][area.INTERFACE_OBJECT].socket.exit_pipeline_v3

        shutdown_event = threading.Event()
        hub = IntegrationTest.Hub(shutdown_event, entry_pipelines, exit_pipelines)
        hub_thread = threading.Thread(target=hub.main_loop)
        hub_thread.start()
        return [routers, threads, hub, hub_thread]

    #  Performs shutdown of provided virtual network
    @staticmethod
    def shutdown_network(network):
        routers = network[0]
        threads = network[1]
        hub = network[2]
        hub_thread = network[3]

        for i in range(len(routers)):
            routers[i].router_shutdown_event.set()
            threads[i].join()
        hub.shutdown_event.set()
        hub_thread.join()

    @staticmethod
    def shutdown_networks(networks):
        for i in range(len(networks)):
            IntegrationTest.shutdown_network(networks[i])

    @classmethod
    def tearDownClass(cls):
        for interfaces in INTERFACE_LIST:
            for interface_data in interfaces:
                interface = interface_data[0]
                os.system("ip addr flush " + interface)
                os.system("ip link set " + interface + " down")
                os.system("ip link delete " + interface)

    #  Virtual hub to connect every router in the test network
    class Hub:
        packet_log = True  # Set to True if printing of packets content is desired

        def __init__(self, shutdown_event, entry_pipelines, exit_pipelines):
            self.shutdown_event = shutdown_event
            self.entry_pipelines = entry_pipelines
            self.exit_pipelines = exit_pipelines

        def main_loop(self):
            while not self.shutdown_event.is_set():
                for i in self.exit_pipelines:
                    pipeline = self.exit_pipelines[i]
                    if not pipeline.empty():
                        data_array = pipeline.get().copy()
                        if self.packet_log:
                            print(datetime.now().time(), "Source:", data_array[1], "Destination:", data_array[2],
                                  packet.Packet.unpack_packet(data_array[0]))
                        for j in self.entry_pipelines:
                            if j != i:  # Interface is not the sending one
                                self.entry_pipelines[j].put(data_array)


if __name__ == '__main__':
    unittest.main()
