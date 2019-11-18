import unittest

import general.utils as utils
import conf.conf as conf

'''
This class tests utility functions used throughout the router code
'''

INTERFACE_NAME = 'ens33'
INTERFACE_IP = '222.222.1.2'  # Must be changed if IP address of interface is changed for tests to pass
NETWORK_MASK = '255.255.255.0'  # Must be changed if network mask of interface is changed for tests to pass


#  Full successful run - Instant
class UtilsTest(unittest.TestCase):

    utils = utils.Utils()

    #  Successful run - Instant
    def test_ipv4_to_decimal_successful(self):
        self.assertEqual(0, self.utils.ipv4_to_decimal('0.0.0.0'))
        self.assertEqual(1, self.utils.ipv4_to_decimal('0.0.0.1'))
        self.assertEqual(255, self.utils.ipv4_to_decimal('0.0.0.255'))
        self.assertEqual(256, self.utils.ipv4_to_decimal('0.0.1.0'))
        self.assertEqual(65535, self.utils.ipv4_to_decimal('0.0.255.255'))
        self.assertEqual(65536, self.utils.ipv4_to_decimal('0.1.0.0'))
        self.assertEqual(16777215, self.utils.ipv4_to_decimal('0.255.255.255'))
        self.assertEqual(16777216, self.utils.ipv4_to_decimal('1.0.0.0'))
        self.assertEqual(4294967295, self.utils.ipv4_to_decimal('255.255.255.255'))

    #  Successful run - Instant
    def test_ipv4_to_decimal_invalid_ip(self):
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('        ')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('An invalid IP address')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('0')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('0.')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('0.0.0')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('0.0.0.')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('0.0.0.0.')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('0.0.0.0.0')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('-1.-1.-1.-1')
        with self.assertRaises(ValueError):
            self.utils.ipv4_to_decimal('256.256.256.256')

    #  Successful run - Instant
    def test_decimal_to_ipv4_successful(self):
        self.assertEqual('0.0.0.0', self.utils.decimal_to_ipv4(0))
        self.assertEqual('0.0.0.1', self.utils.decimal_to_ipv4(1))
        self.assertEqual('0.0.0.255', self.utils.decimal_to_ipv4(255))
        self.assertEqual('0.0.1.0', self.utils.decimal_to_ipv4(256))
        self.assertEqual('0.0.255.255', self.utils.decimal_to_ipv4(65535))
        self.assertEqual('0.1.0.0', self.utils.decimal_to_ipv4(65536))
        self.assertEqual('0.255.255.255', self.utils.decimal_to_ipv4(16777215))
        self.assertEqual('1.0.0.0', self.utils.decimal_to_ipv4(16777216))
        self.assertEqual('255.255.255.255', self.utils.decimal_to_ipv4(4294967295))

    #  Successful run - Instant
    def test_decimal_to_ipv4_invalid_decimal(self):
        with self.assertRaises(ValueError):
            self.utils.decimal_to_ipv4(-1)
        with self.assertRaises(ValueError):
            self.utils.decimal_to_ipv4(conf.MAX_VALUE_32_BITS + 1)

    #  Successful run - Instant
    def test_create_checksum_ipv4_successful(self):
        packet = b'\x02\x01\x000\x03\x03\x03\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff' \
                 b'\xff\xff\x00\x00\n\x00\x00\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01'
        checksum = self.utils.create_checksum_ipv4(packet)
        self.assertEqual(63123, checksum)

    #  Successful run - Instant
    def test_get_ipv4_address_from_interface_name(self):
        self.assertEqual(INTERFACE_IP, self.utils.get_ipv4_address_from_interface_name(INTERFACE_NAME))

    #  Successful run - Instant
    def test_get_ipv4_network_mask_from_interface_name(self):
        self.assertEqual(NETWORK_MASK, self.utils.get_ipv4_network_mask_from_interface_name(INTERFACE_NAME))

    #  Successful run - Instant
    def test_is_ipv4_address_successful(self):
        self.assertTrue(self.utils.is_ipv4_address('0.0.0.0'))
        self.assertTrue(self.utils.is_ipv4_address('0.0.0.1'))
        self.assertTrue(self.utils.is_ipv4_address('0.0.0.255'))
        self.assertTrue(self.utils.is_ipv4_address('0.0.1.0'))
        self.assertTrue(self.utils.is_ipv4_address('0.0.255.255'))
        self.assertTrue(self.utils.is_ipv4_address('0.1.0.0'))
        self.assertTrue(self.utils.is_ipv4_address('0.1.0.0'))
        self.assertTrue(self.utils.is_ipv4_address('0.255.255.255'))
        self.assertTrue(self.utils.is_ipv4_address('1.0.0.0'))
        self.assertTrue(self.utils.is_ipv4_address('255.255.255.255'))

    #  Successful run - Instant
    def test_is_ipv4_address_invalid_ip(self):
        self.assertFalse(self.utils.is_ipv4_address(''))
        self.assertFalse(self.utils.is_ipv4_address('        '))
        self.assertFalse(self.utils.is_ipv4_address('An invalid IP address'))
        self.assertFalse(self.utils.is_ipv4_address('0'))
        self.assertFalse(self.utils.is_ipv4_address('0.'))
        self.assertFalse(self.utils.is_ipv4_address('0.0.0'))
        self.assertFalse(self.utils.is_ipv4_address('0.0.0.'))
        self.assertFalse(self.utils.is_ipv4_address('0.0.0.0.'))
        self.assertFalse(self.utils.is_ipv4_address('0.0.0.0.0'))

    #  Successful run - Instant
    def test_is_ipv4_network_mask_successful(self):
        self.assertTrue(self.utils.is_ipv4_network_mask('0.0.0.0'))
        self.assertTrue(self.utils.is_ipv4_network_mask('128.0.0.0'))
        self.assertTrue(self.utils.is_ipv4_network_mask('255.0.0.0'))
        self.assertTrue(self.utils.is_ipv4_network_mask('255.255.0.0'))
        self.assertTrue(self.utils.is_ipv4_network_mask('255.255.255.0'))
        self.assertTrue(self.utils.is_ipv4_network_mask('255.255.255.254'))
        self.assertTrue(self.utils.is_ipv4_network_mask('255.255.255.255'))

    #  Successful run - Instant
    def test_is_ipv4_network_mask_invalid_mask(self):
        self.assertFalse(self.utils.is_ipv4_network_mask(''))
        self.assertFalse(self.utils.is_ipv4_network_mask('An invalid IP address'))
        self.assertFalse(self.utils.is_ipv4_network_mask('127.0.0.1'))
        self.assertFalse(self.utils.is_ipv4_network_mask('0.0.0.1'))
        self.assertFalse(self.utils.is_ipv4_network_mask('255.255.255.253'))
        self.assertFalse(self.utils.is_ipv4_network_mask('255.255.255.64'))
        self.assertFalse(self.utils.is_ipv4_network_mask('255.255.64.0'))
        self.assertFalse(self.utils.is_ipv4_network_mask('255.64.0.0'))
        self.assertFalse(self.utils.is_ipv4_network_mask('64.0.0.0'))
