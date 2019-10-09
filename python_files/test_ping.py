import unittest
import os

'''
Set of tests to ensure correctness of addresses and connectivity between host and router
This set of tests must be run as superuser
'''

PING_SUCCESSFUL = 0  # Ping command returns 0 if successful
ROUTER_INT_IP = '222.222.1.1'
HOST_INT_IP = '222.222.1.2'


class PingTest(unittest.TestCase):

    def test_host_ping_ipv4(self):
        self.assertEqual(PING_SUCCESSFUL, os.system("ping -c 1 " + HOST_INT_IP))

    def test_router_ping_ipv4(self):
        self.assertEqual(PING_SUCCESSFUL, os.system("ping -c 1 " + ROUTER_INT_IP))


if __name__ == '__main__':
    unittest.main()
