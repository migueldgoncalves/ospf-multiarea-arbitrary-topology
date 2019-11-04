import unittest

import general.utils as utils

'''
This class tests utility functions used throughout the router code
'''


#  Full successful run - Instant
class UtilsTest(unittest.TestCase):

    utils = utils.Utils()

    #  Successful run - Instant
    def test_ip_to_decimal_successful(self):
        self.assertEqual(0, self.utils.ipv4_to_decimal('0.0.0.0'))
        self.assertEqual(1, self.utils.ipv4_to_decimal('0.0.0.1'))
        self.assertEqual(255, self.utils.ipv4_to_decimal('0.0.0.255'))
        self.assertEqual(256, self.utils.ipv4_to_decimal('0.0.1.0'))
        self.assertEqual(65535, self.utils.ipv4_to_decimal('0.0.255.255'))
        self.assertEqual(65536, self.utils.ipv4_to_decimal('0.1.0.0'))
        self.assertEqual(65536, self.utils.ipv4_to_decimal('0.1.0.0'))
        self.assertEqual(16777215, self.utils.ipv4_to_decimal('0.255.255.255'))
        self.assertEqual(16777216, self.utils.ipv4_to_decimal('1.0.0.0'))
        self.assertEqual(4294967295, self.utils.ipv4_to_decimal('255.255.255.255'))

    #  Successful run - Instant
    def test_ip_to_decimal_invalid_ip(self):
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

    #  Successful run - Instant
    def test_create_checksum_ipv4_successful(self):
        packet = b'\x02\x01\x000\x03\x03\x03\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff' \
                 b'\xff\xff\x00\x00\n\x00\x00\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01'
        checksum = self.utils.create_checksum_ipv4(packet)
        self.assertEqual(63123, checksum)
