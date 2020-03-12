import unittest
import threading
import queue
import time

import conf.conf as conf
import general.utils as utils
import general.sock as sock
import interface.interface as interface
import packet.packet as packet

'''
This class tests the interface operations in the router
'''

PACKET_BYTES = b'\x02\x01\x00,\x04\x04\x04\x04\x00\x00\x00\x00\xf4\x96\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff' \
               b'\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00'


#  Full successful run - 129-156 s
class InterfaceTest(unittest.TestCase):
    interface_identifier = ''
    ipv4_address = '0.0.0.0'
    ipv6_address = '::'
    network_mask = 0
    link_prefixes = []
    area_id = '0.0.0.0'
    interface_pipeline_v2 = None
    interface_pipeline_v3 = None
    interface_shutdown_v2 = None
    interface_shutdown_v3 = None

    interface_ospfv2 = None
    interface_ospfv3 = None

    utils = utils.Utils()

    def setUp(self):
        self.interface_identifier = conf.INTERFACE_NAMES[0]
        self.ipv4_address = self.utils.get_ipv4_address_from_interface_name(conf.INTERFACE_NAMES[0])
        self.ipv6_address = self.utils.get_ipv6_link_local_address_from_interface_name(conf.INTERFACE_NAMES[0])
        self.network_mask = self.utils.get_ipv4_network_mask_from_interface_name(conf.INTERFACE_NAMES[0])
        self.link_prefixes = self.utils.get_ipv6_prefix_from_interface_name(conf.INTERFACE_NAMES[0])
        self.area_id = conf.INTERFACE_AREAS[0]
        self.interface_pipeline_v2 = queue.Queue()
        self.interface_pipeline_v3 = queue.Queue()
        self.interface_shutdown_v2 = threading.Event()
        self.interface_shutdown_v3 = threading.Event()
        self.interface_ospfv2 = interface.Interface(
            self.interface_identifier, self.ipv4_address, '', self.network_mask, [], self.area_id,
            self.interface_pipeline_v2, self.interface_shutdown_v2)
        self.interface_ospfv3 = interface.Interface(
            self.interface_identifier, '', self.ipv6_address, '', self.link_prefixes, self.area_id,
            self.interface_pipeline_v3, self.interface_shutdown_v3)

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
        time.sleep(2 * conf.HELLO_INTERVAL + 1)  # Allows for 3 Hello packets to be sent
        self.assertTrue(3, socket_pipeline_v2.qsize())
        self.assertTrue(3, socket_pipeline_v3.qsize())

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
        self.interface_pipeline_v2.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
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
        #  Neighbor goes to 2-WAY state
        while True:
            if not socket_pipeline_v2.empty():
                byte_array = socket_pipeline_v2.get()[0]
                if (packet.Packet.get_ospf_version(byte_array) == conf.VERSION_IPV4) & \
                        (packet.Packet.get_ospf_packet_type(byte_array) == conf.PACKET_TYPE_HELLO):
                    two_way_v2 = packet.Packet.unpack_packet(byte_array)
                    self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
                    break
        while True:
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
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(conf.ROUTER_DEAD_INTERVAL - 5)  # More than 40 s will have passed since original Hello packet
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # New Hello packet resets neighbor timer
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)
        time.sleep(6)
        self.assertEqual(0, len(self.interface_ospfv2.neighbors))  # Neighbor timer expired
        self.assertEqual(0, len(self.interface_ospfv3.neighbors))
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))  # Neighbor is recognized again
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        #  Interface receives another packet from neighbor not acknowledging this router
        #  Neighbor goes to INIT state
        self.interface_pipeline_v2.put([one_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([one_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

        #  Shutdown and restart
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
        #  Neighbor this time jumps to 2-WAY state
        self.interface_pipeline_v2.put([two_way_v2, '222.222.1.1'])
        self.interface_pipeline_v3.put([two_way_v3, 'fe80::c001:18ff:fe34:10'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface_ospfv2.neighbors))
        self.assertEqual(1, len(self.interface_ospfv3.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv2.neighbors['1.1.1.1'].neighbor_state)
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface_ospfv3.neighbors['1.1.1.1'].neighbor_state)

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

    #  Successful run - Instant
    def test_create_packet_successful(self):
        new_packet = self.interface_ospfv2.create_packet()
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

    def tearDown(self):
        self.interface_pipeline_v2 = None
        self.interface_pipeline_v3 = None
        self.interface_shutdown_v2 = None
        self.interface_shutdown_v3 = None
        self.interface_ospfv2 = None
        self.interface_ospfv3 = None
