import unittest

import lsa.extension_prefix as extension_prefix
import conf.conf as conf

'''
This class tests the Prefix-LSA body class of the OSPF extension and its operations
'''


#  Full successful run - Instant
class TestExtensionPrefix(unittest.TestCase):

    body_bytes_v2_1 = b'\x00\x00\x00\x0a\xff\xff\xff\x00\xde\xde\x01\x00'
    body_bytes_v2_2 = b'\x00\x00\x00\x0a\xff\xff\xff\x00\xde\xde\x01\x00\x00\x00\x00\x14\xff\xff\x00\x00\xde\x01\x00' \
                      b'\x00'
    body_bytes_v2_3 = b'\x00\x00\x00\x0a\xff\xff\xff\x00\xde\xde\x01\x00\x00\x00\x00\x14\xff\xff\x00\x00\xde\x01\x00' \
                      b'\x00\x00\x00\x00\x1e\xff\x00\x00\x00\x01\x00\x00\x00'
    body_bytes_v2_4 = b'\x00\x00\x00\x0a\xff\xff\xff\x00\xde\xde\x01\x00\x00\x00\x00\x14\xff\xff\x00\x00\xde\x01\x00' \
                      b'\x00\x00\x00\x00\x1e\xff\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x28\x00\x00\x00\x00\x00\x00' \
                      b'\x00\x00'
    body_bytes_v3_1 = b'\x00\x00\x00\x01\x00\x00\x00\x0a\x00\x00\x00\x00'
    body_bytes_v3_2 = b'\x00\x00\x00\x02\x00\x00\x00\x0a\x00\x00\x00\x00\x00\x00\x00\x14\x20\x00\x00\x00\x20\x01\x0d' \
                      b'\xb8'
    body_bytes_v3_3 = b'\x00\x00\x00\x03\x00\x00\x00\x0a\x00\x00\x00\x00\x00\x00\x00\x14\x20\x00\x00\x00\x20\x01\x0d' \
                      b'\xb8\x00\x00\x00\x1e\x40\x00\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01'
    body_bytes_v3_4 = b'\x00\x00\x00\x04\x00\x00\x00\x0a\x00\x00\x00\x00\x00\x00\x00\x14\x20\x00\x00\x00\x20\x01\x0d' \
                      b'\xb8\x00\x00\x00\x1e\x40\x00\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x28\x60\x00' \
                      b'\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x00'
    body_bytes_v3_5 = b'\x00\x00\x00\x05\x00\x00\x00\x0a\x00\x00\x00\x00\x00\x00\x00\x14\x20\x00\x00\x00\x20\x01\x0d' \
                      b'\xb8\x00\x00\x00\x1e\x40\x00\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x28\x60\x00' \
                      b'\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x00\x00\x00\x00\x32\x80\x00\x00\x00\x20' \
                      b'\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00'

    #  Successful run - Instant
    def test_add_subnet_info_successful(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV4)
        self.assertEqual(0, len(lsa_body.subnet_list))
        lsa_body.add_subnet_info(0, '0.0.0.0', '255.255.255.255')
        self.assertEqual(1, len(lsa_body.subnet_list))
        self.assertEqual([[0, '0.0.0.0', '255.255.255.255']], lsa_body.subnet_list)
        lsa_body.add_subnet_info(conf.MAX_VALUE_24_BITS, '0.0.0.0', '255.255.255.255')
        self.assertEqual(1, len(lsa_body.subnet_list))
        self.assertEqual([[0, '0.0.0.0', '255.255.255.255']], lsa_body.subnet_list)
        lsa_body.add_subnet_info(conf.MAX_VALUE_24_BITS, '255.255.255.255', '0.0.0.0')
        self.assertEqual(2, len(lsa_body.subnet_list))
        self.assertEqual([[0, '0.0.0.0', '255.255.255.255'], [conf.MAX_VALUE_24_BITS, '255.255.255.255', '0.0.0.0']],
                         lsa_body.subnet_list)

    #  Successful run - Instant
    def test_add_subnet_info_invalid_parameters(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            lsa_body.add_subnet_info(-1, '0.0.0.0', '0.0.0.0')
        with self.assertRaises(ValueError):
            lsa_body.add_subnet_info(conf.MAX_VALUE_24_BITS + 1, '0.0.0.0', '0.0.0.0')
        with self.assertRaises(ValueError):
            lsa_body.add_subnet_info(0, '', '0.0.0.0')
        with self.assertRaises(ValueError):
            lsa_body.add_subnet_info(0, '2001:db8:cafe:1::', '0.0.0.0')
        with self.assertRaises(ValueError):
            lsa_body.add_subnet_info(0, '0.0.0.0', '')
        with self.assertRaises(ValueError):
            lsa_body.add_subnet_info(0, '0.0.0.0', '2001:db8:cafe:1::')

    #  Successful run - Instant
    def test_add_prefix_info_successful(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV6)
        self.assertEqual(0, len(lsa_body.prefix_list))
        lsa_body.add_prefix_info(0, 0, 0, '::')
        self.assertEqual(1, len(lsa_body.prefix_list))
        self.assertEqual([[0, 0, 0, '::']], lsa_body.prefix_list)
        lsa_body.add_prefix_info(conf.MAX_VALUE_24_BITS, 0, conf.MAX_VALUE_8_BITS, '::')
        self.assertEqual(1, len(lsa_body.prefix_list))
        self.assertEqual([[0, 0, 0, '::']], lsa_body.prefix_list)
        lsa_body.add_prefix_info(conf.MAX_VALUE_24_BITS, 16 * conf.BYTE_SIZE, conf.MAX_VALUE_8_BITS,
                                 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff')
        self.assertEqual(2, len(lsa_body.prefix_list))
        self.assertEqual([[0, 0, 0, '::'], [conf.MAX_VALUE_24_BITS, 16 * conf.BYTE_SIZE, conf.MAX_VALUE_8_BITS,
                                            'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff']], lsa_body.prefix_list)

    #  Successful run - Instant
    def test_add_prefix_info_invalid_parameters(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV6)
        with self.assertRaises(ValueError):
            lsa_body.add_prefix_info(-1, 0, 0, '::')
        with self.assertRaises(ValueError):
            lsa_body.add_prefix_info(conf.MAX_VALUE_24_BITS + 1, 0, 0, '::')
        with self.assertRaises(ValueError):
            lsa_body.add_prefix_info(0, -1, 0, '::')
        with self.assertRaises(ValueError):
            lsa_body.add_prefix_info(0, 16 * conf.BYTE_SIZE + 1, 0, '::')
        with self.assertRaises(ValueError):
            lsa_body.add_prefix_info(0, 0, -1, '::')
        with self.assertRaises(ValueError):
            lsa_body.add_prefix_info(0, 0, conf.MAX_VALUE_8_BITS + 1, '::')
        with self.assertRaises(ValueError):
            lsa_body.add_prefix_info(0, 0, 0, '')
        with self.assertRaises(ValueError):
            lsa_body.add_prefix_info(0, 0, 0, '0.0.0.0')

    #  Successful run - Instant
    def test_has_subnet_info(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV4)
        self.assertFalse(lsa_body.has_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertFalse(lsa_body.has_subnet_info('255.255.0.0', '111.111.2.0'))
        lsa_body.add_subnet_info(10, '255.255.255.0', '222.222.1.0')
        self.assertTrue(lsa_body.has_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertFalse(lsa_body.has_subnet_info('255.255.0.0', '111.111.2.0'))
        lsa_body.add_subnet_info(10, '255.255.0.0', '111.111.2.0')
        self.assertTrue(lsa_body.has_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertTrue(lsa_body.has_subnet_info('255.255.0.0', '111.111.2.0'))
        lsa_body.delete_subnet_info('255.255.255.0', '222.222.1.0')
        self.assertFalse(lsa_body.has_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertTrue(lsa_body.has_subnet_info('255.255.0.0', '111.111.2.0'))
        lsa_body.delete_subnet_info('255.255.0.0', '111.111.2.0')
        self.assertFalse(lsa_body.has_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertFalse(lsa_body.has_subnet_info('255.255.0.0', '111.111.2.0'))

    #  Successful run - Instant
    def test_has_prefix_info(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV6)
        self.assertFalse(lsa_body.has_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertFalse(lsa_body.has_prefix_info(32, '2001:db8::'))
        lsa_body.add_prefix_info(10, 64, 0, '2001:db8:cafe:1::')
        self.assertTrue(lsa_body.has_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertFalse(lsa_body.has_prefix_info(32, '2001:db8::'))
        lsa_body.add_prefix_info(10, 32, 0, '2001:db8::')
        self.assertTrue(lsa_body.has_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertTrue(lsa_body.has_prefix_info(32, '2001:db8::'))
        lsa_body.delete_prefix_info(64, '2001:db8:cafe:1::')
        self.assertFalse(lsa_body.has_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertTrue(lsa_body.has_prefix_info(32, '2001:db8::'))
        lsa_body.delete_prefix_info(32, '2001:db8::')
        self.assertFalse(lsa_body.has_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertFalse(lsa_body.has_prefix_info(32, '2001:db8::'))

    #  Successful run - Instant
    def test_get_subnet_info(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV4)
        self.assertIsNone(lsa_body.get_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertIsNone(lsa_body.get_subnet_info('255.255.0.0', '111.111.2.0'))
        lsa_body.add_subnet_info(10, '255.255.255.0', '222.222.1.0')
        self.assertEqual([10, '255.255.255.0', '222.222.1.0'], lsa_body.get_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertIsNone(lsa_body.get_subnet_info('255.255.0.0', '111.111.2.0'))
        lsa_body.add_subnet_info(10, '255.255.0.0', '111.111.2.0')
        self.assertEqual([10, '255.255.255.0', '222.222.1.0'], lsa_body.get_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertEqual([10, '255.255.0.0', '111.111.2.0'], lsa_body.get_subnet_info('255.255.0.0', '111.111.2.0'))
        lsa_body.delete_subnet_info('255.255.255.0', '222.222.1.0')
        self.assertIsNone(lsa_body.get_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertEqual([10, '255.255.0.0', '111.111.2.0'], lsa_body.get_subnet_info('255.255.0.0', '111.111.2.0'))
        lsa_body.delete_subnet_info('255.255.0.0', '111.111.2.0')
        self.assertIsNone(lsa_body.get_subnet_info('255.255.255.0', '222.222.1.0'))
        self.assertIsNone(lsa_body.get_subnet_info('255.255.0.0', '111.111.2.0'))

    #  Successful run - Instant
    def test_get_prefix_info(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV6)
        self.assertIsNone(lsa_body.get_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertIsNone(lsa_body.get_prefix_info(32, '2001:db8::'))
        lsa_body.add_prefix_info(10, 64, 0, '2001:db8:cafe:1::')
        self.assertEqual([10, 64, 0, '2001:db8:cafe:1::'], lsa_body.get_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertIsNone(lsa_body.get_prefix_info(32, '2001:db8::'))
        lsa_body.add_prefix_info(10, 32, 0, '2001:db8::')
        self.assertEqual([10, 64, 0, '2001:db8:cafe:1::'], lsa_body.get_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertEqual([10, 32, 0, '2001:db8::'], lsa_body.get_prefix_info(32, '2001:db8::'))
        lsa_body.delete_prefix_info(64, '2001:db8:cafe:1::')
        self.assertIsNone(lsa_body.get_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertEqual([10, 32, 0, '2001:db8::'], lsa_body.get_prefix_info(32, '2001:db8::'))
        lsa_body.delete_prefix_info(32, '2001:db8::')
        self.assertIsNone(lsa_body.get_prefix_info(64, '2001:db8:cafe:1::'))
        self.assertIsNone(lsa_body.get_prefix_info(32, '2001:db8::'))

    #  Successful run - Instant
    def test_delete_subnet_info(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV4)
        lsa_body.delete_subnet_info('255.255.255.0', '222.222.1.0')
        self.assertEqual(0, len(lsa_body.subnet_list))
        lsa_body.add_subnet_info(10, '255.255.255.0', '222.222.1.0')
        lsa_body.add_subnet_info(10, '255.255.0.0', '111.111.2.0')
        lsa_body.delete_subnet_info('255.255.255.0', '222.222.1.0')
        self.assertEqual(1, len(lsa_body.subnet_list))
        self.assertEqual([[10, '255.255.0.0', '111.111.2.0']], lsa_body.subnet_list)
        lsa_body.delete_subnet_info('255.255.255.0', '222.222.1.0')
        self.assertEqual(1, len(lsa_body.subnet_list))
        self.assertEqual([[10, '255.255.0.0', '111.111.2.0']], lsa_body.subnet_list)
        lsa_body.delete_subnet_info('255.255.0.0', '111.111.2.0')
        self.assertEqual(0, len(lsa_body.subnet_list))

    #  Successful run - Instant
    def test_delete_prefix_info(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV6)
        lsa_body.delete_prefix_info(64, '2001:db8:cafe:1::')
        self.assertEqual(0, len(lsa_body.prefix_list))
        lsa_body.add_prefix_info(10, 64, 0, '2001:db8:cafe:1::')
        lsa_body.add_prefix_info(10, 32, 0, '2001:db8::')
        lsa_body.delete_prefix_info(64, '2001:db8:cafe:1::')
        self.assertEqual(1, len(lsa_body.prefix_list))
        self.assertEqual([[10, 32, 0, '2001:db8::']], lsa_body.prefix_list)
        lsa_body.delete_prefix_info(64, '2001:db8:cafe:1::')
        self.assertEqual(1, len(lsa_body.prefix_list))
        self.assertEqual([[10, 32, 0, '2001:db8::']], lsa_body.prefix_list)
        lsa_body.delete_prefix_info(32, '2001:db8::')
        self.assertEqual(0, len(lsa_body.prefix_list))

    #  Successful run - Instant
    def test_pack_body(self):
        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV4)
        lsa_body.add_subnet_info(10, '255.255.255.0', '222.222.1.0')
        self.assertEqual(TestExtensionPrefix.body_bytes_v2_1, lsa_body.pack_lsa_body())
        lsa_body.add_subnet_info(20, '255.255.0.0', '222.1.0.0')
        self.assertEqual(TestExtensionPrefix.body_bytes_v2_2, lsa_body.pack_lsa_body())
        lsa_body.add_subnet_info(30, '255.0.0.0', '1.0.0.0')
        self.assertEqual(TestExtensionPrefix.body_bytes_v2_3, lsa_body.pack_lsa_body())
        lsa_body.add_subnet_info(40, '0.0.0.0', '0.0.0.0')
        self.assertEqual(TestExtensionPrefix.body_bytes_v2_4, lsa_body.pack_lsa_body())

        lsa_body = extension_prefix.ExtensionPrefix(conf.VERSION_IPV6)
        lsa_body.add_prefix_info(10, 0, 0, '::')
        self.assertEqual(TestExtensionPrefix.body_bytes_v3_1, lsa_body.pack_lsa_body())
        lsa_body.add_prefix_info(20, 32, 0, '2001:db8::')
        self.assertEqual(TestExtensionPrefix.body_bytes_v3_2, lsa_body.pack_lsa_body())
        lsa_body.add_prefix_info(30, 64, 0, '2001:db8:cafe:1::')
        self.assertEqual(TestExtensionPrefix.body_bytes_v3_3, lsa_body.pack_lsa_body())
        lsa_body.add_prefix_info(40, 96, 0, '2001:db8:cafe:1::')
        self.assertEqual(TestExtensionPrefix.body_bytes_v3_4, lsa_body.pack_lsa_body())
        lsa_body.add_prefix_info(50, 128, 0, '2001:db8:cafe:1::')
        self.assertEqual(TestExtensionPrefix.body_bytes_v3_5, lsa_body.pack_lsa_body())

    #  Successful run - Instant
    def test_unpack_body(self):
        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v2_1, conf.VERSION_IPV4)
        self.assertEqual([[10, '255.255.255.0', '222.222.1.0']], unpacked_body.subnet_list)
        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v2_2, conf.VERSION_IPV4)
        self.assertEqual([[10, '255.255.255.0', '222.222.1.0'], [20, '255.255.0.0', '222.1.0.0']],
                         unpacked_body.subnet_list)
        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v2_3, conf.VERSION_IPV4)
        self.assertEqual([[10, '255.255.255.0', '222.222.1.0'], [20, '255.255.0.0', '222.1.0.0'],
                          [30, '255.0.0.0', '1.0.0.0']], unpacked_body.subnet_list)
        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v2_4, conf.VERSION_IPV4)
        self.assertEqual([[10, '255.255.255.0', '222.222.1.0'], [20, '255.255.0.0', '222.1.0.0'],
                          [30, '255.0.0.0', '1.0.0.0'], [40, '0.0.0.0', '0.0.0.0']], unpacked_body.subnet_list)

        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v3_1, conf.VERSION_IPV6)
        self.assertEqual(1, unpacked_body.prefix_number)
        self.assertEqual([[10, 0, 0, '::']], unpacked_body.prefix_list)
        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v3_2, conf.VERSION_IPV6)
        self.assertEqual(2, unpacked_body.prefix_number)
        self.assertEqual([[10, 0, 0, '::'], [20, 32, 0, '2001:db8::']], unpacked_body.prefix_list)
        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v3_3, conf.VERSION_IPV6)
        self.assertEqual(3, unpacked_body.prefix_number)
        self.assertEqual([[10, 0, 0, '::'], [20, 32, 0, '2001:db8::'], [30, 64, 0, '2001:db8:cafe:1::']],
                         unpacked_body.prefix_list)
        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v3_4, conf.VERSION_IPV6)
        self.assertEqual(4, unpacked_body.prefix_number)
        self.assertEqual([[10, 0, 0, '::'], [20, 32, 0, '2001:db8::'], [30, 64, 0, '2001:db8:cafe:1::'],
                          [40, 96, 0, '2001:db8:cafe:1::']], unpacked_body.prefix_list)
        unpacked_body = extension_prefix.ExtensionPrefix.unpack_lsa_body(
            TestExtensionPrefix.body_bytes_v3_5, conf.VERSION_IPV6)
        self.assertEqual(5, unpacked_body.prefix_number)
        self.assertEqual([[10, 0, 0, '::'], [20, 32, 0, '2001:db8::'], [30, 64, 0, '2001:db8:cafe:1::'],
                          [40, 96, 0, '2001:db8:cafe:1::'], [50, 128, 0, '2001:db8:cafe:1::']],
                         unpacked_body.prefix_list)
