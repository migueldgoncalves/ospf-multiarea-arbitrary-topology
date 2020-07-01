import unittest
import threading
import time

import router.router as router
import conf.conf as conf
import area.area as area
import general.utils as utils

'''
This class tests integration between 2 router processes running inside the VM
'''


#  Full successful run - 80 s
class IntegrationTest(unittest.TestCase):

    #  Successful run - 80 s
    def test_one_router(self):
        self.one_router(conf.VERSION_IPV4)
        self.one_router(conf.VERSION_IPV6)

    def one_router(self, version):
        router_ids = ['1.1.1.1']
        interfaces = [['ens38']]
        areas = [[conf.BACKBONE_AREA]]
        network = IntegrationTest.create_network(router_ids, interfaces, areas, version)
        router_1 = network[0][0]
        interface_object = router_1.interfaces[interfaces[0][0]][area.INTERFACE_OBJECT]

        self.assertEqual(router_ids[0], router_1.router_id)
        self.assertEqual(1, len(router_1.interfaces))
        if version == conf.VERSION_IPV4:
            ip_address = utils.Utils.get_ipv4_address_from_interface_name(interfaces[0][0])
            self.assertEqual(ip_address, interface_object.ipv4_address)
        else:
            ip_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(interfaces[0][0])
            self.assertEqual(ip_address, interface_object.ipv6_address)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, interface_object.state)
        self.assertEqual(0, len(interface_object.neighbors))

        time.sleep(40)
        self.assertEqual(conf.INTERFACE_STATE_DR, interface_object.state)
        if version == conf.VERSION_IPV4:
            self.assertEqual(ip_address, interface_object.designated_router)
        else:
            self.assertEqual(router_ids[0], interface_object.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, interface_object.backup_designated_router)
        self.assertEqual(0, len(interface_object.neighbors))

        self.shutdown_network(network)

    #  Successful run - ?
    def test_base_integration(self):
        self.base_integration(conf.VERSION_IPV4)
        self.base_integration(conf.VERSION_IPV6)

    def base_integration(self, version):
        router_ids = ['1.1.1.1', '2.2.2.2']
        interfaces = [['ens38'], ['ens39']]
        areas = [[conf.BACKBONE_AREA], [conf.BACKBONE_AREA]]  # One element for each router interface
        network = IntegrationTest.create_network(router_ids, interfaces, areas, version)
        routers = network[0]
        router_1 = routers[0]
        router_2 = routers[1]
        interface_object_1 = router_1.interfaces[interfaces[0][0]][area.INTERFACE_OBJECT]
        interface_object_2 = router_2.interfaces[interfaces[1][0]][area.INTERFACE_OBJECT]

        time.sleep(12)
        self.assertEqual(4, len(network))
        self.assertEqual(2, len(routers))
        self.assertEqual('1.1.1.1', router_1.router_id)
        self.assertEqual('2.2.2.2', router_2.router_id)
        self.assertEqual(1, len(router_1.interfaces))
        self.assertEqual(1, len(router_2.interfaces))
        if version == conf.VERSION_IPV4:
            ip_address_1 = utils.Utils.get_ipv4_address_from_interface_name('ens38')
            ip_address_2 = utils.Utils.get_ipv4_address_from_interface_name('ens39')
            self.assertEqual(ip_address_1, interface_object_1.ipv4_address)
            self.assertEqual(ip_address_2, interface_object_2.ipv4_address)
        else:
            ip_address_1 = utils.Utils.get_ipv6_link_local_address_from_interface_name('ens38')
            ip_address_2 = utils.Utils.get_ipv6_link_local_address_from_interface_name('ens39')
            self.assertEqual(ip_address_1, interface_object_1.ipv6_address)
            self.assertEqual(ip_address_2, interface_object_2.ipv6_address)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, interface_object_1.state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, interface_object_2.state)
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
            routers.append(router.Router(router_id, version, router_shutdown, router_interfaces, router_areas, True))
            threads.append(threading.Thread(target=routers[i].main_loop))
            threads[i].start()

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

    #  Virtual hub to connect every router in the test network
    class Hub:
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
                        for j in self.entry_pipelines:
                            if j != i:  # Interface is not the sending one
                                self.entry_pipelines[j].put(data_array)
