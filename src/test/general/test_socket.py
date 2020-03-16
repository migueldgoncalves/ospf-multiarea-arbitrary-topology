import unittest
import timeout_decorator
import threading
import queue
import time

import general.sock as sock
import general.utils as utils
import packet.packet as packet
import conf.conf as conf

'''
This class tests the socket operations in the router
'''

TIMEOUT_SECONDS = 30  # Time to wait for the conclusion of a test
DATA_TO_SEND_OSPFV2 = b'\x02\x01\x000\x04\x04\x04\x04\x02\x02\x02\x02\x14\xb3\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02' \
                      b'\xff\xff\xff\x00\x00\n\x02\x01\x00\x00\x00(\xde\xde\x01\x02\x00\x00\x00\x00\x01\x01\x01\x01'
DATA_TO_SEND_OSPFV3 = b'\x03\x01\x00(\x04\x04\x04\x04\x02\x02\x02\x02;j\x03\x00\x00\x00\x00\x01\x01\x00\x00\x02\x00\n' \
                      b'\x00(\xde\xde\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01'
OTHER_ROUTER_IPV4_ADDRESS = '222.222.1.1'
OTHER_ROUTER_IPV6_ADDRESS = 'fe80::c001:18ff:fe34:10'
OTHER_ROUTER_ID = '1.1.1.1'


