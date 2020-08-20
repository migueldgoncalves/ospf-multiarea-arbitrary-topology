import unittest

import lsa.extension_abr as extension_abr
import conf.conf as conf

'''
This class tests the ABR-LSA body class of the OSPF extension and its operations
'''


#  Full successful run - Instant
class TestExtensionAbr(unittest.TestCase):

    body_bytes_1 = b'\x00\x00\x00\x0a\x01\x01\x01\x01'
    body_bytes_2 = b'\x00\x00\x00\x0a\x01\x01\x01\x01\x00\x00\x00\x0f\x02\x02\x02\x02'
    body_bytes_3 = b'\x00\x00\x00\x0a\x01\x01\x01\x01\x00\x00\x00\x0f\x02\x02\x02\x02\x00\x00\x00\x14\x03\x03\x03\x03'
    body_bytes_4 = b'\x00\x00\x00\x0a\x01\x01\x01\x01\x00\x00\x00\x0f\x02\x02\x02\x02\x00\x00\x00\x14\x03\x03\x03\x03' \
                   b'\x00\x00\x00\x00\x04\x04\x04\x04'

    #  Successful run - Instant
    def test_add_abr_info_successful(self):
        lsa_body = extension_abr.ExtensionAbr()
        self.assertEqual(0, len(lsa_body.abr_list))
        lsa_body.add_abr_info(0, '1.1.1.1')
        self.assertEqual(1, len(lsa_body.abr_list))
        self.assertEqual([[0, '1.1.1.1']], lsa_body.abr_list)
        lsa_body.add_abr_info(10, '1.1.1.1')
        self.assertEqual(1, len(lsa_body.abr_list))
        self.assertEqual([[0, '1.1.1.1']], lsa_body.abr_list)
        lsa_body.add_abr_info(conf.MAX_VALUE_24_BITS, '2.2.2.2')
        self.assertEqual(2, len(lsa_body.abr_list))
        self.assertEqual([[0, '1.1.1.1'], [conf.MAX_VALUE_24_BITS, '2.2.2.2']], lsa_body.abr_list)

    #  Successful run - Instant
    def test_add_abr_info_invalid_parameters(self):
        lsa_body = extension_abr.ExtensionAbr()
        with self.assertRaises(ValueError):
            lsa_body.add_abr_info(-1, '1.1.1.1')
        with self.assertRaises(ValueError):
            lsa_body.add_abr_info(conf.MAX_VALUE_24_BITS + 1, '1.1.1.1')
        with self.assertRaises(ValueError):
            lsa_body.add_abr_info(1, '')
        with self.assertRaises(ValueError):
            lsa_body.add_abr_info(1, '2001:db8:cafe:1::')

    #  Successful run - Instant
    def test_has_abr_info(self):
        lsa_body = extension_abr.ExtensionAbr()
        self.assertFalse(lsa_body.has_abr_info('1.1.1.1'))
        self.assertFalse(lsa_body.has_abr_info('2.2.2.2'))
        lsa_body.add_abr_info(10, '1.1.1.1')
        self.assertTrue(lsa_body.has_abr_info('1.1.1.1'))
        self.assertFalse(lsa_body.has_abr_info('2.2.2.2'))
        lsa_body.add_abr_info(20, '2.2.2.2')
        self.assertTrue(lsa_body.has_abr_info('1.1.1.1'))
        self.assertTrue(lsa_body.has_abr_info('2.2.2.2'))
        lsa_body.delete_abr_info('1.1.1.1')
        self.assertFalse(lsa_body.has_abr_info('1.1.1.1'))
        self.assertTrue(lsa_body.has_abr_info('2.2.2.2'))
        lsa_body.delete_abr_info('2.2.2.2')
        self.assertFalse(lsa_body.has_abr_info('1.1.1.1'))
        self.assertFalse(lsa_body.has_abr_info('2.2.2.2'))

    #  Successful run - Instant
    def test_get_abr_info(self):
        lsa_body = extension_abr.ExtensionAbr()
        self.assertIsNone(lsa_body.get_abr_info('1.1.1.1'))
        self.assertIsNone(lsa_body.get_abr_info('2.2.2.2'))
        lsa_body.add_abr_info(10, '1.1.1.1')
        self.assertIsNotNone(lsa_body.get_abr_info('1.1.1.1'))
        self.assertEqual([10, '1.1.1.1'], lsa_body.get_abr_info('1.1.1.1'))
        self.assertIsNone(lsa_body.get_abr_info('2.2.2.2'))
        lsa_body.add_abr_info(100, '2.2.2.2')
        self.assertIsNotNone(lsa_body.get_abr_info('1.1.1.1'))
        self.assertEqual([10, '1.1.1.1'], lsa_body.get_abr_info('1.1.1.1'))
        self.assertIsNotNone(lsa_body.get_abr_info('2.2.2.2'))
        self.assertEqual([100, '2.2.2.2'], lsa_body.get_abr_info('2.2.2.2'))

    #  Successful run - Instant
    def test_delete_abr_info(self):
        lsa_body = extension_abr.ExtensionAbr()
        lsa_body.add_abr_info(10, '1.1.1.1')
        lsa_body.add_abr_info(200, '2.2.2.2')
        lsa_body.delete_abr_info('3.3.3.3')
        self.assertEqual([[10, '1.1.1.1'], [200, '2.2.2.2']], lsa_body.abr_list)
        lsa_body.delete_abr_info('1.1.1.1')
        self.assertEqual([[200, '2.2.2.2']], lsa_body.abr_list)
        lsa_body.delete_abr_info('1.1.1.1')
        self.assertEqual([[200, '2.2.2.2']], lsa_body.abr_list)
        lsa_body.delete_abr_info('2.2.2.2')
        self.assertEqual([], lsa_body.abr_list)

    #  Successful run - Instant
    def test_pack_body(self):
        lsa_body = extension_abr.ExtensionAbr()
        lsa_body.add_abr_info(10, '1.1.1.1')
        self.assertEqual(TestExtensionAbr.body_bytes_1, lsa_body.pack_lsa_body())
        lsa_body.add_abr_info(15, '2.2.2.2')
        self.assertEqual(TestExtensionAbr.body_bytes_2, lsa_body.pack_lsa_body())
        lsa_body.add_abr_info(20, '3.3.3.3')
        self.assertEqual(TestExtensionAbr.body_bytes_3, lsa_body.pack_lsa_body())
        lsa_body.add_abr_info(0, '4.4.4.4')
        self.assertEqual(TestExtensionAbr.body_bytes_4, lsa_body.pack_lsa_body())

    #  Successful run - Instant
    def test_unpack_body(self):
        unpacked_body = extension_abr.ExtensionAbr.unpack_lsa_body(TestExtensionAbr.body_bytes_1, 0)
        self.assertEqual([[10, '1.1.1.1']], unpacked_body.abr_list)
        unpacked_body = extension_abr.ExtensionAbr.unpack_lsa_body(TestExtensionAbr.body_bytes_2, 0)
        self.assertEqual([[10, '1.1.1.1'], [15, '2.2.2.2']], unpacked_body.abr_list)
        unpacked_body = extension_abr.ExtensionAbr.unpack_lsa_body(TestExtensionAbr.body_bytes_3, 0)
        self.assertEqual([[10, '1.1.1.1'], [15, '2.2.2.2'], [20, '3.3.3.3']], unpacked_body.abr_list)
        unpacked_body = extension_abr.ExtensionAbr.unpack_lsa_body(TestExtensionAbr.body_bytes_4, 0)
        self.assertEqual([[10, '1.1.1.1'], [15, '2.2.2.2'], [20, '3.3.3.3'], [0, '4.4.4.4']], unpacked_body.abr_list)
