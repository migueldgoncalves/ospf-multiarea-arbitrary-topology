import unittest
import os

'''
This class tests connection with the GNS3 network elements
'''

PING_SUCCESSFUL = 0  # Ping command returns 0 if successful
HOST_INTERFACE_NAME = "ens33"

ROUTER_INT_IPV4 = '222.222.1.1'
HOST_INT_IPV4 = '222.222.1.2'
ROUTER_INT_IPV6 = '2001:db8:cafe:1::1'
HOST_INT_IPV6 = '2001:db8:cafe:1::2'


#  Full successful run - Instant
class PingTest(unittest.TestCase):

    def test_host_ping_ipv4(self):
        self.assertEqual(PING_SUCCESSFUL, os.system("ping -c 1 " + HOST_INT_IPV4))

    def test_router_ping_ipv4(self):
        self.assertEqual(PING_SUCCESSFUL, os.system("ping -c 1 " + ROUTER_INT_IPV4))

    def test_host_ping_ipv6(self):
        self.assertEqual(PING_SUCCESSFUL, os.system("ping6 -c 1 -I " + HOST_INTERFACE_NAME + " " + HOST_INT_IPV6))

    def test_router_ping_ipv6(self):
        self.assertEqual(PING_SUCCESSFUL, os.system("ping6 -c 1 -I " + HOST_INTERFACE_NAME + " " + ROUTER_INT_IPV6))


if __name__ == '__main__':
    unittest.main()