#  Full successful run - 42-82 s
class SocketTest(unittest.TestCase):
    pipeline = None
    shutdown = None
    socket = None

    def setUp(self):
        self.pipeline = queue.Queue()
        self.shutdown = threading.Event()
        self.socket = sock.Socket()

    #  Successful run - 10-20 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_receive_data_successful_ipv4(self):
        accept_self_packets = False
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv4, args=(
            self.pipeline, self.shutdown, conf.INTERFACE_NAMES[0], accept_self_packets, is_dr))
        thread.start()

        while self.pipeline.qsize() == 0:
            pass
        self.assertEqual(1, self.pipeline.qsize())
        data_array = self.pipeline.get()
        self.assertEqual(2, len(data_array))

        packet_byte_stream = data_array[0]
        source_ip_address = data_array[1]
        received_packet = packet.Packet.unpack_packet(packet_byte_stream)

        self.assertEqual(conf.VERSION_IPV4, received_packet.header.version)
        self.assertEqual(conf.PACKET_TYPE_HELLO, received_packet.header.packet_type)
        self.assertEqual(OTHER_ROUTER_IPV4_ADDRESS, received_packet.body.designated_router)
        self.assertEqual(OTHER_ROUTER_IPV4_ADDRESS, source_ip_address)

        self.shutdown.set()  # Signals the thread to shutdown
        thread.join()

    #  Successful run - 10-20 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_receive_data_successful_ipv6(self):
        accept_self_packets = False
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv6, args=(
            self.pipeline, self.shutdown, conf.INTERFACE_NAMES[0], accept_self_packets, is_dr))
        thread.start()

        while self.pipeline.qsize() == 0:
            pass
        self.assertEqual(1, self.pipeline.qsize())
        data_array = self.pipeline.get()
        self.assertEqual(2, len(data_array))

        packet_byte_stream = data_array[0]
        source_ip_address = data_array[1]
        received_packet = packet.Packet.unpack_packet(packet_byte_stream)

        self.assertEqual(conf.VERSION_IPV6, received_packet.header.version)
        self.assertEqual(conf.PACKET_TYPE_HELLO, received_packet.header.packet_type)
        self.assertEqual(OTHER_ROUTER_ID, received_packet.body.designated_router)
        self.assertEqual(OTHER_ROUTER_IPV6_ADDRESS, source_ip_address)

        self.shutdown.set()
        thread.join()

    #  Successful run - Instant
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_is_dr_ipv4(self):
        accept_self_packets = False
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv4, args=(
            self.pipeline, self.shutdown, conf.INTERFACE_NAMES[0], accept_self_packets, is_dr))
        thread.start()
        self.shutdown.set()
        thread.join()
        self.assertFalse(self.socket.is_dr)

        is_dr = True
        thread = threading.Thread(target=self.socket.receive_ipv4, args=(
            self.pipeline, self.shutdown, conf.INTERFACE_NAMES[0], accept_self_packets, is_dr))
        thread.start()
        self.shutdown.set()
        thread.join()
        self.assertTrue(self.socket.is_dr)

    #  Successful run - Instant
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_is_dr_ipv6(self):
        accept_self_packets = False
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv6, args=(
            self.pipeline, self.shutdown, conf.INTERFACE_NAMES[0], accept_self_packets, is_dr))
        thread.start()
        self.shutdown.set()
        thread.join()
        self.assertFalse(self.socket.is_dr)

        is_dr = True
        thread = threading.Thread(target=self.socket.receive_ipv6, args=(
            self.pipeline, self.shutdown, conf.INTERFACE_NAMES[0], accept_self_packets, is_dr))
        thread.start()
        self.shutdown.set()
        thread.join()
        self.assertTrue(self.socket.is_dr)

    #  Successful run - Instant
    def test_receive_invalid_parameters_ipv4(self):
        accept_self_packets = False
        is_dr = False
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv4(sock.Socket(), None, self.shutdown, conf.INTERFACE_NAMES[0],
                                     accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv4(sock.Socket(), self.pipeline, None, conf.INTERFACE_NAMES[0],
                                     accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv4(sock.Socket(), self.pipeline, self.shutdown, None,
                                     accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv4(sock.Socket(), self.pipeline, self.shutdown, '',
                                     accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv4(sock.Socket(), self.pipeline, self.shutdown, '        ',
                                     accept_self_packets, is_dr)

    #  Successful run - Instant
    def test_receive_invalid_parameters_ipv6(self):
        accept_self_packets = False
        is_dr = False
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv6(sock.Socket(), None, self.shutdown, conf.INTERFACE_NAMES[0],
                                     accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv6(sock.Socket(), self.pipeline, None, conf.INTERFACE_NAMES[0],
                                     accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv6(sock.Socket(), self.pipeline, self.shutdown, None,
                                     accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv6(sock.Socket(), self.pipeline, self.shutdown, '',
                                     accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            sock.Socket.receive_ipv6(sock.Socket(), self.pipeline, self.shutdown, '        ',
                                     accept_self_packets, is_dr)

    #  Successful run - 11-21 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_send_data_successful_ipv4(self):
        accept_self_packets = True
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv4, args=(
            self.pipeline, self.shutdown, conf.INTERFACE_NAMES[0], accept_self_packets, is_dr))
        thread.start()
        time.sleep(1)   # Needed to give CPU to other thread
        self.socket.send_ipv4(DATA_TO_SEND_OSPFV2, conf.ALL_OSPF_ROUTERS_IPV4, conf.INTERFACE_NAMES[0])
        time.sleep(10)  # Wait of 10 s ensures other router always sends one and only one Hello packet during wait
        self.assertTrue(self.pipeline.qsize() > 1)  # Hello packets from other router will appear while waiting

        packets_data = []
        interface_ip_address = utils.Utils.get_ipv4_address_from_interface_name(conf.INTERFACE_NAMES[0])
        while not self.pipeline.empty():
            packets_data.append(self.pipeline.get())
        self_packet_data = []
        for p in packets_data:
            if p[1] == interface_ip_address:
                self_packet_data.append(p)
        self.assertEqual(1, len(self_packet_data))  # One and only one packet from this router received
        self_packet = packet.Packet.unpack_packet(self_packet_data[0][0])
        self_source_ip_address = self_packet_data[0][1]

        self.assertEqual(conf.VERSION_IPV4, self_packet.header.version)
        self.assertEqual(conf.PACKET_TYPE_HELLO, self_packet.header.packet_type)
        self.assertEqual(conf.ROUTER_ID, self_packet.header.router_id)
        self.assertEqual(interface_ip_address, self_source_ip_address)

        self.shutdown.set()
        thread.join()
        self.pipeline = queue.Queue()
        self.shutdown = threading.Event()
        self.socket = sock.Socket()

    #  Successful run - 11-21 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_send_data_successful_ipv6(self):
        accept_self_packets = True
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv6, args=(
            self.pipeline, self.shutdown, conf.INTERFACE_NAMES[0], accept_self_packets, is_dr))
        thread.start()
        time.sleep(1)
        self.socket.send_ipv6(DATA_TO_SEND_OSPFV3, conf.ALL_OSPF_ROUTERS_IPV6, conf.INTERFACE_NAMES[0])
        time.sleep(10)
        self.assertTrue(self.pipeline.qsize() > 1)

        packets_data = []
        interface_ip_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(conf.INTERFACE_NAMES[0])
        while not self.pipeline.empty():
            packets_data.append(self.pipeline.get())
        self_packet_data = []
        for p in packets_data:
            if p[1] == interface_ip_address:
                self_packet_data.append(p)
        self.assertEqual(1, len(self_packet_data))
        self_packet = packet.Packet.unpack_packet(self_packet_data[0][0])
        self_source_ip_address = self_packet_data[0][1]

        self.assertEqual(conf.VERSION_IPV6, self_packet.header.version)
        self.assertEqual(conf.PACKET_TYPE_HELLO, self_packet.header.packet_type)
        self.assertEqual(conf.ROUTER_ID, self_packet.header.router_id)
        self.assertEqual(interface_ip_address, self_source_ip_address)

        self.shutdown.set()
        thread.join()

    #  Successful run - Instant
    def test_send_invalid_parameters_ipv4(self):
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(
                sock.Socket(), None, conf.ALL_OSPF_ROUTERS_IPV4, conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(
                sock.Socket(), '', conf.ALL_OSPF_ROUTERS_IPV4, conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(
                sock.Socket(), '        ', conf.ALL_OSPF_ROUTERS_IPV4, conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(sock.Socket(), DATA_TO_SEND_OSPFV2, None, conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(sock.Socket(), DATA_TO_SEND_OSPFV2, '', conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(sock.Socket(), DATA_TO_SEND_OSPFV2, '        ', conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(sock.Socket(), DATA_TO_SEND_OSPFV2, conf.ALL_OSPF_ROUTERS_IPV4, None)
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(sock.Socket(), DATA_TO_SEND_OSPFV2, conf.ALL_OSPF_ROUTERS_IPV4, '')
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv4(sock.Socket(), DATA_TO_SEND_OSPFV2, conf.ALL_OSPF_ROUTERS_IPV4, '        ')

    #  Successful run - Instant
    def test_send_invalid_parameters_ipv6(self):
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(
                sock.Socket(), None, conf.ALL_OSPF_ROUTERS_IPV6, conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(
                sock.Socket(), '', conf.ALL_OSPF_ROUTERS_IPV6, conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(
                sock.Socket(), '        ', conf.ALL_OSPF_ROUTERS_IPV6, conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(sock.Socket(), DATA_TO_SEND_OSPFV2, None, conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(sock.Socket(), DATA_TO_SEND_OSPFV2, '', conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(sock.Socket(), DATA_TO_SEND_OSPFV2, '        ', conf.INTERFACE_NAMES[0])
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(sock.Socket(), DATA_TO_SEND_OSPFV2, conf.ALL_OSPF_ROUTERS_IPV6, None)
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(sock.Socket(), DATA_TO_SEND_OSPFV2, conf.ALL_OSPF_ROUTERS_IPV6, '')
        with self.assertRaises(ValueError):
            sock.Socket.send_ipv6(sock.Socket(), DATA_TO_SEND_OSPFV2, conf.ALL_OSPF_ROUTERS_IPV6, '        ')

    def tearDown(self):
        self.pipeline = None
        self.shutdown = None
        self.socket = None


if __name__ == '__main__':
    unittest.main()
