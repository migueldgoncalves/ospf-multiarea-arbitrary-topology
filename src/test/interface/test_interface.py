import unittest
import threading
import queue
import time

import conf.conf as conf
import general.utils as utils
import general.sock as sock
import interface.interface as interface
import packet.packet as packet
import lsa.lsa as lsa
import neighbor.neighbor as neighbor

'''
This class tests the interface operations in the router
'''

PACKET_BYTES = b'\x02\x01\x00,\x04\x04\x04\x04\x00\x00\x00\x00\xf4\x96\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff' \
               b'\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00'


#  Full successful run - 129-156 s
class InterfaceTest(unittest.TestCase):

    def setUp(self):
        self.interface_identifier = conf.INTERFACE_NAMES[0]
        self.ipv4_address = utils.Utils.get_ipv4_address_from_interface_name(conf.INTERFACE_NAMES[0])
        self.ipv6_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(conf.INTERFACE_NAMES[0])
        self.network_mask = utils.Utils.get_ipv4_network_mask_from_interface_name(conf.INTERFACE_NAMES[0])
        self.link_prefixes = utils.Utils.get_ipv6_prefix_from_interface_name(conf.INTERFACE_NAMES[0])
        self.area_id = conf.INTERFACE_AREAS[0]
        self.interface_pipeline_v2 = queue.Queue()
        self.interface_pipeline_v3 = queue.Queue()
        self.interface_shutdown_v2 = threading.Event()
        self.interface_shutdown_v3 = threading.Event()
        self.interface_ospfv2 = interface.Interface(
            self.interface_identifier, self.ipv4_address, '', self.network_mask, [], self.area_id,
            self.interface_pipeline_v2, self.interface_shutdown_v2, conf.VERSION_IPV4, None)
        self.interface_ospfv3 = interface.Interface(
            self.interface_identifier, '', self.ipv6_address, '', self.link_prefixes, self.area_id,
            self.interface_pipeline_v3, self.interface_shutdown_v3, conf.VERSION_IPV6, None)

    #  #  #  #  #  #
    #  Main methods  #
    #  #  #  #  #  #

    #  Successful run - 21-36 s
    def test_interface_loop_packet_sending_successful(self):
        socket_v2 = sock.Socket()
        socket_v3 = sock.Socket()
        socket_pipeline_v2 = queue.Queue()
        socket_pipeline_v3 = queue.Queue()
        socket_shutdown_v2 = threading.Event()
        socket_shutdown_v3 = threading.Event()
        accept_self_packets = True
        is_dr = False

        #  Creates thread with socket that listens for packets from the router itself
        thread_socket_v2 = threading.Thread(
            target=socket_v2.receive_ipv4,
            args=(socket_pipeline_v2, socket_shutdown_v2, self.interface_identifier, accept_self_packets, is_dr))
        thread_socket_v3 = threading.Thread(
            target=socket_v3.receive_ipv6,
            args=(socket_pipeline_v3, socket_shutdown_v3, self.interface_identifier, accept_self_packets, is_dr))
        thread_socket_v2.start()
        thread_socket_v3.start()

        thread_interface_v2 = threading.Thread(target=self.interface_ospfv2.interface_loop)
        thread_interface_v3 = threading.Thread(target=self.interface_ospfv3.interface_loop)
        thread_interface_v2.start()
        thread_interface_v3.start()
        self.assertEqual(conf.INTERFACE_STATE_DOWN, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DOWN, self.interface_ospfv3.state)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)

        time.sleep(1)  # One Hello packet is sent on interface startup
        self.assertEqual(conf.INTERFACE_STATE_WAITING, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, self.interface_ospfv3.state)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
        self.assertTrue(1, socket_pipeline_v2.qsize())
        self.assertTrue(1, socket_pipeline_v3.qsize())

        time.sleep(4 * conf.HELLO_INTERVAL - 2)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, self.interface_ospfv3.state)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
        self.assertTrue(4, socket_pipeline_v2.qsize())
        self.assertTrue(4, socket_pipeline_v3.qsize())

        time.sleep(1)  # 40 s have passed
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)  # No other router is known
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
        self.assertTrue(5, socket_pipeline_v2.qsize())
        self.assertTrue(5, socket_pipeline_v3.qsize())

        #  Shutdown
        self.interface_shutdown_v2.set()
        self.interface_shutdown_v3.set()
        socket_shutdown_v2.set()
        socket_shutdown_v3.set()
        thread_interface_v2.join()
        thread_interface_v3.join()
        thread_socket_v2.join()
        thread_socket_v3.join()

    #  Successful run - 108-120 s
    #  Tests neighbor state machine for Hello protocol
    def test_interface_loop_incoming_packet_processing_successful(self):
        socket_v2 = sock.Socket()
        socket_v3 = sock.Socket()
        socket_pipeline_v2 = queue.Queue()
        socket_pipeline_v3 = queue.Queue()
        socket_shutdown_v2 = threading.Event()
        socket_shutdown_v3 = threading.Event()
        accept_self_packets = False
        is_dr = False
        one_way_v2 = packet.Packet()  # Bogus packet from router 1.1.1.1 not listing this router as neighbor
        one_way_v3 = packet.Packet()
        one_way_v2.create_header_v2(conf.PACKET_TYPE_HELLO, '1.1.1.1', '0.0.0.0', 0, 0)
        one_way_v3.create_header_v3(
            conf.PACKET_TYPE_HELLO, '1.1.1.1', '0.0.0.0', 0, 'fe80::c001:18ff:fe34:10', 'ff02::5')
        one_way_v2.create_hello_v2_packet_body(
            '255.255.255.0', conf.HELLO_INTERVAL, 12, conf.ROUTER_PRIORITY, conf.ROUTER_DEAD_INTERVAL, '222.222.1.1',
            conf.DEFAULT_DESIGNATED_ROUTER, ())
        one_way_v3.create_hello_v3_packet_body(
            6, conf.HELLO_INTERVAL, 13, conf.ROUTER_PRIORITY, conf.ROUTER_DEAD_INTERVAL, '1.1.1.1',
            conf.DEFAULT_DESIGNATED_ROUTER, ())
        self.assertEqual(0, len(self.interface_ospfv2.neighbors))
        self.assertEqual(0, len(self.interface_ospfv3.neighbors))

        #  Interface receives packet from neighbor not acknowledging this router
        #  Neighbor is created and goes to INIT state
        thread_interface_v2 = threading.Thread(target=self.interface_ospfv2.interface_loop)
        thread_interface_v3 = threading.Thread(target=self.interface_ospfv3.interface_loop)
        thread_interface_v2.start()
        thread_interface_v3.start()
        self.interface_pipeline_v2.put([one_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(10)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # Neighbor is recognized
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        self.interface_pipeline_v2.put([one_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(conf.ROUTER_DEAD_INTERVAL - 5)  # More than 40 s will have passed since original Hello packet
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # New Hello packet resets neighbor timer
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        time.sleep(6)
        self.assertEqual(0, len(self.interface_ospfv2.neighbors))  # Neighbor timer expired
        self.assertEqual(0, len(self.interface_ospfv3.neighbors))
        self.interface_pipeline_v2.put([one_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # Neighbor is recognized again
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        #  Creates thread with socket that listens for packets in the network
        thread_socket_v2 = threading.Thread(
            target=socket_v2.receive_ipv4,
            args=(socket_pipeline_v2, socket_shutdown_v2, self.interface_identifier, accept_self_packets, is_dr))
        thread_socket_v3 = threading.Thread(
            target=socket_v3.receive_ipv6,
            args=(socket_pipeline_v3, socket_shutdown_v3, self.interface_identifier, accept_self_packets, is_dr))
        thread_socket_v2.start()
        thread_socket_v3.start()

        #  Listens for a packet from the neighbor acknowledging this router
        #  Neighbor goes to EXSTART state
        while True:  # OSPFv2
            if not socket_pipeline_v2.empty():
                byte_array = socket_pipeline_v2.get()[0]
                if (packet.Packet.get_ospf_version(byte_array) == conf.VERSION_IPV4) & \
                        (packet.Packet.get_ospf_packet_type(byte_array) == conf.PACKET_TYPE_HELLO):
                    two_way_v2 = packet.Packet.unpack_packet(byte_array)
                    self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
                    break
        while True:  # OSPFv3
            if not socket_pipeline_v3.empty():
                byte_array = socket_pipeline_v3.get()[0]
                if (packet.Packet.get_ospf_version(byte_array) == conf.VERSION_IPV6) & \
                        (packet.Packet.get_ospf_packet_type(byte_array) == conf.PACKET_TYPE_HELLO):
                    two_way_v3 = packet.Packet.unpack_packet(byte_array)
                    self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
                    break
        time.sleep(10)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(conf.ROUTER_DEAD_INTERVAL - 5)  # More than 40 s will have passed since original Hello packet
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # New Hello packet resets neighbor timer
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        time.sleep(6)
        self.assertEqual(0, len(self.interface_ospfv2.neighbors))  # Neighbor timer expired
        self.assertEqual(0, len(self.interface_ospfv3.neighbors))
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # Neighbor is recognized again
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        #  Interface receives another packet from neighbor not acknowledging this router
        #  Neighbor goes to INIT state
        self.interface_pipeline_v2.put([one_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        #  Interface restart
        #  Neighbor goes to DOWN state and is deleted
        self.interface_shutdown_v2.set()
        self.interface_shutdown_v3.set()
        thread_interface_v2.join()
        thread_interface_v3.join()
        self.assertEqual(0, len(self.interface_ospfv2.neighbors))
        self.assertEqual(0, len(self.interface_ospfv3.neighbors))
        thread_interface_v2 = threading.Thread(target=self.interface_ospfv2.interface_loop)
        thread_interface_v3 = threading.Thread(target=self.interface_ospfv3.interface_loop)
        thread_interface_v2.start()
        thread_interface_v3.start()

        #  Interface receives another packet from neighbor acknowledging this router
        #  Neighbor this time jumps to EXSTART state
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        #  Final shutdown
        #  Neighbor goes to DOWN state and is deleted
        self.interface_shutdown_v2.set()
        self.interface_shutdown_v3.set()
        socket_shutdown_v2.set()
        socket_shutdown_v3.set()
        thread_interface_v2.join()
        thread_interface_v3.join()
        thread_socket_v2.join()
        thread_socket_v3.join()

    #  #  #  #  #  #  #  #  #  #  #  #  #
    #  Interface event handling methods  #
    #  #  #  #  #  #  #  #  #  #  #  #  #

    #  Successful run - Instant
    def test_election_algorithm(self):
        neighbor_1 = neighbor.Neighbor('10.10.10.10', conf.ROUTER_PRIORITY, 1, '222.222.1.1', 0,
                                       conf.DEFAULT_DESIGNATED_ROUTER, conf.DEFAULT_DESIGNATED_ROUTER)
        neighbor_2 = neighbor.Neighbor('11.11.11.11', conf.ROUTER_PRIORITY, 2, '222.222.2.1', 0,
                                       conf.DEFAULT_DESIGNATED_ROUTER, conf.DEFAULT_DESIGNATED_ROUTER)
        neighbor_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)

        #  Cold start

        #  This router is non-DR/BDR, no router declares itself as DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_2
        self.interface_ospfv3.neighbors['11.11.11.11'] = neighbor_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('11.11.11.11', self.interface_ospfv2.designated_router)
        self.assertEqual('11.11.11.11', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('11.11.11.11', self.interface_ospfv3.designated_router)
        self.assertEqual('11.11.11.11', self.interface_ospfv3.backup_designated_router)

        self.reset_interface()
        neighbor_2.neighbor_dr = '11.11.11.11'

        #  This router is non-DR/BDR, DR declares itself as DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_2
        self.interface_ospfv3.neighbors['11.11.11.11'] = neighbor_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('11.11.11.11', self.interface_ospfv2.designated_router)
        self.assertEqual('10.10.10.10', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('11.11.11.11', self.interface_ospfv3.designated_router)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.backup_designated_router)

        self.reset_interface()
        neighbor_2.neighbor_dr = conf.DEFAULT_DESIGNATED_ROUTER
        neighbor_2.neighbor_id = '1.1.1.1'

        #  This router is BDR, no router declares itself as DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv2.neighbors['1.1.1.1'] = neighbor_2
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('10.10.10.10', self.interface_ospfv2.designated_router)
        self.assertEqual('10.10.10.10', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.designated_router)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.backup_designated_router)

        self.reset_interface()
        neighbor_1.neighbor_dr = '10.10.10.10'

        #  This router is BDR, DR declares itself as DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv2.neighbors['1.1.1.1'] = neighbor_2
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv2.state)
        self.assertEqual('10.10.10.10', self.interface_ospfv2.designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv3.state)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.backup_designated_router)

        self.reset_interface()
        neighbor_1.neighbor_id = '2.2.2.2'

        #  This router is DR
        self.interface_ospfv2.neighbors['2.2.2.2'] = neighbor_1
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_1
        self.interface_ospfv2.neighbors['1.1.1.1'] = neighbor_2
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv2.designated_router)
        self.assertEqual('2.2.2.2', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual('2.2.2.2', self.interface_ospfv3.backup_designated_router)

        self.reset_interface()

        #  Cold start with different priorities

        neighbor_1.neighbor_priority = 4
        neighbor_1.neighbor_id = '1.1.1.1'
        neighbor_2.neighbor_priority = 2
        neighbor_2.neighbor_id = '2.2.2.2'

        #  This router is non-DR/BDR
        self.interface_ospfv2.neighbors['1.1.1.1'] = neighbor_1
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_1
        self.interface_ospfv2.neighbors['2.2.2.2'] = neighbor_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('1.1.1.1', self.interface_ospfv2.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.backup_designated_router)

        self.reset_interface()
        self.interface_ospfv2.router_priority = 3
        self.interface_ospfv3.router_priority = 3

        #  This router is BDR
        self.interface_ospfv2.neighbors['1.1.1.1'] = neighbor_1
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_1
        self.interface_ospfv2.neighbors['2.2.2.2'] = neighbor_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('1.1.1.1', self.interface_ospfv2.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.backup_designated_router)

        self.reset_interface()
        self.interface_ospfv2.router_priority = 5
        self.interface_ospfv3.router_priority = 5

        #  This router is DR
        self.interface_ospfv2.neighbors['1.1.1.1'] = neighbor_1
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_1
        self.interface_ospfv2.neighbors['2.2.2.2'] = neighbor_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv2.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.backup_designated_router)

        self.reset_interface()
        neighbor_1.neighbor_priority = 0
        neighbor_2.neighbor_priority = 0
        self.interface_ospfv2.router_priority = 1
        self.interface_ospfv3.router_priority = 1

        #  This router is the only eligible to be DR/BDR
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)

        #  TODO: Case where router joins link where DR and BDR are already elected
        #  TODO: Case where there is only one router at the link
        #  TODO: Case where DR fails

        #  Shutdown

        neighbor_1.delete_neighbor()
        neighbor_2.delete_neighbor()

    def reset_interface(self):
        self.interface_ospfv2.state = conf.INTERFACE_STATE_DOWN
        self.interface_ospfv2.neighbors = {}
        self.interface_ospfv2.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv2.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv3.state = conf.INTERFACE_STATE_DOWN
        self.interface_ospfv3.neighbors = {}
        self.interface_ospfv3.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv3.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER

    #  Successful run - Instant
    def test_election_algorithm_step_1(self):
        self.assertEqual(
            [[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv2.designated_router,
              self.interface_ospfv2.backup_designated_router]], self.interface_ospfv2.election_algorithm_step_1())
        self.assertEqual(
            [[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv3.designated_router,
              self.interface_ospfv3.backup_designated_router]], self.interface_ospfv3.election_algorithm_step_1())

        neighbor_1 = neighbor.Neighbor('10.10.10.10', 1, 1, '222.222.1.1', 0, '1.1.1.1', '2.2.2.2')
        neighbor_2 = neighbor.Neighbor('11.11.11.11', 2, 2, '222.222.2.1', 0, '3.3.3.3', '4.4.4.4')

        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_1
        self.assertEqual([[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv2.designated_router,
                           self.interface_ospfv2.backup_designated_router], ['10.10.10.10', 1, '1.1.1.1', '2.2.2.2']],
                         self.interface_ospfv2.election_algorithm_step_1())
        self.assertEqual([[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv3.designated_router,
                           self.interface_ospfv3.backup_designated_router], ['10.10.10.10', 1, '1.1.1.1', '2.2.2.2']],
                         self.interface_ospfv3.election_algorithm_step_1())

        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_2
        self.interface_ospfv3.neighbors['11.11.11.11'] = neighbor_2
        self.assertEqual(
            [[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv2.designated_router,
              self.interface_ospfv2.backup_designated_router], ['10.10.10.10', 1, '1.1.1.1', '2.2.2.2'],
             ['11.11.11.11', 2, '3.3.3.3', '4.4.4.4']], self.interface_ospfv2.election_algorithm_step_1())
        self.assertEqual(
            [[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv3.designated_router,
              self.interface_ospfv3.backup_designated_router], ['10.10.10.10', 1, '1.1.1.1', '2.2.2.2'],
             ['11.11.11.11', 2, '3.3.3.3', '4.4.4.4']], self.interface_ospfv3.election_algorithm_step_1())

        #  Shutdown
        neighbor_1.delete_neighbor()
        neighbor_2.delete_neighbor()

    #  Successful run - Instant
    def test_election_algorithm_step_2(self):
        router_list = [['1.1.1.1', 1, '0.0.0.0', '0.0.0.0']]
        self.assertEqual('1.1.1.1', interface.Interface.election_algorithm_step_2(router_list))
        router_list = [['1.1.1.1', 1, '0.0.0.0', '0.0.0.0'], ['2.2.2.2', 2, '2.2.2.2', '0.0.0.0']]
        self.assertEqual('1.1.1.1', interface.Interface.election_algorithm_step_2(router_list))
        router_list = [['3.3.3.3', 2, '3.3.3.3', '3.3.3.3'], ['1.1.1.1', 1, '0.0.0.0', '0.0.0.0'],
                       ['2.2.2.2', 2, '2.2.2.2', '0.0.0.0']]
        self.assertEqual('1.1.1.1', interface.Interface.election_algorithm_step_2(router_list))
        router_list = [['3.3.3.3', 0, '0.0.0.0', '3.3.3.3'], ['1.1.1.1', 1, '0.0.0.0', '0.0.0.0'],
                       ['2.2.2.2', 2, '2.2.2.2', '0.0.0.0']]
        self.assertEqual('1.1.1.1', interface.Interface.election_algorithm_step_2(router_list))
        router_list = [['3.3.3.3', 2, '3.3.3.3', '0.0.0.0'], ['1.1.1.1', 1, '0.0.0.0', '0.0.0.0'],
                       ['0.0.0.1', 1, '0.0.0.0', '0.0.0.1'], ['2.2.2.2', 2, '2.2.2.2', '0.0.0.0']]
        self.assertEqual('0.0.0.1', interface.Interface.election_algorithm_step_2(router_list))
        router_list = [['3.3.3.3', 2, '3.3.3.3', '0.0.0.0'], ['1.1.1.1', 1, '0.0.0.0', '0.0.0.0'],
                       ['0.0.0.2', 1, '0.0.0.0', '0.0.0.1'], ['0.0.0.1', 2, '0.0.0.0', '0.0.0.1'],
                       ['2.2.2.2', 2, '2.2.2.2', '0.0.0.0']]
        self.assertEqual('0.0.0.1', interface.Interface.election_algorithm_step_2(router_list))
        router_list = [['3.3.3.3', 2, '3.3.3.3', '0.0.0.0'], ['1.1.1.1', 2, '0.0.0.0', '0.0.0.0'],
                       ['0.0.0.2', 1, '0.0.0.0', '1.1.1.1'], ['0.0.0.1', 1, '0.0.0.0', '1.1.1.1'],
                       ['2.2.2.2', 2, '2.2.2.2', '0.0.0.0']]
        self.assertEqual('1.1.1.1', interface.Interface.election_algorithm_step_2(router_list))
        router_list = [['3.3.3.3', 2, '3.3.3.3', '0.0.0.0'], ['1.1.1.1', 2, '1.1.1.1', '0.0.0.0'],
                       ['0.0.0.2', 1, '0.0.0.2', '1.1.1.1'], ['0.0.0.1', 1, '0.0.0.1', '1.1.1.1'],
                       ['2.2.2.2', 2, '2.2.2.2', '0.0.0.0']]
        self.assertEqual('0.0.0.0', interface.Interface.election_algorithm_step_2(router_list))

    #  Successful run - Instant
    def test_election_algorithm_step_3(self):
        router_list = [['1.1.1.1', 1, '0.0.0.0', '0.0.0.0']]
        determined_bdr = '0.0.0.1'
        self.assertEqual(determined_bdr, interface.Interface.election_algorithm_step_3(router_list, determined_bdr))
        router_list = [['1.1.1.1', 1, '1.1.1.1', '0.0.0.0']]
        self.assertEqual('1.1.1.1', interface.Interface.election_algorithm_step_3(router_list, determined_bdr))
        router_list = [['2.2.2.2', 2, '0.0.0.0', '2.2.2.2'], ['1.1.1.1', 1, '1.1.1.1', '0.0.0.0'],
                       ['3.3.3.3', 3, '0.0.0.0', '0.0.0.0']]
        self.assertEqual('1.1.1.1', interface.Interface.election_algorithm_step_3(router_list, determined_bdr))
        router_list = [['2.2.2.2', 2, '0.0.0.0', '2.2.2.2'], ['1.1.1.1', 1, '1.1.1.1', '0.0.0.0'],
                       ['0.0.0.1', 2, '0.0.0.1', '0.0.0.1'], ['3.3.3.3', 3, '0.0.0.0', '0.0.0.0']]
        self.assertEqual('0.0.0.1', interface.Interface.election_algorithm_step_3(router_list, determined_bdr))

    #  Successful run - Instant
    def test_election_algorithm_step_4(self):
        self.interface_ospfv2.designated_router = '0.0.0.0'
        self.interface_ospfv2.backup_designated_router = '0.0.0.0'
        first_run = True
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))
        self.interface_ospfv2.designated_router = '0.0.0.0'
        self.interface_ospfv2.backup_designated_router = conf.ROUTER_ID
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))
        self.interface_ospfv2.designated_router = conf.ROUTER_ID
        self.interface_ospfv2.backup_designated_router = '0.0.0.0'
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))

        first_run = False
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))
        self.interface_ospfv2.designated_router = '0.0.0.0'
        self.interface_ospfv2.backup_designated_router = conf.ROUTER_ID
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))
        self.interface_ospfv2.designated_router = conf.ROUTER_ID
        self.interface_ospfv2.backup_designated_router = '0.0.0.0'
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))

    #  Successful run - Instant
    def test_election_algorithm_step_5(self):
        self.assertTrue(self.interface_ospfv2.state not in [
            conf.INTERFACE_STATE_DROTHER, conf.INTERFACE_STATE_BACKUP, conf.INTERFACE_STATE_DR])
        self.assertTrue(self.interface_ospfv3.state not in [
            conf.INTERFACE_STATE_DROTHER, conf.INTERFACE_STATE_BACKUP, conf.INTERFACE_STATE_DR])

        self.interface_ospfv2.election_algorithm_step_5('0.0.0.0', '0.0.0.0')
        self.interface_ospfv3.election_algorithm_step_5('0.0.0.0', '0.0.0.0')
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.interface_ospfv2.election_algorithm_step_5('0.0.0.0', '0.0.0.0')
        self.interface_ospfv3.election_algorithm_step_5('0.0.0.0', '0.0.0.0')
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)

        self.interface_ospfv2.election_algorithm_step_5('0.0.0.0', conf.ROUTER_ID)
        self.interface_ospfv3.election_algorithm_step_5('0.0.0.0', conf.ROUTER_ID)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv3.state)
        self.interface_ospfv2.election_algorithm_step_5('0.0.0.0', conf.ROUTER_ID)
        self.interface_ospfv3.election_algorithm_step_5('0.0.0.0', conf.ROUTER_ID)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv3.state)

        self.interface_ospfv2.election_algorithm_step_5(conf.ROUTER_ID, '0.0.0.0')
        self.interface_ospfv3.election_algorithm_step_5(conf.ROUTER_ID, '0.0.0.0')
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.interface_ospfv2.election_algorithm_step_5(conf.ROUTER_ID, '0.0.0.0')
        self.interface_ospfv3.election_algorithm_step_5(conf.ROUTER_ID, '0.0.0.0')
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)

    #  Successful run - Instant
    def test_rank_routers(self):
        router_list = [['1.1.1.1', 1]]
        self.assertEqual('1.1.1.1', interface.Interface.rank_routers(router_list))
        router_list = [['4.4.4.4', 1], ['2.2.2.2', 2]]
        self.assertEqual('2.2.2.2', interface.Interface.rank_routers(router_list))
        router_list = [['5.5.5.5', 1], ['6.6.6.6', 1], ['8.8.8.8', 1], ['1.1.1.1', 1]]
        self.assertEqual('8.8.8.8', interface.Interface.rank_routers(router_list))
        router_list = [['2.2.2.2', 1], ['3.3.3.3', 1], ['1.1.1.1', 2], ['4.4.4.4', 1]]
        self.assertEqual('1.1.1.1', interface.Interface.rank_routers(router_list))
        router_list = [['2.2.2.2', 1], ['3.3.3.3', 1], ['1.1.1.1', 2], ['4.4.4.4', 2], ['5.5.5.5', 1]]
        self.assertEqual('4.4.4.4', interface.Interface.rank_routers(router_list))
        router_list = [['2.2.2.2', 1], ['3.3.3.3', 3], ['1.1.1.1', 2], ['4.4.4.4', 2], ['5.5.5.5', 1]]
        self.assertEqual('3.3.3.3', interface.Interface.rank_routers(router_list))

    #  #  #  #  #  #  #  #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #  #

    #  Successful run - Instant
    def test_create_hello_packet_successful(self):
        new_packet = self.interface_ospfv2.create_hello_packet().pack_packet()
        self.assertEqual(PACKET_BYTES, new_packet)

    #  Successful run - Instant
    def test_ospf_identifier_generator(self):
        identifiers_tuple = ()
        self.assertEqual(0, interface.Interface.ospf_identifier_generator(self.interface_identifier, identifiers_tuple))
        identifiers_tuple = (self.interface_identifier,)
        self.assertEqual(1, interface.Interface.ospf_identifier_generator(self.interface_identifier, identifiers_tuple))
        identifiers_tuple = ("An interface",)
        self.assertEqual(0, interface.Interface.ospf_identifier_generator(self.interface_identifier, identifiers_tuple))
        identifiers_tuple = (self.interface_identifier, "Another interface",)
        self.assertEqual(1, interface.Interface.ospf_identifier_generator(self.interface_identifier, identifiers_tuple))
        identifiers_tuple = ("An interface", self.interface_identifier,)
        self.assertEqual(2, interface.Interface.ospf_identifier_generator(self.interface_identifier, identifiers_tuple))
        identifiers_tuple = ("An interface", "Another interface",)
        self.assertEqual(0, interface.Interface.ospf_identifier_generator(self.interface_identifier, identifiers_tuple))
        identifiers_tuple = (self.interface_identifier, self.interface_identifier,)
        self.assertEqual(1, interface.Interface.ospf_identifier_generator(self.interface_identifier, identifiers_tuple))

    #  #  #  #  #  #  #  #  #  #  #  #
    #  Link-local LSA list methods  #
    #  #  #  #  #  #  #  #  #  #  #  #

    #  Successful run - Instant
    def test_link_local_lsa_methods(self):
        lsa_1 = lsa.Lsa()
        lsa_1.create_header(1, 0, 1, '0.0.0.0', '2.2.2.2', 2147483655, conf.VERSION_IPV6)
        lsa_1.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        lsa_1.add_link_info_v3(2, 1, 6, 4, '3.3.3.3')
        lsa_1.add_link_info_v3(2, 10, 5, 5, '2.2.2.2')
        lsa_2 = lsa.Lsa()
        lsa_2.create_header(1, 0, 2, '0.0.0.5', '2.2.2.2', 2147483650, conf.VERSION_IPV6)
        lsa_2.create_network_lsa_body('', 51, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV6)

        self.interface_ospfv3.add_link_local_lsa(lsa_1)
        self.interface_ospfv3.add_link_local_lsa(lsa_2)
        self.assertEqual(2, len(self.interface_ospfv3.link_local_lsa_list))
        self.assertEqual(0x2001, self.interface_ospfv3.link_local_lsa_list[0].header.ls_type)
        self.assertEqual(2147483655, self.interface_ospfv3.link_local_lsa_list[0].header.ls_sequence_number)
        self.assertEqual(0x2002, self.interface_ospfv3.link_local_lsa_list[1].header.ls_type)
        lsa_3 = lsa.Lsa()
        lsa_3.create_header(1, 0, 1, '0.0.0.0', '2.2.2.2', 10000, conf.VERSION_IPV6)
        lsa_3.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        self.interface_ospfv3.add_link_local_lsa(lsa_3)
        self.assertEqual(2, len(self.interface_ospfv3.link_local_lsa_list))
        self.assertEqual(0x2001, self.interface_ospfv3.link_local_lsa_list[1].header.ls_type)
        self.assertEqual(10000, self.interface_ospfv3.link_local_lsa_list[1].header.ls_sequence_number)
        self.assertEqual(0x2002, self.interface_ospfv3.link_local_lsa_list[0].header.ls_type)
        lsa_4 = lsa.Lsa()
        lsa_4.create_header(1, 0, 1, '4.4.4.4', '2.2.2.2', 10000, conf.VERSION_IPV6)
        lsa_4.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        self.interface_ospfv3.add_link_local_lsa(lsa_4)
        self.assertEqual(3, len(self.interface_ospfv3.link_local_lsa_list))
        self.assertEqual('4.4.4.4', self.interface_ospfv3.link_local_lsa_list[2].header.link_state_id)

        retrieved_list = self.interface_ospfv3.get_link_local_lsa_list()
        self.assertEqual(3, len(retrieved_list))
        self.assertEqual(0x2001, retrieved_list[1].header.ls_type)
        self.assertEqual(0x2002, retrieved_list[0].header.ls_type)

        retrieved_lsa = self.interface_ospfv3.get_link_local_lsa(0x2003, '0.0.0.0', '0.0.0.0')
        self.assertIsNone(retrieved_lsa)
        retrieved_lsa = self.interface_ospfv3.get_link_local_lsa(0x2001, '0.0.0.0', '2.2.2.2')
        self.assertEqual(0x2001, retrieved_lsa.header.ls_type)

        self.interface_ospfv3.delete_link_local_lsa(0x2003, '0.0.0.0', '2.2.2.2')
        self.assertEqual(3, len(self.interface_ospfv3.link_local_lsa_list))
        self.interface_ospfv3.delete_link_local_lsa(0x2002, '0.0.0.5', '2.2.2.2')
        self.assertEqual(2, len(self.interface_ospfv3.link_local_lsa_list))
        self.assertEqual(0x2001, self.interface_ospfv3.link_local_lsa_list[0].header.ls_type)
        self.interface_ospfv3.delete_link_local_lsa(0x2002, '0.0.0.5', '2.2.2.2')
        self.assertEqual(2, len(self.interface_ospfv3.link_local_lsa_list))
        self.assertEqual(0x2001, self.interface_ospfv3.link_local_lsa_list[0].header.ls_type)
        self.interface_ospfv3.delete_link_local_lsa(0x2001, '0.0.0.0', '2.2.2.2')
        self.interface_ospfv3.delete_link_local_lsa(0x2001, '4.4.4.4', '2.2.2.2')
        self.assertEqual(0, len(self.interface_ospfv3.link_local_lsa_list))

        self.interface_ospfv3.add_link_local_lsa(lsa_1)
        self.interface_ospfv3.add_link_local_lsa(lsa_2)
        self.interface_ospfv3.clean_link_local_lsa_list()
        self.assertEqual(0, len(self.interface_ospfv3.link_local_lsa_list))
