import unittest
import threading
import queue
import time

import conf.conf as conf
import general.utils as utils
import general.socket_python as socket_python
import interface.interface as interface

'''
This class tests the interface operations in the router
'''

PACKET_BYTES = b'\x02\x01\x00,\x03\x03\x03\x03\x00\x00\x00\x00\xf6\x98\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff' \
               b'\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00'


#  Full successful run - 21-30 s, can be longer
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

    #  Successful run - 21-30 s, can be longer
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
