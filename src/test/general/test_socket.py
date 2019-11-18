import unittest
import timeout_decorator
import threading
import queue

import general.socket_python as socket_python
import packet.packet_reader as packer_reader
import packet.packet_creator as packet_creator
import conf.conf as conf

'''
This class tests the socket operations in the router
'''

TIMEOUT_SECONDS = 30
DATA_TO_SEND = b'11111111111111'
OSPF_ALL_PACKETS_IPV4 = "224.0.0.5"
OSPF_ALL_PACKETS_IPV6 = "ff02::5"
SOURCE_INTERFACE = "ens33"


#  Full successful run - 40-80 s
class SocketTest(unittest.TestCase):
    pipeline = None
    shutdown = None
    socket = None

    def setUp(self):
        self.pipeline = queue.Queue()
        self.shutdown = threading.Event()
        self.socket = socket_python.Socket()

    #  Successful run - 10-20 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_receive_data_successful_ipv4(self):
        accept_self_packets = False
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv4, args=(self.pipeline, self.shutdown, SOURCE_INTERFACE,
                                                                         accept_self_packets, is_dr))
        thread.start()

        while self.pipeline.qsize() == 0:
            pass
        self.assertEqual(1, self.pipeline.qsize())
        data_array = self.pipeline.get()
        self.assertEqual(3, len(data_array))

        packet_byte_stream = data_array[0]
        source_ip_address = data_array[1]
        destination_ip_address = data_array[2]
        packet = packer_reader.PacketReader.convert_bytes_to_packet(packet_byte_stream)

        self.assertEqual(conf.VERSION_IPV4, packet.header.version)
        self.assertEqual(conf.PACKET_TYPE_HELLO, packet.header.packet_type)
        self.assertEqual('222.222.1.1', packet.body.designated_router)
        self.assertEqual('222.222.1.1', source_ip_address)
        self.assertEqual(conf.ALL_OSPF_ROUTERS_IPV4, destination_ip_address)

        self.shutdown.set()  # Signals the thread to shutdown
        thread.join()

    #  Successful run - 10-20 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_receive_data_successful_ipv6(self):
        accept_self_packets = False
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv6, args=(self.pipeline, self.shutdown, SOURCE_INTERFACE,
                                                                         accept_self_packets, is_dr))
        thread.start()
        while self.pipeline.qsize() == 0:
            pass
        self.shutdown.set()
        thread.join()

    #  Successful run - Instant
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_is_dr_ipv4(self):
        accept_self_packets = False
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv4, args=(self.pipeline, self.shutdown, SOURCE_INTERFACE,
                                                                         accept_self_packets, is_dr))
        thread.start()
        self.shutdown.set()
        thread.join()
        self.assertFalse(self.socket.is_dr)

        is_dr = True
        thread = threading.Thread(target=self.socket.receive_ipv4, args=(self.pipeline, self.shutdown, SOURCE_INTERFACE,
                                                                         accept_self_packets, is_dr))
        thread.start()
        self.shutdown.set()
        thread.join()
        self.assertTrue(self.socket.is_dr)

    #  Successful run - Instant
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_is_dr_ipv6(self):
        accept_self_packets = False
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv6, args=(self.pipeline, self.shutdown, SOURCE_INTERFACE,
                                                                         accept_self_packets, is_dr))
        thread.start()
        self.shutdown.set()
        thread.join()
        self.assertFalse(self.socket.is_dr)

        is_dr = True
        thread = threading.Thread(target=self.socket.receive_ipv6, args=(self.pipeline, self.shutdown, SOURCE_INTERFACE,
                                                                         accept_self_packets, is_dr))
        thread.start()
        self.shutdown.set()
        thread.join()
        self.assertTrue(self.socket.is_dr)

    #  Successful run - Instant
    def test_receive_invalid_parameters_ipv4(self):
        accept_self_packets = False
        is_dr = False
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv4(socket_python.Socket(), None, self.shutdown, SOURCE_INTERFACE,
                                              accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv4(socket_python.Socket(), self.pipeline, None, SOURCE_INTERFACE,
                                              accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv4(socket_python.Socket(), self.pipeline, self.shutdown, None,
                                              accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv4(socket_python.Socket(), self.pipeline, self.shutdown, '',
                                              accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv4(socket_python.Socket(), self.pipeline, self.shutdown, '        ',
                                              accept_self_packets, is_dr)

    #  Successful run - Instant
    def test_receive_invalid_parameters_ipv6(self):
        accept_self_packets = False
        is_dr = False
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv6(socket_python.Socket(), None, self.shutdown, SOURCE_INTERFACE,
                                              accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv6(socket_python.Socket(), self.pipeline, None, SOURCE_INTERFACE,
                                              accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv6(socket_python.Socket(), self.pipeline, self.shutdown, None,
                                              accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv6(socket_python.Socket(), self.pipeline, self.shutdown, '',
                                              accept_self_packets, is_dr)
        with self.assertRaises(ValueError):
            socket_python.Socket.receive_ipv6(socket_python.Socket(), self.pipeline, self.shutdown, '        ',
                                              accept_self_packets, is_dr)

    #  Successful run - 10-20 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_send_data_successful_ipv4(self):
        accept_self_packets = True
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv4, args=(self.pipeline, self.shutdown, SOURCE_INTERFACE,
                                                                         accept_self_packets, is_dr))
        thread.start()  # Sends a packet that should be listened by the receiving socket
        self.socket.send_ipv4(DATA_TO_SEND, OSPF_ALL_PACKETS_IPV4, SOURCE_INTERFACE)
        while self.pipeline.qsize() == 0:
            pass
        self.shutdown.set()
        thread.join()

    #  Successful run - 10-20 s
    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_send_data_successful_ipv6(self):
        accept_self_packets = True
        is_dr = False
        thread = threading.Thread(target=self.socket.receive_ipv6, args=(self.pipeline, self.shutdown, SOURCE_INTERFACE,
                                                                         accept_self_packets, is_dr))
        thread.start()  # Sends a packet that should be listened by the receiving socket
        self.socket.send_ipv6(DATA_TO_SEND, OSPF_ALL_PACKETS_IPV6, SOURCE_INTERFACE)
        while self.pipeline.qsize() == 0:
            pass
        self.shutdown.set()
        thread.join()

    #  Successful run - Instant
    def test_send_invalid_parameters_ipv4(self):
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), None, OSPF_ALL_PACKETS_IPV4, SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), '', OSPF_ALL_PACKETS_IPV4, SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), '        ', OSPF_ALL_PACKETS_IPV4, SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), DATA_TO_SEND, None, SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), DATA_TO_SEND, '', SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), DATA_TO_SEND, '        ', SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), DATA_TO_SEND, OSPF_ALL_PACKETS_IPV4, None)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), DATA_TO_SEND, OSPF_ALL_PACKETS_IPV4, '')
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv4(socket_python.Socket(), DATA_TO_SEND, OSPF_ALL_PACKETS_IPV4, '        ')

    #  Successful run - Instant
    def test_send_invalid_parameters_ipv6(self):
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), None, OSPF_ALL_PACKETS_IPV4, SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), '', OSPF_ALL_PACKETS_IPV4, SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), '        ', OSPF_ALL_PACKETS_IPV4, SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), DATA_TO_SEND, None, SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), DATA_TO_SEND, '', SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), DATA_TO_SEND, '        ', SOURCE_INTERFACE)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), DATA_TO_SEND, OSPF_ALL_PACKETS_IPV4, None)
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), DATA_TO_SEND, OSPF_ALL_PACKETS_IPV4, '')
        with self.assertRaises(ValueError):
            socket_python.Socket.send_ipv6(socket_python.Socket(), DATA_TO_SEND, OSPF_ALL_PACKETS_IPV4, '        ')

    def tearDown(self):
        self.pipeline = None
        self.shutdown = None
        self.socket = None


if __name__ == '__main__':
    unittest.main()
