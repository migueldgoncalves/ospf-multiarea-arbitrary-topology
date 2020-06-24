import unittest

import lsa.router as router
import conf.conf as conf

'''
This class tests the OSPF Hello-LSA body class and its operations
'''


#  Full successful run - Instant
class TestRouter(unittest.TestCase):

    #  Successful run - Instant
    def test_delete_interface_link_info(self):
        lsa_body = router.Router(False, False, False, 0, conf.VERSION_IPV4)
        lsa_body.add_link_info_v2('2.2.2.2', '222.222.6.1', 1, 0, 64)
        lsa_body.add_link_info_v2('222.222.6.0', '255.255.255.0', 3, 0, 64)
        lsa_body.add_link_info_v2('222.222.3.2', '222.222.3.1', 2, 0, 10)
        self.assertFalse(lsa_body.has_link_info_v2('2.2.2.2', '222.222.6.1', 1, 0, 10))
        self.assertTrue(lsa_body.has_link_info_v2('2.2.2.2', '222.222.6.1', 1, 0, 64))
        lsa_body.delete_interface_link_info('222.222.6.1', '222.222.6.0', 0)
        self.assertEqual(1, len(lsa_body.links))
        self.assertEqual('222.222.3.2', lsa_body.links[0][0])
        lsa_body.delete_interface_link_info('222.222.6.1', '222.222.6.0', 0)
        self.assertEqual(1, len(lsa_body.links))

        lsa_body = router.Router(False, False, False, 51, conf.VERSION_IPV6)
        lsa_body.add_link_info_v3(1, 64, 7, 6, '3.3.3.3')
        lsa_body.add_link_info_v3(3, 64, 7, 6, '4.4.4.4')
        lsa_body.add_link_info_v3(2, 10, 4, 5, '2.2.2.2')
        self.assertFalse(lsa_body.has_link_info_v3(2, 64, 7, 6, '3.3.3.3'))
        self.assertTrue(lsa_body.has_link_info_v3(1, 64, 7, 6, '3.3.3.3'))
        lsa_body.delete_interface_link_info('', '', 7)
        self.assertEqual(1, len(lsa_body.links))
        self.assertEqual(4, lsa_body.links[0][2])
        lsa_body.delete_interface_link_info('', '', 7)
        self.assertEqual(1, len(lsa_body.links))

    #  Successful run - Instant
    def test_delete_link_info(self):
        lsa_body = router.Router(False, False, False, 0, conf.VERSION_IPV4)
        lsa_body.add_link_info_v2('2.2.2.2', '222.222.6.1', 1, 0, 64)
        lsa_body.add_link_info_v2('222.222.6.0', '255.255.255.0', 3, 0, 64)
        lsa_body.delete_link_info_v2('2.2.2.2', '222.222.6.1', 1, 0, 64)
        self.assertEqual(1, len(lsa_body.links))
        self.assertEqual('222.222.6.0', lsa_body.links[0][0])
        lsa_body.delete_link_info_v2('2.2.2.2', '222.222.6.1', 1, 0, 64)
        self.assertEqual(1, len(lsa_body.links))

        lsa_body = router.Router(False, False, False, 51, conf.VERSION_IPV6)
        lsa_body.add_link_info_v3(1, 64, 7, 6, '3.3.3.3')
        lsa_body.add_link_info_v3(2, 10, 4, 5, '2.2.2.2')
        lsa_body.delete_link_info_v3(2, 10, 4, 5, '2.2.2.2')
        self.assertEqual(1, len(lsa_body.links))
        self.assertEqual(7, lsa_body.links[0][2])
        lsa_body.delete_link_info_v3(2, 10, 4, 5, '2.2.2.2')
        self.assertEqual(1, len(lsa_body.links))

    #  Successful run - Instant
    def test_pack_body(self):
        body_bytes = b'\x00\x00\x00\x03\x01\x01\x01\x01\xde\xde\x06\x02\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00' \
                     b'\x03\x00\x00@\xde\xde\x05\x02\xde\xde\x05\x02\x02\x00\x00\n'
        lsa_body = router.Router(False, False, False, 0, conf.VERSION_IPV4)
        lsa_body.add_link_info_v2('1.1.1.1', '222.222.6.2', 1, 0, 64)
        lsa_body.add_link_info_v2('222.222.6.0', '255.255.255.0', 3, 0, 64)
        lsa_body.add_link_info_v2('222.222.5.2', '222.222.5.2', 2, 0, 10)
        self.assertEqual(body_bytes, lsa_body.pack_lsa_body())

        body_bytes = b'\x00\x00\x00\x33\x01\x00\x00\x40\x00\x00\x00\x07\x00\x00\x00\x06\x03\x03\x03\x03\x02\x00\x00' \
                     b'\x0a\x00\x00\x00\x04\x00\x00\x00\x05\x02\x02\x02\x02'
        lsa_body = router.Router(False, False, False, 51, conf.VERSION_IPV6)
        lsa_body.add_link_info_v3(1, 64, 7, 6, '3.3.3.3')
        lsa_body.add_link_info_v3(2, 10, 4, 5, '2.2.2.2')
        self.assertEqual(body_bytes, lsa_body.pack_lsa_body())

    #  Successful run - Instant
    def test_unpack_body(self):
        body_bytes = b'\x00\x00\x00\x03\x01\x01\x01\x01\xde\xde\x06\x02\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00' \
                     b'\x03\x00\x00@\xde\xde\x05\x02\xde\xde\x05\x02\x02\x00\x00\n'
        lsa_body = router.Router.unpack_lsa_body(body_bytes, conf.VERSION_IPV4)
        self.assertFalse(lsa_body.bit_v)
        self.assertFalse(lsa_body.bit_e)
        self.assertFalse(lsa_body.bit_b)
        self.assertEqual(3, lsa_body.link_number)
        self.assertEqual([['1.1.1.1', '222.222.6.2', 1, 0, 64], ['222.222.6.0', '255.255.255.0', 3, 0, 64],
                          ['222.222.5.2', '222.222.5.2', 2, 0, 10]], lsa_body.links)

        body_bytes = b'\x00\x00\x00\x33\x01\x00\x00\x40\x00\x00\x00\x07\x00\x00\x00\x06\x03\x03\x03\x03\x02\x00\x00' \
                     b'\x0a\x00\x00\x00\x04\x00\x00\x00\x05\x02\x02\x02\x02'
        lsa_body = router.Router.unpack_lsa_body(body_bytes, conf.VERSION_IPV6)
        self.assertFalse(lsa_body.bit_v)
        self.assertFalse(lsa_body.bit_e)
        self.assertFalse(lsa_body.bit_b)
        self.assertEqual(51, lsa_body.options)
        self.assertEqual([[1, 64, 7, 6, '3.3.3.3'], [2, 10, 4, 5, '2.2.2.2']], lsa_body.links)
