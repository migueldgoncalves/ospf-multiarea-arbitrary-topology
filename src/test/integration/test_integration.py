import unittest
import threading
import time

import router.router as router
import conf.conf as conf
import area.area as area
import general.utils as utils

'''
This class tests integration between 2 routers running on localhost
'''


#  Full successful run - Instant
class IntegrationTest(unittest.TestCase):

    def setUp(self):
        self.networks_v2 = []
        self.networks_v3 = []
        router_ids = ['1.1.1.1', '2.2.2.2']
        interfaces = [['ens38'], ['ens39']]
        areas = [[conf.BACKBONE_AREA], [conf.BACKBONE_AREA]]  # One element for each router interface
        self.networks_v2.append(IntegrationTest.create_network(router_ids, interfaces, areas, conf.VERSION_IPV4))
        self.networks_v3.append(IntegrationTest.create_network(router_ids, interfaces, areas, conf.VERSION_IPV6))

    #  Successful run - Instant
    def test_base_integration(self):
        time.sleep(3)
        self.assertEqual(1, len(self.networks_v2))
        self.assertEqual(1, len(self.networks_v3))
        self.assertEqual(4, len(self.networks_v2[0]))
        self.assertEqual(4, len(self.networks_v3[0]))
        self.assertEqual(2, len(self.networks_v2[0][0]))
        self.assertEqual(2, len(self.networks_v3[0][0]))
        self.assertEqual('1.1.1.1', self.networks_v2[0][0][0].router_id)
        self.assertEqual('1.1.1.1', self.networks_v3[0][0][0].router_id)
        self.assertEqual('2.2.2.2', self.networks_v2[0][0][1].router_id)
        self.assertEqual('2.2.2.2', self.networks_v3[0][0][1].router_id)
        self.assertEqual(1, len(self.networks_v2[0][0][0].interfaces))
        self.assertEqual(1, len(self.networks_v3[0][0][0].interfaces))
        self.assertEqual(1, len(self.networks_v2[0][0][1].interfaces))
        self.assertEqual(1, len(self.networks_v3[0][0][1].interfaces))
        ip_address = utils.Utils.get_ipv4_address_from_interface_name('ens38')
        self.assertEqual(ip_address, self.networks_v2[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].ipv4_address)
        ip_address = utils.Utils.get_ipv4_address_from_interface_name('ens39')
        self.assertEqual(ip_address, self.networks_v2[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].ipv4_address)
        ip_address = utils.Utils.get_ipv6_link_local_address_from_interface_name('ens38')
        self.assertEqual(ip_address, self.networks_v3[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].ipv6_address)
        ip_address = utils.Utils.get_ipv6_link_local_address_from_interface_name('ens39')
        self.assertEqual(ip_address, self.networks_v3[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].ipv6_address)
        self.assertEqual(conf.INTERFACE_STATE_WAITING,
                         self.networks_v2[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING,
                         self.networks_v2[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING,
                         self.networks_v3[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING,
                         self.networks_v3[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].state)
        self.assertEqual(1, len(self.networks_v2[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].neighbors))
        self.assertEqual(1, len(self.networks_v2[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].neighbors))
        self.assertEqual(1, len(self.networks_v3[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].neighbors))
        self.assertEqual(1, len(self.networks_v3[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.networks_v2[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT]
                         .neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.networks_v2[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT]
                         .neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.networks_v3[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT]
                         .neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.networks_v3[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT]
                         .neighbors['1.1.1.1'].neighbor_state)

        time.sleep(40)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP,
                         self.networks_v2[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].state)
        self.assertEqual(conf.INTERFACE_STATE_DR,
                         self.networks_v2[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].state)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP,
                         self.networks_v3[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].state)
        self.assertEqual(conf.INTERFACE_STATE_DR,
                         self.networks_v3[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].state)
        self.assertEqual(1, len(self.networks_v2[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].neighbors))
        self.assertEqual(1, len(self.networks_v2[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].neighbors))
        self.assertEqual(1, len(self.networks_v3[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT].neighbors))
        self.assertEqual(1, len(self.networks_v3[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT].neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.networks_v2[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT]
                         .neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.networks_v2[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT]
                         .neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.networks_v3[0][0][0].interfaces['ens38'][area.INTERFACE_OBJECT]
                         .neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.networks_v3[0][0][1].interfaces['ens39'][area.INTERFACE_OBJECT]
                         .neighbors['1.1.1.1'].neighbor_state)

    def tearDown(self):
        for i in range(len(self.networks_v2)):
            IntegrationTest.shutdown_network(self.networks_v2[i])
            IntegrationTest.shutdown_network(self.networks_v3[i])

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
