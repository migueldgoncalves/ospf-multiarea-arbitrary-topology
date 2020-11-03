import unittest

import general.utils as utils
import conf.conf as conf

'''
This class tests utility functions used throughout the router code
'''

INTERFACE_NAME = conf.INTERFACE_NAMES[0]
INTERFACE_IPV4 = '222.222.1.2'  # Must be changed if IPv4 address of interface is changed for tests to pass
INTERFACE_IPV6 = '2001:db8:cafe:1::2'  # Must be changed if IPv6 address of interface is changed for tests to pass
NETWORK_MASK_IPV4 = '255.255.255.0'  # Must be changed if IPv4 network mask of interface is changed for tests to pass
NETWORK_MASK_IPV6 = 'ffff:ffff:ffff:ffff::'  # Must be changed if IPv6 network mask of interface is changed
PREFIX_IPV4 = '222.222.1.0'  # Must be changed if IPv4 network prefix of interface is changed
PREFIX_IPV4_LENGTH = 24  # Must be changed if length of IPv4 network prefix of interface is changed
PREFIX_IPV6 = '2001:db8:cafe:1::'  # Must be changed if IPv6 network prefix of interface is changed
PREFIX_IPV6_LENGTH = 64  # Must be changed if length of IPv6 network prefix of interface is changed


