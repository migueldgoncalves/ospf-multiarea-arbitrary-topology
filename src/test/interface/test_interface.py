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
import area.area as area

'''
This class tests the interface operations in the router
'''

PACKET_BYTES = b'\x02\x01\x00,\x04\x04\x04\x04\x00\x00\x00\x00\xb4\x96\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff' \
               b'\xff\xff\x00\x00\nB\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00'


#  Full successful run - 180-220 s
class InterfaceTest(unittest.TestCase):

    def setUp(self):
        self.interface_identifier = conf.INTERFACE_NAMES[0]
        self.ipv4_address = utils.Utils.interface_name_to_ipv4_address(conf.INTERFACE_NAMES[0])
        self.ipv6_address = utils.Utils.interface_name_to_ipv6_link_local_address(conf.INTERFACE_NAMES[0])
        self.network_mask = utils.Utils.interface_name_to_ipv4_network_mask(conf.INTERFACE_NAMES[0])
        self.link_prefixes = utils.Utils.interface_name_to_ipv6_prefix_and_length(conf.INTERFACE_NAMES[0])
        self.area_id = conf.INTERFACE_AREAS[0]
        self.interface_pipeline_v2 = queue.Queue()
        self.interface_pipeline_v3 = queue.Queue()
        self.interface_shutdown_v2 = threading.Event()
        self.interface_shutdown_v3 = threading.Event()
        self.lsdb_v2 = area.Area.lsdb_startup(
            conf.ROUTER_ID, conf.VERSION_IPV4, conf.BACKBONE_AREA, False, [self.interface_identifier])
        self.lsdb_v3 = area.Area.lsdb_startup(
            conf.ROUTER_ID, conf.VERSION_IPV6, conf.BACKBONE_AREA, False, [self.interface_identifier])
        self.interface_ospfv2 = interface.Interface(
            conf.ROUTER_ID, self.interface_identifier, self.ipv4_address, '', self.network_mask, [], self.area_id,
            self.interface_pipeline_v2, self.interface_shutdown_v2, conf.VERSION_IPV4, self.lsdb_v2, False, False)
        self.interface_ospfv3 = interface.Interface(
            conf.ROUTER_ID, self.interface_identifier, '', self.ipv6_address, '', self.link_prefixes, self.area_id,
            self.interface_pipeline_v3, self.interface_shutdown_v3, conf.VERSION_IPV6, self.lsdb_v3, False, False)

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
        is_dr = threading.Event()

        #  Creates thread with socket that listens for packets from the router itself
        thread_socket_v2 = threading.Thread(
            target=socket_v2.receive_ipv4,
            args=(socket_pipeline_v2, socket_shutdown_v2, self.interface_identifier, accept_self_packets, is_dr, False))
        thread_socket_v3 = threading.Thread(
            target=socket_v3.receive_ipv6,
            args=(socket_pipeline_v3, socket_shutdown_v3, self.interface_identifier, accept_self_packets, is_dr, False,
                  ''))
        thread_socket_v2.start()
        thread_socket_v3.start()

        thread_interface_v2 = threading.Thread(target=self.interface_ospfv2.interface_loop)
        thread_interface_v3 = threading.Thread(target=self.interface_ospfv3.interface_loop)
        thread_interface_v2.start()
        thread_interface_v3.start()
        #  Interfaces might have time to reach Waiting state
        self.assertTrue(self.interface_ospfv2.state in [conf.INTERFACE_STATE_DOWN, conf.INTERFACE_STATE_WAITING])
        self.assertTrue(self.interface_ospfv3.state in [conf.INTERFACE_STATE_DOWN, conf.INTERFACE_STATE_WAITING])
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

        time.sleep(2)  # 40 s have passed
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)  # No other router is known
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        #  In OSPFv2 DR/BDR is identified by interface IP address
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
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

    #  Successful run - 152-164 s
    #  Tests neighbor state machine for Hello protocol
    def test_interface_loop_incoming_packet_processing_successful(self):
        socket_v2 = sock.Socket()
        socket_v3 = sock.Socket()
        socket_pipeline_v2 = queue.Queue()
        socket_pipeline_v3 = queue.Queue()
        socket_shutdown_v2 = threading.Event()
        socket_shutdown_v3 = threading.Event()
        accept_self_packets = False
        is_dr = threading.Event()
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
        #  Interfaces might have time to reach Waiting state
        self.assertTrue(self.interface_ospfv2.state in [conf.INTERFACE_STATE_DOWN, conf.INTERFACE_STATE_WAITING])
        self.assertTrue(self.interface_ospfv3.state in [conf.INTERFACE_STATE_DOWN, conf.INTERFACE_STATE_WAITING])
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)

        #  Interface receives packet from neighbor not acknowledging this router
        #  Neighbor is created and goes to INIT state
        thread_interface_v2 = threading.Thread(target=self.interface_ospfv2.interface_loop)
        thread_interface_v3 = threading.Thread(target=self.interface_ospfv3.interface_loop)
        thread_interface_v2.start()
        thread_interface_v3.start()
        self.interface_pipeline_v2.put([one_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(10)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, self.interface_ospfv3.state)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # Neighbor is recognized
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        self.interface_pipeline_v2.put([one_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(conf.ROUTER_DEAD_INTERVAL - 5)  # More than 40 s will have passed since original Hello packet
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
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
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)

        #  Creates thread with socket that listens for packets in the network
        thread_socket_v2 = threading.Thread(
            target=socket_v2.receive_ipv4,
            args=(socket_pipeline_v2, socket_shutdown_v2, self.interface_identifier, accept_self_packets, is_dr, False))
        thread_socket_v3 = threading.Thread(
            target=socket_v3.receive_ipv6,
            args=(socket_pipeline_v3, socket_shutdown_v3, self.interface_identifier, accept_self_packets, is_dr, False,
                  ''))
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
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
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
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # Neighbor is recognized again
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)

        #  Interface receives another packet from neighbor not acknowledging this router
        #  Neighbor goes to INIT state
        self.interface_pipeline_v2.put([one_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)

        #  Interface restart
        #  Neighbor goes to DOWN state and is deleted
        self.interface_shutdown_v2.set()
        self.interface_shutdown_v3.set()
        thread_interface_v2.join()
        thread_interface_v3.join()
        self.assertEqual(0, len(self.interface_ospfv2.neighbors))
        self.assertEqual(0, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.INTERFACE_STATE_DOWN, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DOWN, self.interface_ospfv3.state)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
        thread_interface_v2 = threading.Thread(target=self.interface_ospfv2.interface_loop)
        thread_interface_v3 = threading.Thread(target=self.interface_ospfv3.interface_loop)
        thread_interface_v2.start()
        thread_interface_v3.start()

        #  Interface receives another packet from neighbor acknowledging this router
        #  Neighbor this time jumps to EXSTART state after moving to 2_WAY
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(10)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_WAITING, self.interface_ospfv3.state)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)

        #  Interface runs again election algorithm after 40 s - Neighbor declares itself as BDR in provided packet
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(conf.ROUTER_DEAD_INTERVAL - 5)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)  # Considers neighbor as DR and BDR
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('222.222.1.1', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.1.1', self.interface_ospfv2.backup_designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.backup_designated_router)

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

    #  Successful run - 8-10 s
    def test_election_algorithm(self):
        neighbor_v2_1 = neighbor.Neighbor(
            '10.10.10.10', conf.ROUTER_PRIORITY, 1, '222.222.1.10', 0, conf.DEFAULT_DESIGNATED_ROUTER,
            conf.DEFAULT_DESIGNATED_ROUTER, conf.ROUTER_ID)
        neighbor_v2_2 = neighbor.Neighbor(
            '11.11.11.11', conf.ROUTER_PRIORITY, 2, '222.222.1.11', 0, conf.DEFAULT_DESIGNATED_ROUTER,
            conf.DEFAULT_DESIGNATED_ROUTER, conf.ROUTER_ID)
        neighbor_v3_1 = neighbor.Neighbor(
            '10.10.10.10', conf.ROUTER_PRIORITY, 1, '2001:db8:cafe:1::10', 0, conf.DEFAULT_DESIGNATED_ROUTER,
            conf.DEFAULT_DESIGNATED_ROUTER, conf.ROUTER_ID)
        neighbor_v3_2 = neighbor.Neighbor(
            '11.11.11.11', conf.ROUTER_PRIORITY, 2, '2001:db8:cafe:1::11', 0, conf.DEFAULT_DESIGNATED_ROUTER,
            conf.DEFAULT_DESIGNATED_ROUTER, conf.ROUTER_ID)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        self.reset_interface(conf.INTERFACE_STATE_WAITING)

        #  Cold start

        #  This router will be non-DR/BDR, no router declares itself as DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['11.11.11.11'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('222.222.1.11', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.1.11', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('11.11.11.11', self.interface_ospfv3.designated_router)
        self.assertEqual('11.11.11.11', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['11.11.11.11'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.neighbor_dr = '222.222.1.11'
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.neighbor_dr = '11.11.11.11'

        #  This router will be non-DR/BDR, DR declares itself as DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['11.11.11.11'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('222.222.1.11', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.1.10', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('11.11.11.11', self.interface_ospfv3.designated_router)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['11.11.11.11'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.neighbor_dr = conf.DEFAULT_DESIGNATED_ROUTER
        neighbor_v2_2.neighbor_ip_address = '222.222.0.1'
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.neighbor_dr = conf.DEFAULT_DESIGNATED_ROUTER
        neighbor_v3_2.neighbor_id = '1.1.1.1'

        #  This router will be BDR, no router declares itself as DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('222.222.1.10', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.1.10', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.designated_router)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_1.neighbor_dr = '222.222.1.10'
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.neighbor_dr = '10.10.10.10'

        #  This router will be BDR, DR declares itself as DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv2.state)
        self.assertEqual('222.222.1.10', self.interface_ospfv2.designated_router)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv3.state)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.designated_router)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_1.neighbor_ip_address = '222.222.0.2'
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.neighbor_id = '2.2.2.2'

        #  This router will be DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.0.2', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual('2.2.2.2', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)

        #  Cold start with different priorities

        neighbor_v2_1.neighbor_priority = 4
        neighbor_v2_1.neighbor_ip_address = '222.222.0.1'
        neighbor_v2_2.neighbor_priority = 2
        neighbor_v2_2.neighbor_ip_address = '222.222.0.2'
        neighbor_v3_1.neighbor_priority = 4
        neighbor_v3_1.neighbor_id = '1.1.1.1'
        neighbor_v3_2.neighbor_priority = 2
        neighbor_v3_2.neighbor_id = '2.2.2.2'

        #  This router will be non-DR/BDR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('222.222.0.1', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.0.1', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        self.interface_ospfv2.router_priority = 3
        self.interface_ospfv3.router_priority = 3

        #  This router will be BDR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('222.222.0.1', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.0.1', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        self.interface_ospfv2.router_priority = 5
        self.interface_ospfv3.router_priority = 5

        #  This router will be DR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.0.1', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_1.neighbor_priority = 0
        neighbor_v2_2.neighbor_priority = 0
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.neighbor_priority = 0
        neighbor_v3_2.neighbor_priority = 0
        self.interface_ospfv2.router_priority = 1
        self.interface_ospfv3.router_priority = 1

        #  This router is the only eligible to be DR/BDR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['11.11.11.11'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.delete_neighbor()
        neighbor_v2_2.delete_neighbor()
        neighbor_v3_1.delete_neighbor()
        neighbor_v3_2.delete_neighbor()

        #  Router joins link where DR and BDR are elected

        neighbor_v2_1 = neighbor.Neighbor('1.1.1.1', conf.ROUTER_PRIORITY, 1, '222.222.0.1', 0, '222.222.0.1',
                                          '222.222.0.2', conf.ROUTER_ID)
        neighbor_v2_2 = neighbor.Neighbor('2.2.2.2', conf.ROUTER_PRIORITY, 2, '222.222.0.2', 0, '222.222.0.1',
                                          '222.222.0.2', conf.ROUTER_ID)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1 = neighbor.Neighbor(
            '1.1.1.1', conf.ROUTER_PRIORITY, 1, '2001:db8:cafe:1::1', 0, '1.1.1.1', '2.2.2.2', conf.ROUTER_ID)
        neighbor_v3_2 = neighbor.Neighbor(
            '2.2.2.2', conf.ROUTER_PRIORITY, 2, '2001:db8:cafe:1::2', 0, '1.1.1.1', '2.2.2.2', conf.ROUTER_ID)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)

        self.interface_ospfv2.neighbors['1.1.1.1'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['1.1.1.1'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['2.2.2.2'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_v3_2
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('222.222.0.1', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.0.2', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('1.1.1.1', self.interface_ospfv3.designated_router)
        self.assertEqual('2.2.2.2', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_EXSTART, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_WAITING)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)

        #  Router is the only one in the link

        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual(conf.DEFAULT_DESIGNATED_ROUTER, self.interface_ospfv3.backup_designated_router)

        self.reset_interface(conf.INTERFACE_STATE_BACKUP)
        neighbor_v2_1.delete_neighbor()
        neighbor_v2_2.delete_neighbor()
        neighbor_v3_1.delete_neighbor()
        neighbor_v3_2.delete_neighbor()

        #  Link DR fails

        neighbor_v2_1 = neighbor.Neighbor('10.10.10.10', conf.ROUTER_PRIORITY, 1, '222.222.1.10', 0, '222.222.1.10',
                                          self.interface_ospfv2.ipv4_address, conf.ROUTER_ID)
        neighbor_v2_2 = neighbor.Neighbor('2.2.2.2', conf.ROUTER_PRIORITY, 2, '222.222.0.2', 0, '222.222.1.10',
                                          self.interface_ospfv2.ipv4_address, conf.ROUTER_ID)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)  # DR fails
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)
        neighbor_v3_1 = neighbor.Neighbor('10.10.10.10', conf.ROUTER_PRIORITY, 1, '2001:db8:cafe:1::10', 0,
                                          '10.10.10.10', conf.ROUTER_ID, conf.ROUTER_ID)
        neighbor_v3_2 = neighbor.Neighbor('2.2.2.2', conf.ROUTER_PRIORITY, 2, '2001:db8:cafe:1::2', 0, '10.10.10.10',
                                          conf.ROUTER_ID, conf.ROUTER_ID)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)

        #  This router is the previous BDR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['2.2.2.2'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['2.2.2.2'] = neighbor_v3_2
        self.interface_ospfv2.designated_router = '222.222.1.10'
        self.interface_ospfv2.backup_designated_router = self.interface_ospfv2.ipv4_address
        self.interface_ospfv3.designated_router = '10.10.10.10'
        self.interface_ospfv3.backup_designated_router = conf.ROUTER_ID
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(self.interface_ospfv2.ipv4_address, self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.0.2', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.interface_ospfv2.neighbors['2.2.2.2'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.assertEqual(conf.ROUTER_ID, self.interface_ospfv3.designated_router)
        self.assertEqual('2.2.2.2', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.interface_ospfv3.neighbors['2.2.2.2'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_DROTHER)
        neighbor_v2_2.neighbor_id = '11.11.11.11'
        neighbor_v2_1.neighbor_dr = '222.222.1.11'
        neighbor_v2_1.neighbor_bdr = '222.222.1.10'
        neighbor_v2_2.neighbor_dr = '222.222.1.11'
        neighbor_v2_2.neighbor_bdr = '222.222.1.10'
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)
        neighbor_v3_2.neighbor_id = '11.11.11.11'
        neighbor_v3_1.neighbor_dr = '11.11.11.11'
        neighbor_v3_1.neighbor_bdr = '10.10.10.10'
        neighbor_v3_2.neighbor_dr = '11.11.11.11'
        neighbor_v3_2.neighbor_bdr = '10.10.10.10'
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)

        #  This router previously was non-DR/BDR, will become BDR
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['11.11.11.11'] = neighbor_v3_2
        self.interface_ospfv2.designated_router = '222.222.1.11'
        self.interface_ospfv2.backup_designated_router = '222.222.1.10'
        self.interface_ospfv3.designated_router = '11.11.11.11'
        self.interface_ospfv3.backup_designated_router = '10.10.10.10'
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('222.222.1.10', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.1.10', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.designated_router)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.interface_ospfv3.neighbors['10.10.10.10'].neighbor_state)

        self.reset_interface(conf.INTERFACE_STATE_DROTHER)
        neighbor_v2_3 = neighbor.Neighbor(
            '9.9.9.9', conf.ROUTER_PRIORITY, 2, '222.222.1.9', 0, conf.DEFAULT_DESIGNATED_ROUTER,
            conf.DEFAULT_DESIGNATED_ROUTER, conf.ROUTER_ID)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)
        neighbor_v2_3.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_3 = neighbor.Neighbor(
            '9.9.9.9', conf.ROUTER_PRIORITY, 2, '2001:db8:cafe:1::9', 0, conf.DEFAULT_DESIGNATED_ROUTER,
            conf.DEFAULT_DESIGNATED_ROUTER, conf.ROUTER_ID)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_DOWN)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_FULL)
        neighbor_v3_3.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)

        #  This router previously was non-DR/BDR and remains so
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_v3_1
        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['11.11.11.11'] = neighbor_v3_2
        self.interface_ospfv2.neighbors['9.9.9.9'] = neighbor_v2_3
        self.interface_ospfv3.neighbors['9.9.9.9'] = neighbor_v3_3
        self.interface_ospfv2.designated_router = '222.222.1.11'
        self.interface_ospfv2.backup_designated_router = '222.222.1.10'
        self.interface_ospfv3.designated_router = '11.11.11.11'
        self.interface_ospfv3.backup_designated_router = '10.10.10.10'
        self.interface_ospfv2.election_algorithm()
        self.interface_ospfv3.election_algorithm()
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv2.state)
        self.assertEqual('222.222.1.10', self.interface_ospfv2.designated_router)
        self.assertEqual('222.222.1.10', self.interface_ospfv2.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.interface_ospfv2.neighbors['10.10.10.10'].neighbor_state)
        self.assertEqual(conf.INTERFACE_STATE_DROTHER, self.interface_ospfv3.state)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.designated_router)
        self.assertEqual('10.10.10.10', self.interface_ospfv3.backup_designated_router)
        self.assertEqual(conf.NEIGHBOR_STATE_FULL, self.interface_ospfv3.neighbors['10.10.10.10'].neighbor_state)

        #  Shutdown

        neighbor_v2_1.delete_neighbor()
        neighbor_v2_2.delete_neighbor()
        neighbor_v2_3.delete_neighbor()
        neighbor_v3_1.delete_neighbor()
        neighbor_v3_2.delete_neighbor()
        neighbor_v3_3.delete_neighbor()

    #  Auxiliary method used in the previous test
    def reset_interface(self, state):
        self.interface_ospfv2.state = state
        self.interface_ospfv2.neighbors = {}
        self.interface_ospfv2.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv2.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv3.state = state
        self.interface_ospfv3.neighbors = {}
        self.interface_ospfv3.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv3.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER

    #  Successful run - Instant
    def test_election_algorithm_step_1(self):
        self.assertEqual(
            [[self.interface_ospfv2.ipv4_address, conf.ROUTER_PRIORITY, self.interface_ospfv2.designated_router,
              self.interface_ospfv2.backup_designated_router]], self.interface_ospfv2.election_algorithm_step_1())
        self.assertEqual(
            [[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv3.designated_router,
              self.interface_ospfv3.backup_designated_router]], self.interface_ospfv3.election_algorithm_step_1())

        neighbor_v2_1 = neighbor.Neighbor(
            '10.10.10.10', 1, 1, '222.222.1.10', 0, '222.222.0.1', '222.222.0.2', conf.ROUTER_ID)
        neighbor_v2_2 = neighbor.Neighbor(
            '11.11.11.11', 2, 2, '222.222.1.11', 0, '222.222.0.3', '222.222.0.4', conf.ROUTER_ID)
        neighbor_v3_1 = neighbor.Neighbor(
            '10.10.10.10', 1, 1, '2001:db8:cafe:1::10', 0, '1.1.1.1', '2.2.2.2', conf.ROUTER_ID)
        neighbor_v3_2 = neighbor.Neighbor(
            '11.11.11.11', 2, 2, '2001:db8:cafe:1::11', 0, '3.3.3.3', '4.4.4.4', conf.ROUTER_ID)
        neighbor_v2_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v2_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_1.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
        neighbor_v3_2.set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)

        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_v2_1
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_v3_1
        self.assertEqual(
            [[self.interface_ospfv2.ipv4_address, conf.ROUTER_PRIORITY, self.interface_ospfv2.designated_router,
              self.interface_ospfv2.backup_designated_router], ['222.222.1.10', 1, '222.222.0.1', '222.222.0.2']],
            self.interface_ospfv2.election_algorithm_step_1())
        self.assertEqual(
            [[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv3.designated_router,
              self.interface_ospfv3.backup_designated_router], ['10.10.10.10', 1, '1.1.1.1', '2.2.2.2']],
            self.interface_ospfv3.election_algorithm_step_1())

        self.interface_ospfv2.neighbors['11.11.11.11'] = neighbor_v2_2
        self.interface_ospfv3.neighbors['11.11.11.11'] = neighbor_v3_2
        self.assertEqual(
            [[self.interface_ospfv2.ipv4_address, conf.ROUTER_PRIORITY, self.interface_ospfv2.designated_router,
              self.interface_ospfv2.backup_designated_router], ['222.222.1.10', 1, '222.222.0.1', '222.222.0.2'],
             ['222.222.1.11', 2, '222.222.0.3', '222.222.0.4']], self.interface_ospfv2.election_algorithm_step_1())
        self.assertEqual(
            [[conf.ROUTER_ID, conf.ROUTER_PRIORITY, self.interface_ospfv3.designated_router,
              self.interface_ospfv3.backup_designated_router], ['10.10.10.10', 1, '1.1.1.1', '2.2.2.2'],
             ['11.11.11.11', 2, '3.3.3.3', '4.4.4.4']], self.interface_ospfv3.election_algorithm_step_1())

        #  Shutdown
        neighbor_v2_1.delete_neighbor()
        neighbor_v2_2.delete_neighbor()
        neighbor_v3_1.delete_neighbor()
        neighbor_v3_2.delete_neighbor()

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
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', self.interface_ospfv2.ipv4_address,
                                                                        first_run))
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4(self.interface_ospfv2.ipv4_address, '0.0.0.0',
                                                                        first_run))
        self.interface_ospfv2.designated_router = '0.0.0.0'
        self.interface_ospfv2.backup_designated_router = self.interface_ospfv2.ipv4_address
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', self.interface_ospfv2.ipv4_address,
                                                                         first_run))
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4(self.interface_ospfv2.ipv4_address, '0.0.0.0',
                                                                        first_run))
        self.interface_ospfv2.designated_router = self.interface_ospfv2.ipv4_address
        self.interface_ospfv2.backup_designated_router = '0.0.0.0'
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertTrue(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', self.interface_ospfv2.ipv4_address,
                                                                        first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4(self.interface_ospfv2.ipv4_address, '0.0.0.0',
                                                                         first_run))

        self.assertFalse(self.interface_ospfv3.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertTrue(self.interface_ospfv3.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertTrue(self.interface_ospfv3.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))
        self.interface_ospfv3.designated_router = '0.0.0.0'
        self.interface_ospfv3.backup_designated_router = conf.ROUTER_ID
        self.assertTrue(self.interface_ospfv3.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv3.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertTrue(self.interface_ospfv3.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))
        self.interface_ospfv3.designated_router = conf.ROUTER_ID
        self.interface_ospfv3.backup_designated_router = '0.0.0.0'
        self.assertTrue(self.interface_ospfv3.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertTrue(self.interface_ospfv3.election_algorithm_step_4('0.0.0.0', conf.ROUTER_ID, first_run))
        self.assertFalse(self.interface_ospfv3.election_algorithm_step_4(conf.ROUTER_ID, '0.0.0.0', first_run))

        first_run = False

        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', self.interface_ospfv2.ipv4_address,
                                                                         first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4(self.interface_ospfv2.ipv4_address, '0.0.0.0',
                                                                         first_run))
        self.interface_ospfv2.designated_router = '0.0.0.0'
        self.interface_ospfv2.backup_designated_router = self.interface_ospfv2.ipv4_address
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', self.interface_ospfv2.ipv4_address,
                                                                         first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4(self.interface_ospfv2.ipv4_address, '0.0.0.0',
                                                                         first_run))
        self.interface_ospfv2.designated_router = self.interface_ospfv2.ipv4_address
        self.interface_ospfv2.backup_designated_router = '0.0.0.0'
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', '0.0.0.0', first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4('0.0.0.0', self.interface_ospfv2.ipv4_address,
                                                                         first_run))
        self.assertFalse(self.interface_ospfv2.election_algorithm_step_4(self.interface_ospfv2.ipv4_address, '0.0.0.0',
                                                                         first_run))

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

        self.interface_ospfv2.election_algorithm_step_5('0.0.0.0', self.interface_ospfv2.ipv4_address)
        self.interface_ospfv3.election_algorithm_step_5('0.0.0.0', conf.ROUTER_ID)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv3.state)
        self.interface_ospfv2.election_algorithm_step_5('0.0.0.0', self.interface_ospfv2.ipv4_address)
        self.interface_ospfv3.election_algorithm_step_5('0.0.0.0', conf.ROUTER_ID)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_BACKUP, self.interface_ospfv3.state)

        self.interface_ospfv2.election_algorithm_step_5(self.interface_ospfv2.ipv4_address, '0.0.0.0')
        self.interface_ospfv3.election_algorithm_step_5(conf.ROUTER_ID, '0.0.0.0')
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv2.state)
        self.assertEqual(conf.INTERFACE_STATE_DR, self.interface_ospfv3.state)
        self.interface_ospfv2.election_algorithm_step_5(self.interface_ospfv2.ipv4_address, '0.0.0.0')
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
    def test_get_flooding_ip_address(self):
        self.assertEqual('', self.interface_ospfv2.get_flooding_ip_address())
        self.assertEqual('', self.interface_ospfv3.get_flooding_ip_address())
        neighbor_ospfv2 = neighbor.Neighbor('10.10.10.10', 1, 0, '222.222.0.1', 0, '0.0.0.0', '0.0.0.0', conf.ROUTER_ID)
        neighbor_ospfv3 = neighbor.Neighbor('10.10.10.10', 1, 1, 'fe80::1', 0, '0.0.0.0', '0.0.0.0', conf.ROUTER_ID)
        self.interface_ospfv2.neighbors['10.10.10.10'] = neighbor_ospfv2
        self.interface_ospfv3.neighbors['10.10.10.10'] = neighbor_ospfv3
        self.assertEqual(conf.ALL_DR_IPV4, self.interface_ospfv2.get_flooding_ip_address())
        self.assertEqual(conf.ALL_DR_IPV6, self.interface_ospfv3.get_flooding_ip_address())
        self.interface_ospfv2.state = conf.INTERFACE_STATE_DR
        self.interface_ospfv3.state = conf.INTERFACE_STATE_DR
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV4, self.interface_ospfv2.get_flooding_ip_address())
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV6, self.interface_ospfv3.get_flooding_ip_address())
        self.interface_ospfv2.state = conf.INTERFACE_STATE_BACKUP
        self.interface_ospfv3.state = conf.INTERFACE_STATE_BACKUP
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV4, self.interface_ospfv2.get_flooding_ip_address())
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV6, self.interface_ospfv3.get_flooding_ip_address())
        self.interface_ospfv2.state = conf.INTERFACE_STATE_DROTHER
        self.interface_ospfv3.state = conf.INTERFACE_STATE_DROTHER
        self.assertEqual(conf.ALL_DR_IPV4, self.interface_ospfv2.get_flooding_ip_address())
        self.assertEqual(conf.ALL_DR_IPV6, self.interface_ospfv3.get_flooding_ip_address())
        self.interface_ospfv2.state = conf.INTERFACE_STATE_POINT_POINT
        self.interface_ospfv3.state = conf.INTERFACE_STATE_POINT_POINT
        self.interface_ospfv2.type = conf.POINT_TO_POINT_INTERFACE
        self.interface_ospfv3.type = conf.POINT_TO_POINT_INTERFACE
        self.assertEqual('222.222.0.1', self.interface_ospfv2.get_flooding_ip_address())
        self.assertEqual('fe80::1', self.interface_ospfv3.get_flooding_ip_address())

    #  Successful run - Instant
    def test_get_ospf_multicast_destination_address(self):
        self.assertEqual(conf.ALL_DR_IPV4, self.interface_ospfv2.get_ospf_multicast_destination_address())
        self.assertEqual(conf.ALL_DR_IPV6, self.interface_ospfv3.get_ospf_multicast_destination_address())
        self.interface_ospfv2.backup_designated_router = self.interface_ospfv2.ipv4_address
        self.interface_ospfv3.backup_designated_router = self.interface_ospfv3.router_id
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV4, self.interface_ospfv2.get_ospf_multicast_destination_address())
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV6, self.interface_ospfv3.get_ospf_multicast_destination_address())
        self.interface_ospfv2.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv3.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv2.designated_router = self.interface_ospfv2.ipv4_address
        self.interface_ospfv3.designated_router = self.interface_ospfv3.router_id
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV4, self.interface_ospfv2.get_ospf_multicast_destination_address())
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV6, self.interface_ospfv3.get_ospf_multicast_destination_address())

    #  Successful run - Instant
    def test_is_dr_bdr(self):
        self.assertFalse(self.interface_ospfv2.is_dr_bdr())
        self.assertFalse(self.interface_ospfv3.is_dr_bdr())
        self.interface_ospfv2.backup_designated_router = self.interface_ospfv2.ipv4_address
        self.interface_ospfv3.backup_designated_router = self.interface_ospfv3.router_id
        self.assertTrue(self.interface_ospfv2.is_dr_bdr())
        self.assertTrue(self.interface_ospfv3.is_dr_bdr())
        self.interface_ospfv2.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv3.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.interface_ospfv2.designated_router = self.interface_ospfv2.ipv4_address
        self.interface_ospfv3.designated_router = self.interface_ospfv3.router_id
        self.assertTrue(self.interface_ospfv2.is_dr_bdr())
        self.assertTrue(self.interface_ospfv3.is_dr_bdr())

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


if __name__ == '__main__':
    unittest.main()
