import unittest

import lsa.network as network
import conf.conf as conf

'''
This class tests the OSPF Network-LSA body class and its operations
'''


#  Full successful run - Instant
class TestNetwork(unittest.TestCase):

    #  Successful run - Instant
    def test_pack_body(self):
        body_bytes = b'\xff\xff\xff\x00\x02\x02\x02\x02\x01\x01\x01\x01'
        self.assertEqual(
            body_bytes, network.Network('255.255.255.0', 0, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV4).pack_lsa_body())

        body_bytes = b'\x00\x00\x003\x02\x02\x02\x02\x01\x01\x01\x01'
        self.assertEqual(
            body_bytes, network.Network('', 51, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV6).pack_lsa_body())

    #  Successful run - Instant
    def test_unpack_body(self):
        body_bytes = b'\xff\xff\xff\x00\x02\x02\x02\x02\x01\x01\x01\x01'
        unpacked_body = network.Network.unpack_lsa_body(body_bytes, conf.VERSION_IPV4)
        self.assertEqual('255.255.255.0', unpacked_body.network_mask)
        self.assertEqual(['2.2.2.2', '1.1.1.1'], unpacked_body.attached_routers)

        body_bytes = b'\x00\x00\x003\x02\x02\x02\x02\x01\x01\x01\x01'
        unpacked_body = network.Network.unpack_lsa_body(body_bytes, conf.VERSION_IPV6)
        self.assertEqual(51, unpacked_body.options)
        self.assertEqual(['2.2.2.2', '1.1.1.1'], unpacked_body.attached_routers)