#  Full successful run - Instant
class UtilsTest(unittest.TestCase):

    #  Successful run - Instant
    def test_ipv4_to_decimal_successful(self):
        self.assertEqual(0, utils.Utils.ipv4_to_decimal('0.0.0.0'))
        self.assertEqual(1, utils.Utils.ipv4_to_decimal('0.0.0.1'))
        self.assertEqual(255, utils.Utils.ipv4_to_decimal('0.0.0.255'))
        self.assertEqual(256, utils.Utils.ipv4_to_decimal('0.0.1.0'))
        self.assertEqual(65535, utils.Utils.ipv4_to_decimal('0.0.255.255'))
        self.assertEqual(65536, utils.Utils.ipv4_to_decimal('0.1.0.0'))
        self.assertEqual(16777215, utils.Utils.ipv4_to_decimal('0.255.255.255'))
        self.assertEqual(16777216, utils.Utils.ipv4_to_decimal('1.0.0.0'))
        self.assertEqual(4294967295, utils.Utils.ipv4_to_decimal('255.255.255.255'))
        self.assertEqual(0, utils.Utils.ipv4_to_decimal(0))
        self.assertEqual(4294967295, utils.Utils.ipv4_to_decimal(4294967295))

    #  Successful run - Instant
    def test_ipv4_to_decimal_invalid_ip(self):
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('        ')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('An invalid IP address')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('0')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('0.')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('0.0.0')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('0.0.0.')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('0.0.0.0.')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('0.0.0.0.0')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('-1.-1.-1.-1')
        with self.assertRaises(ValueError):
            utils.Utils.ipv4_to_decimal('256.256.256.256')

    #  Successful run - Instant
    def test_decimal_to_ipv4_successful(self):
        self.assertEqual('0.0.0.0', utils.Utils.decimal_to_ipv4(0))
        self.assertEqual('0.0.0.1', utils.Utils.decimal_to_ipv4(1))
        self.assertEqual('0.0.0.255', utils.Utils.decimal_to_ipv4(255))
        self.assertEqual('0.0.1.0', utils.Utils.decimal_to_ipv4(256))
        self.assertEqual('0.0.255.255', utils.Utils.decimal_to_ipv4(65535))
        self.assertEqual('0.1.0.0', utils.Utils.decimal_to_ipv4(65536))
        self.assertEqual('0.255.255.255', utils.Utils.decimal_to_ipv4(16777215))
        self.assertEqual('1.0.0.0', utils.Utils.decimal_to_ipv4(16777216))
        self.assertEqual('255.255.255.255', utils.Utils.decimal_to_ipv4(4294967295))
        self.assertEqual('0.0.0.1', utils.Utils.decimal_to_ipv4('1'))

    #  Successful run - Instant
    def test_decimal_to_ipv6_successful(self):
        self.assertEqual('::', utils.Utils.decimal_to_ipv6(0))
        self.assertEqual('::1', utils.Utils.decimal_to_ipv6(1))
        self.assertEqual('::ffff', utils.Utils.decimal_to_ipv6(65535))
        self.assertEqual('::1:0', utils.Utils.decimal_to_ipv6(65536))
        self.assertEqual('::ffff:ffff', utils.Utils.decimal_to_ipv6(4294967295))
        self.assertEqual('::1:0:0', utils.Utils.decimal_to_ipv6(4294967296))
        self.assertEqual('::ffff:ffff:ffff', utils.Utils.decimal_to_ipv6(281474976710655))
        self.assertEqual('::1:0:0:0', utils.Utils.decimal_to_ipv6(281474976710656))
        self.assertEqual('::ffff:ffff:ffff:ffff', utils.Utils.decimal_to_ipv6(18446744073709551615))
        self.assertEqual('0:0:0:1::', utils.Utils.decimal_to_ipv6(18446744073709551616))
        self.assertEqual('::ffff:ffff:ffff:ffff:ffff', utils.Utils.decimal_to_ipv6(1208925819614629174706175))
        self.assertEqual('0:0:1::', utils.Utils.decimal_to_ipv6(1208925819614629174706176))
        self.assertEqual('0:ffff:ffff:ffff:ffff:ffff:ffff:ffff',
                         utils.Utils.decimal_to_ipv6(5192296858534827628530496329220095))
        self.assertEqual('1::', utils.Utils.decimal_to_ipv6(5192296858534827628530496329220096))
        self.assertEqual('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',
                         utils.Utils.decimal_to_ipv6(340282366920938463463374607431768211455))
        self.assertEqual('::1', utils.Utils.decimal_to_ipv6('1'))

    #  Successful run - Instant
    def test_decimal_to_ipv4_invalid_decimal(self):
        with self.assertRaises(ValueError):
            utils.Utils.decimal_to_ipv4('Invalid address')
        with self.assertRaises(ValueError):
            utils.Utils.decimal_to_ipv4(-1)
        with self.assertRaises(ValueError):
            utils.Utils.decimal_to_ipv4(conf.MAX_VALUE_32_BITS + 1)

    #  Successful run - Instant
    def test_decimal_to_ipv6_invalid_decimal(self):
        with self.assertRaises(ValueError):
            utils.Utils.decimal_to_ipv6('Invalid address')
        with self.assertRaises(ValueError):
            utils.Utils.decimal_to_ipv6(-1)
        with self.assertRaises(ValueError):
            utils.Utils.decimal_to_ipv6(conf.MAX_VALUE_128_BITS + 1)

    #  Successful run - Instant
    def test_create_checksum_ospfv2_successful(self):
        self.assertEqual(65535, utils.Utils.create_checksum_ospfv2(b'\x00'))
        self.assertEqual(65535, utils.Utils.create_checksum_ospfv2(b'\x00\x00'))
        self.assertEqual(65279, utils.Utils.create_checksum_ospfv2(b'\x01\x00'))
        self.assertEqual(65534, utils.Utils.create_checksum_ospfv2(b'\x00\x01'))
        self.assertEqual(65535, utils.Utils.create_checksum_ospfv2(b'\x00\x00\x00'))
        self.assertEqual(65279, utils.Utils.create_checksum_ospfv2(b'\x01\x00\x00'))
        self.assertEqual(65534, utils.Utils.create_checksum_ospfv2(b'\x00\x01\x00'))
        self.assertEqual(65279, utils.Utils.create_checksum_ospfv2(b'\x00\x00\x01'))
        self.assertEqual(65279, utils.Utils.create_checksum_ospfv2(b'\x01\x00\x00\x00'))
        self.assertEqual(65534, utils.Utils.create_checksum_ospfv2(b'\x00\x01\x00\x00'))
        self.assertEqual(65279, utils.Utils.create_checksum_ospfv2(b'\x00\x00\x01\x00'))
        self.assertEqual(65534, utils.Utils.create_checksum_ospfv2(b'\x00\x00\x00\x01'))
        self.assertEqual(0, utils.Utils.create_checksum_ospfv2(b'\xff\xff\xff\xff'))
        self.assertEqual(63123, utils.Utils.create_checksum_ospfv2(
            b'\x02\x01\x000\x03\x03\x03\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff'
            b'\x00\x00\n\x00\x00\x00\x00\x00(\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01'))
        self.assertEqual(2749, utils.Utils.create_checksum_ospfv2(
            b'\x02\x01\x00,\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff'
            b'\x00\x00\n\x12\x01\x00\x00\x00(\xde\xde\x01\x01\x00\x00\x00\x00\xff\xf6\x00\x03\x00\x01\x00\x04\x00\x00'
            b'\x00\x01'))

    #  Successful run - Instant
    def test_create_checksum_ospfv3_successful(self):
        self.assertEqual(8768, utils.Utils.create_checksum_ospfv3(
            b'\x03\x01\x00$\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x01\x00\x00\x13\x00\n\x00('
            b'\x01\x01\x01\x01\x00\x00\x00\x00',
            'fe80::c001:18ff:fe34:10', 'ff02::5'))
        self.assertEqual(32756, utils.Utils.create_checksum_ospfv3(
            b'\x03\x04\x00\x3c\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01\x20\x01\x00\x00'
            b'\x00\x00\x01\x01\x01\x01\x80\x00\x00\xa6\xf1\x7d\x00\x28\x00\x00\x00\x02\x02\x00\x00\x0a\x00\x00\x00\x04'
            b'\x00\x00\x00\x02\x02\x02\x02\x02', 'fe80::20c:29ff:fe27:b810', 'ff02::5'))

    #  Successful run - Instant
    def test_create_fletcher_checksum_successful(self):
        byte_stream = b' \x01\x00\x00\x00\x00\x08\x08\x08\x08\x80\x00\x00\x01\x00\x00\x00(\x00\x00\x003\x02\x00\x00\n' \
                      b'\x00\x00\x00\x04\x00\x00\x00\x04\x07\x07\x07\x07'
        self.assertEqual(20832, utils.Utils.create_fletcher_checksum(byte_stream))
        byte_stream = b' \x01\x00\x00\x00\x00\x08\x08\x08\x08\x80\x00\x00\x04\x00\x00\x00(\x00\x00\x003\x02\x00\x00\n' \
                      b'\x00\x00\x00\x04\x00\x00\x00\x04\x07\x07\x07\x07'
        self.assertEqual(19299, utils.Utils.create_fletcher_checksum(byte_stream))

    #  Successful run - Instant
    def test_get_ipv4_address_from_interface_name(self):
        self.assertEqual(INTERFACE_IPV4, utils.Utils.get_ipv4_address_from_interface_name(INTERFACE_NAME))

    #  Successful run - Instant
    def test_get_ipv6_global_address_from_interface_name(self):
        self.assertEqual(INTERFACE_IPV6, utils.Utils.get_ipv6_global_address_from_interface_name(INTERFACE_NAME))

    #  Successful run - Instant
    def test_get_ipv6_link_local_address_from_interface_name(self):
        link_local_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(INTERFACE_NAME)
        self.assertEqual("fe80", link_local_address[0:4])
        self.assertFalse('%' in link_local_address)
        self.assertFalse(INTERFACE_NAME in link_local_address)
        self.assertTrue(utils.Utils.is_ipv6_address(link_local_address))

    #  Successful run - Instant
    def test_get_ipv4_network_mask_from_interface_name(self):
        self.assertEqual(NETWORK_MASK_IPV4, utils.Utils.get_ipv4_network_mask_from_interface_name(INTERFACE_NAME))

    #  Successful run - Instant
    def test_get_ipv4_prefix_from_interface_name(self):
        self.assertEqual(
            [PREFIX_IPV4, PREFIX_IPV4_LENGTH], utils.Utils.get_ipv4_prefix_from_interface_name(INTERFACE_NAME))

    #  Successful run - Instant
    def test_get_ipv6_network_mask_from_interface_name(self):
        self.assertEqual(NETWORK_MASK_IPV6, utils.Utils.get_ipv6_network_mask_from_interface_name(INTERFACE_NAME))

    #  Successful run - Instant
    def test_get_ipv6_prefix_from_interface_name(self):
        self.assertEqual(
            [PREFIX_IPV6, PREFIX_IPV6_LENGTH], utils.Utils.get_ipv6_prefix_from_interface_name(INTERFACE_NAME))

    #  Successful run - Instant
    def test_is_ipv4_address_successful(self):
        self.assertTrue(utils.Utils.is_ipv4_address('0.0.0.0'))
        self.assertTrue(utils.Utils.is_ipv4_address('0.0.0.1'))
        self.assertTrue(utils.Utils.is_ipv4_address('0.0.0.255'))
        self.assertTrue(utils.Utils.is_ipv4_address('0.0.1.0'))
        self.assertTrue(utils.Utils.is_ipv4_address('0.0.255.255'))
        self.assertTrue(utils.Utils.is_ipv4_address('0.1.0.0'))
        self.assertTrue(utils.Utils.is_ipv4_address('0.1.0.0'))
        self.assertTrue(utils.Utils.is_ipv4_address('0.255.255.255'))
        self.assertTrue(utils.Utils.is_ipv4_address('1.0.0.0'))
        self.assertTrue(utils.Utils.is_ipv4_address('255.255.255.255'))

    #  Successful run - Instant
    def test_is_ipv6_address_successful(self):
        self.assertTrue(utils.Utils.is_ipv6_address('::'))
        self.assertTrue(utils.Utils.is_ipv6_address('0::'))
        self.assertTrue(utils.Utils.is_ipv6_address('ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_address('::0'))
        self.assertTrue(utils.Utils.is_ipv6_address('::ffff'))
        self.assertTrue(utils.Utils.is_ipv6_address('0::0'))
        self.assertTrue(utils.Utils.is_ipv6_address('ffff::ffff'))
        self.assertTrue(utils.Utils.is_ipv6_address('ffff:0::0:ffff'))
        self.assertTrue(utils.Utils.is_ipv6_address('ffff:ffff::ffff:ffff'))
        self.assertTrue(utils.Utils.is_ipv6_address('0:0:0:0:0:0:0::'))
        self.assertTrue(utils.Utils.is_ipv6_address('ffff:ffff:ffff:ffff:ffff:ffff:ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_address('::0:0:0:0:0:0:0'))
        self.assertTrue(utils.Utils.is_ipv6_address('::ffff:ffff:ffff:ffff:ffff:ffff:ffff'))
        self.assertTrue(utils.Utils.is_ipv6_address('0:0:0:0:0:0:0:0'))
        self.assertTrue(utils.Utils.is_ipv6_address('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'))

    #  Successful run - Instant
    def test_is_ipv4_address_invalid_ip(self):
        self.assertFalse(utils.Utils.is_ipv4_address(''))
        self.assertFalse(utils.Utils.is_ipv4_address('        '))
        self.assertFalse(utils.Utils.is_ipv4_address('An invalid IP address'))
        self.assertFalse(utils.Utils.is_ipv4_address('0::0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0.'))
        self.assertFalse(utils.Utils.is_ipv4_address('.0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0.0.0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0.0.0.'))
        self.assertFalse(utils.Utils.is_ipv4_address('0.0.0.0.'))
        self.assertFalse(utils.Utils.is_ipv4_address('0.0.0.0.0'))
        self.assertFalse(utils.Utils.is_ipv4_address('256.0.0.0'))
        self.assertFalse(utils.Utils.is_ipv4_address('-1.0.0.0'))
        self.assertFalse(utils.Utils.is_ipv4_address('256.256.256.256'))
        self.assertFalse(utils.Utils.is_ipv4_address('-1.-1.-1.-1'))
        self.assertFalse(utils.Utils.is_ipv4_address(' 0.0.0.0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0 .0.0.0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0. 0.0.0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0.0.0 .0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0.0.0. 0'))
        self.assertFalse(utils.Utils.is_ipv4_address('0.0.0.0 '))
        self.assertFalse(utils.Utils.is_ipv4_address(1))

    #  Successful run - Instant
    def test_is_ipv6_address_invalid_ip(self):
        self.assertFalse(utils.Utils.is_ipv6_address(''))
        self.assertFalse(utils.Utils.is_ipv6_address('    '))
        self.assertFalse(utils.Utils.is_ipv6_address('An invalid IP address'))
        self.assertFalse(utils.Utils.is_ipv6_address('0.0.0.0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0'))
        self.assertFalse(utils.Utils.is_ipv6_address('00000000'))
        self.assertFalse(utils.Utils.is_ipv6_address('0:'))
        self.assertFalse(utils.Utils.is_ipv6_address(':0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0:0:0:0:0:0:0:'))
        self.assertFalse(utils.Utils.is_ipv6_address(':0:0:0:0:0:0:0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0:0:0:0:0:0:0:0::'))
        self.assertFalse(utils.Utils.is_ipv6_address('::0:0:0:0:0:0:0:0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0:0:0:0::0:0:0:0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0:0:0:0:0:0:0:0:0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0:0:0:0:0:0:0'))
        self.assertFalse(utils.Utils.is_ipv6_address(' 0::0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0 ::0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0: :0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0:: 0'))
        self.assertFalse(utils.Utils.is_ipv6_address('0::0 '))
        self.assertFalse(utils.Utils.is_ipv6_address('0:0::0:0::0:0'))
        self.assertFalse(utils.Utils.is_ipv6_address('-1::0'))
        self.assertFalse(utils.Utils.is_ipv6_address('-1::-1'))
        self.assertFalse(utils.Utils.is_ipv6_address('-1:-1:-1:-1:-1:-1:-1:-1'))
        self.assertFalse(utils.Utils.is_ipv6_address('fffg::0'))
        self.assertFalse(utils.Utils.is_ipv6_address('fffg::fffg'))
        self.assertFalse(utils.Utils.is_ipv6_address('fffg:fffg:fffg:fffg:fffg:fffg:fffg:fffg'))
        self.assertFalse(utils.Utils.is_ipv6_address('10000::0'))
        self.assertFalse(utils.Utils.is_ipv6_address('10000::10000'))
        self.assertFalse(utils.Utils.is_ipv6_address('10000:10000:10000:10000:10000:10000:10000:10000'))
        self.assertFalse(utils.Utils.is_ipv6_address(1))

    #  Successful run - Instant
    def test_get_ospf_version(self):
        self.assertEqual(conf.VERSION_IPV4, utils.Utils.get_ospf_version('0.0.0.0'))
        self.assertEqual(conf.VERSION_IPV6, utils.Utils.get_ospf_version('::'))
        with self.assertRaises(ValueError):
            utils.Utils.get_ospf_version('')

    #  Successful run - Instant
    def test_is_ipv4_network_mask_successful(self):
        self.assertTrue(utils.Utils.is_ipv4_network_mask('0.0.0.0'))
        self.assertTrue(utils.Utils.is_ipv4_network_mask('128.0.0.0'))
        self.assertTrue(utils.Utils.is_ipv4_network_mask('255.0.0.0'))
        self.assertTrue(utils.Utils.is_ipv4_network_mask('255.255.0.0'))
        self.assertTrue(utils.Utils.is_ipv4_network_mask('255.255.255.0'))
        self.assertTrue(utils.Utils.is_ipv4_network_mask('255.255.255.254'))
        self.assertTrue(utils.Utils.is_ipv4_network_mask('255.255.255.255'))

    #  Successful run - Instant
    def test_is_ipv4_network_mask_invalid_mask(self):
        self.assertFalse(utils.Utils.is_ipv4_network_mask(''))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('An invalid IP address'))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('222.222.1.0'))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('127.0.0.1'))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('0.0.0.1'))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('255.255.255.253'))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('255.255.255.64'))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('255.255.64.0'))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('255.64.0.0'))
        self.assertFalse(utils.Utils.is_ipv4_network_mask('64.0.0.0'))

    #  Successful run - Instant
    def test_is_ipv6_network_mask_successful(self):
        self.assertTrue(utils.Utils.is_ipv6_network_mask('::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('8000::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ff00::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff:ffff::'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff:ffff:8000'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ff00'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe'))
        self.assertTrue(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'))

    #  Successful run - Instant
    def test_is_ipv6_network_mask_invalid_mask(self):
        self.assertFalse(utils.Utils.is_ipv6_network_mask(''))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('An invalid IP address'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('2001:db8:cafe:1::'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('2001:db8:cafe:1::1'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('::1'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffd'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff:ffff:4000'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:ffff:4000::'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:ffff:4000::'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:ffff:4000::'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('ffff:ffff:ffff:4000::'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('ffff:ffff:4000::'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('ffff:4000::'))
        self.assertFalse(utils.Utils.is_ipv6_network_mask('4000::'))

    #  Successful run - Instant
    def test_is_ip_in_network(self):
        self.assertTrue(utils.Utils.is_ip_in_network(INTERFACE_IPV4, INTERFACE_NAME))
        next_address = utils.Utils.decimal_to_ipv4(utils.Utils.ipv4_to_decimal(INTERFACE_IPV4) + 1)
        self.assertTrue(utils.Utils.is_ip_in_network(next_address, INTERFACE_NAME))
        next_address = utils.Utils.decimal_to_ipv4(utils.Utils.ipv4_to_decimal(INTERFACE_IPV4) + 2)
        self.assertTrue(utils.Utils.is_ip_in_network(next_address, INTERFACE_NAME))

        self.assertTrue(utils.Utils.is_ip_in_network(INTERFACE_IPV6, INTERFACE_NAME))
        next_address = utils.Utils.decimal_to_ipv6(utils.Utils.ipv6_to_decimal(INTERFACE_IPV6) + 1)
        self.assertTrue(utils.Utils.is_ip_in_network(next_address, INTERFACE_NAME))
        next_address = utils.Utils.decimal_to_ipv6(utils.Utils.ipv6_to_decimal(INTERFACE_IPV6) + 2)
        self.assertTrue(utils.Utils.is_ip_in_network(next_address, INTERFACE_NAME))

        self.assertFalse(utils.Utils.is_ip_in_network('-1.-1.-1.-1', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('::-1', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('0.0.0.0', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('::', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('0.0.0.1', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('::1', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('255.255.255.254', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('255.255.255.255', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('256.256.256.256', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('gggg:gggg:gggg:gggg:gggg:gggg:gggg:gggg', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network('Invalid address', INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network(0, INTERFACE_NAME))
        self.assertFalse(utils.Utils.is_ip_in_network(None, INTERFACE_NAME))

    #  Successful run - Instant
    def test_ip_address_to_prefix(self):
        self.assertEqual('222.222.1.0', utils.Utils.ip_address_to_prefix('222.222.1.1', 24))
        self.assertEqual('222.222.1.0', utils.Utils.ip_address_to_prefix('222.222.1.1', '255.255.255.0'))
        self.assertEqual('2001:db8:cafe:1::', utils.Utils.ip_address_to_prefix('2001:db8:cafe:1::1', 64))

    #  Successful run - Instant
    def test_prefix_lenght_to_network_mask(self):
        self.assertEqual('255.255.255.0', utils.Utils.prefix_length_to_network_mask(24, conf.VERSION_IPV4))
        self.assertEqual('ffff:ffff:ffff:ffff::', utils.Utils.prefix_length_to_network_mask(64, conf.VERSION_IPV6))

    #  Successful run - Instant
    def test_get_prefix_length_from_prefix(self):
        self.assertEqual(24, utils.Utils.get_prefix_length_from_prefix('222.222.1.0'))
        self.assertEqual(64, utils.Utils.get_prefix_length_from_prefix('2001:db8:cafe:1::'))

    #  Successful run - Instant
    def test_get_prefix_from_prefix_length(self):
        self.assertEqual('255.255.255.0', utils.Utils.get_prefix_from_prefix_length(24, conf.VERSION_IPV4))
        self.assertEqual('ffff:ffff:ffff:ffff::', utils.Utils.get_prefix_from_prefix_length(64, conf.VERSION_IPV6))
