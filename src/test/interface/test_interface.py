import unittest
import threading
import queue
import time

import conf.conf as conf
import general.utils as utils
import general.socket_python as socket_python
import interface.interface as interface
import packet.packet_creator as packet_creator
import packet.packet_reader as packet_reader

'''
This class tests the interface operations in the router
'''

PACKET_BYTES = b'\x02\x01\x00,\x04\x04\x04\x04\x00\x00\x00\x00\xf4\x96\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff' \
               b'\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00'


#  Full successful run - 35-50 s, can be longer
class InterfaceTest(unittest.TestCase):
    interface = None

    interface_identifier = ''
    ip_address = ''
    network_mask = 0
    area_id = ''
    interface_pipeline = None
    interface_shutdown = None

    utils = utils.Utils()

    def setUp(self):
        self.interface_identifier = conf.INTERFACE_NAMES[0]
        self.ip_address = self.utils.get_ipv4_address_from_interface_name(conf.INTERFACE_NAMES[0])
        self.network_mask = self.utils.get_ipv4_network_mask_from_interface_name(conf.INTERFACE_NAMES[0])
        self.area_id = conf.INTERFACE_AREAS[0]
        self.interface_pipeline = queue.Queue()
        self.interface_shutdown = threading.Event()
        self.interface = interface.Interface(self.interface_identifier, self.ip_address, self.network_mask,
                                             self.area_id, self.interface_pipeline, self.interface_shutdown)

    #  Successful run - 22-36 s, can be longer
    def test_interface_loop_packet_sending_successful(self):
        socket = socket_python.Socket()
        socket_pipeline = queue.Queue()
        socket_shutdown = threading.Event()
        accept_self_packets = True
        is_dr = False

        #  Creates thread with socket that listens for packets from the router itself
        thread_socket = threading.Thread(target=socket.receive_ipv4,
                                         args=(socket_pipeline, socket_shutdown, self.interface_identifier,
                                               accept_self_packets, is_dr))
        thread_socket.start()

        thread_interface = threading.Thread(target=self.interface.interface_loop)
        thread_interface.start()
        time.sleep(2 * conf.HELLO_INTERVAL + 1)  # Allows for Hello packets to be sent

        #  Shutdown
        self.interface_shutdown.set()
        socket_shutdown.set()
        thread_interface.join()
        thread_socket.join()

    #  Successful run - 12-18 s, can be longer
    def test_interface_loop_incoming_packet_processing_successful(self):
        socket = socket_python.Socket()
        socket_pipeline = queue.Queue()
        socket_shutdown = threading.Event()
        accept_self_packets = False
        is_dr = False
        one_way = packet_creator.PacketCreator([conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO, '1.1.1.1', '0.0.0.0', 0, 0])
        one_way.create_hello_v2_packet('255.255.255.0', conf.HELLO_INTERVAL, 12, conf.ROUTER_PRIORITY,
                                       conf.ROUTER_DEAD_INTERVAL, '222.222.1.1', conf.DEFAULT_DESIGNATED_ROUTER, ())
        self.assertEqual(0, len(self.interface.neighbors))

        #  Interface receives packet from neighbor not acknowledging router itself
        #  Neighbor is created and goes to INIT state
        thread_interface = threading.Thread(target=self.interface.interface_loop)
        thread_interface.start()
        self.interface_pipeline.put([one_way, '222.222.1.1'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface.neighbors['1.1.1.1'].neighbor_state)

        #  Creates thread with socket that listens for packets in the network
        thread_socket = threading.Thread(target=socket.receive_ipv4,
                                         args=(socket_pipeline, socket_shutdown, self.interface_identifier,
                                               accept_self_packets, is_dr))
        thread_socket.start()

        #  Listens for a packet from the neighbor acknowledging the router itself
        #  Neighbor goes to 2-WAY state
        while True:
            if not socket_pipeline.empty():
                byte_array = socket_pipeline.get()[0]
                if (packet_reader.PacketReader.get_ospf_version(byte_array) == conf.VERSION_IPV4) & \
                        (packet_reader.PacketReader.get_ospf_packet_type(byte_array) == conf.PACKET_TYPE_HELLO):
                    two_way = packet_reader.PacketReader.convert_bytes_to_packet(byte_array)
                    self.interface_pipeline.put([two_way, '222.222.1.1'])
                    break
        time.sleep(1)
        self.assertEqual(1, len(self.interface.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface.neighbors['1.1.1.1'].neighbor_state)

        #  Interface receives another packet from neighbor not acknowledging router itself
        #  Neighbor goes to INIT state
        self.interface_pipeline.put([one_way, '222.222.1.1'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_INIT, self.interface.neighbors['1.1.1.1'].neighbor_state)

        #  Shutdown and restart
        #  Neighbor goes to DOWN state and is deleted
        self.interface_shutdown.set()
        thread_interface.join()
        self.assertEqual(0, len(self.interface.neighbors))
        thread_interface = threading.Thread(target=self.interface.interface_loop)
        thread_interface.start()

        #  Interface receives another packet from neighbor acknowledging router itself
        #  Neighbor this time jumps to 2-WAY state
        self.interface_pipeline.put([two_way, '222.222.1.1'])
        time.sleep(1)
        self.assertEqual(1, len(self.interface.neighbors))
        self.assertEqual(conf.NEIGHBOR_STATE_2_WAY, self.interface.neighbors['1.1.1.1'].neighbor_state)

        #  Final shutdown
        #  Neighbor goes to DOWN state and is deleted
        self.interface_shutdown.set()
        socket_shutdown.set()
        thread_interface.join()
        thread_socket.join()

    #  Successful run - Instant
    def test_create_packet_successful(self):
        packet = self.interface.create_packet()
        self.assertEqual(PACKET_BYTES, packet)

    def tearDown(self):
        self.interface_identifier = ''
        self.ip_address = ''
        self.network_mask = 0
        self.area_id = ''
        self.interface_pipeline = None
        self.interface_shutdown = None
        self.interface = None
