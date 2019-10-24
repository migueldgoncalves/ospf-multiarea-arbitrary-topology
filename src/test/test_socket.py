import unittest
import timeout_decorator
import threading

import general.socket_python as socket_python

TIMEOUT_SECONDS = 15
DATA_TO_SEND = b'11111111111111'
OSPF_ALL_PACKETS = "224.0.0.5"
SOURCE_INTERFACE = "ens33"


class SocketTest(unittest.TestCase):

    @timeout_decorator.timeout(TIMEOUT_SECONDS)
    def test_receive_data_successful(self):
        #  For IPv4
        buffer = []
        accept_self_packets = False
        is_dr = False
        socket = socket_python.Socket()
        thread = threading.Thread(target=socket.receive_ipv4, args=(buffer, SOURCE_INTERFACE, accept_self_packets,
                                                                    is_dr))
        thread.start()
        while len(buffer) == 0:
            if len(buffer) > 0:
                break
        socket.shutdown()
        thread.join()

        #  For IPv6
        buffer = []
        socket = socket_python.Socket()
        thread = threading.Thread(target=socket.receive_ipv6, args=(buffer, SOURCE_INTERFACE, accept_self_packets,
                                                                    is_dr))
        thread.start()
        while len(buffer) == 0:
            if len(buffer) > 0:
                break
        socket.shutdown()
        thread.join()

    def test_is_dr(self):
        buffer = []
        accept_self_packets = False
        is_dr = False
        socket = socket_python.Socket()
        thread = threading.Thread(target=socket.receive_ipv4, args=(buffer, SOURCE_INTERFACE, accept_self_packets,
                                                                    is_dr))
        thread.start()
        socket.shutdown()
        thread.join()
        self.assertFalse(socket.is_dr)

        is_dr = True
        thread = threading.Thread(target=socket.receive_ipv4, args=(buffer, SOURCE_INTERFACE, accept_self_packets,
                                                                    is_dr))
        thread.start()
        socket.shutdown()
        thread.join()
        self.assertTrue(socket.is_dr)

    def test_receive_no_parameters(self):
        buffer = []
        accept_self_packets = False
        is_dr = False
        self.assertRaises(ValueError,
                          socket_python.Socket.receive_ipv4(socket_python.Socket(), '', buffer, accept_self_packets,
                                                            is_dr))
        self.assertRaises(ValueError,
                          socket_python.Socket.receive_ipv6(socket_python.Socket(), '', buffer, accept_self_packets,
                                                            is_dr))
        self.assertRaises(ValueError,
                          socket_python.Socket.receive_ipv4(socket_python.Socket(), SOURCE_INTERFACE, None,
                                                            accept_self_packets, is_dr))
        self.assertRaises(ValueError,
                          socket_python.Socket.receive_ipv6(socket_python.Socket(), SOURCE_INTERFACE, None,
                                                            accept_self_packets, is_dr))

    def test_send_data_successful(self):
        #  For IPv4
        buffer = []
        accept_self_packets = True
        is_dr = False
        socket = socket_python.Socket()
        thread = threading.Thread(target=socket.receive_ipv4, args=(buffer, SOURCE_INTERFACE, accept_self_packets,
                                                                    is_dr))
        thread.start()
        socket.send_ipv4(DATA_TO_SEND, OSPF_ALL_PACKETS, SOURCE_INTERFACE)
        self.assertTrue(len(buffer) > 0)
        socket.shutdown()

        # For IPv6
        buffer = []
        socket = socket_python.Socket()
        thread = threading.Thread(target=socket.receive_ipv4, args=(buffer, SOURCE_INTERFACE, accept_self_packets,
                                                                    is_dr))
        thread.start()
        socket.send_ipv6(DATA_TO_SEND, OSPF_ALL_PACKETS, SOURCE_INTERFACE)
        self.assertTrue(len(buffer) > 0)
        socket.shutdown()

    def test_send_no_parameters(self):
        socket = socket_python.Socket()
        self.assertRaises(ValueError, socket.send_ipv4(None, OSPF_ALL_PACKETS, SOURCE_INTERFACE))
        self.assertRaises(ValueError, socket.send_ipv4(DATA_TO_SEND, '', SOURCE_INTERFACE))
        self.assertRaises(ValueError, socket.send_ipv4(DATA_TO_SEND, OSPF_ALL_PACKETS, ''))


if __name__ == '__main__':
    unittest.main()
