import unittest

import lsa.inter_area_prefix as inter_area_prefix

'''
This class tests the OSPF Inter-Area-Prefix-LSA body class and its operations
'''


#  Full successful run - Instant
class TestInterAreaPrefix(unittest.TestCase):

    body_bytes_prefix_0 = b'\x00\x00\x00\n\x00\x00\x00\x00'
    body_bytes_prefix_1 = b'\x00\x00\x00\n\x01\x00\x00\x00\x00\x00\x00\x00'
    body_bytes_prefix_32 = b'\x00\x00\x00\n\x20\x00\x00\x00\x20\x01\x0d\xb8'
    body_bytes_prefix_33 = b'\x00\x00\x00\n\x21\x00\x00\x00\x20\x01\x0d\xb8\x80\x00\x00\x00'
    body_bytes_prefix_64 = b'\x00\x00\x00\n\x40\x00\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01'
    body_bytes_prefix_65 = b'\x00\x00\x00\n\x41\x00\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x00'
    body_bytes_prefix_96 = b'\x00\x00\x00\n\x60\x00\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x00'
    body_bytes_prefix_97 = b'\x00\x00\x00\n\x61\x00\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x00\x00\x00' \
                           b'\x00\x00'
    body_bytes_prefix_128 = b'\x00\x00\x00\n\x80\x00\x00\x00\x20\x01\x0d\xb8\xca\xfe\x00\x01\x00\x00\x00\x00\x00\x00' \
                            b'\x00\x01'
    metric = 10

    #  Successful run - Instant
    def test_pack_body(self):
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_0, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 0, 0, '::').pack_lsa_body())
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_1, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 1, 0, '::').pack_lsa_body())
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_32, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 32, 0, '2001:db8::').pack_lsa_body())
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_33, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 33, 0, '2001:db8:8000::').pack_lsa_body())
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_64, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 64, 0, '2001:db8:cafe:1::').pack_lsa_body())
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_65, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 65, 0, '2001:db8:cafe:1::').pack_lsa_body())
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_96, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 96, 0, '2001:db8:cafe:1::').pack_lsa_body())
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_97, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 97, 0, '2001:db8:cafe:1::').pack_lsa_body())
        self.assertEqual(TestInterAreaPrefix.body_bytes_prefix_128, inter_area_prefix.InterAreaPrefix(
            TestInterAreaPrefix.metric, 128, 0, '2001:db8:cafe:1::1').pack_lsa_body())

    #  Successful run - Instant
    def test_unpack_body(self):
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_0, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(0, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('::', unpacked_body.address_prefix)
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_1, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(1, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('::', unpacked_body.address_prefix)
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_32, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(32, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('2001:db8::', unpacked_body.address_prefix)
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_33, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(33, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('2001:db8:8000::', unpacked_body.address_prefix)
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_64, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(64, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('2001:db8:cafe:1::', unpacked_body.address_prefix)
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_65, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(65, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('2001:db8:cafe:1::', unpacked_body.address_prefix)
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_96, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(96, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('2001:db8:cafe:1::', unpacked_body.address_prefix)
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_97, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(97, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('2001:db8:cafe:1::', unpacked_body.address_prefix)
        unpacked_body = inter_area_prefix.InterAreaPrefix.unpack_lsa_body(TestInterAreaPrefix.body_bytes_prefix_128, 0)
        self.assertEqual(TestInterAreaPrefix.metric, unpacked_body.metric)
        self.assertEqual(128, unpacked_body.prefix_length)
        self.assertEqual(0, unpacked_body.prefix_options)
        self.assertEqual('2001:db8:cafe:1::1', unpacked_body.address_prefix)
