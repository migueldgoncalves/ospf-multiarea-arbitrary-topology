import unittest

import lsa.link as link

'''
This class tests the OSPF Link-LSA body class and its operations
'''


#  Full successful run - Instant
class TestLink(unittest.TestCase):

    #  Successful run - Instant
    def test_add_prefix_info(self):
        lsa_body = link.Link(1, 51, 'fe80::c004:18ff:fe30:0')
        self.assertEqual(0, len(lsa_body.prefixes))
        self.assertEqual(0, lsa_body.prefix_number)
        lsa_body.add_prefix_info(1, 0, '::')
        self.assertEqual(1, len(lsa_body.prefixes))
        self.assertEqual(1, lsa_body.prefix_number)
        self.assertEqual(1, lsa_body.prefixes[0][0])
        lsa_body.add_prefix_info(1, 0, '::')
        self.assertEqual(1, len(lsa_body.prefixes))
        self.assertEqual(1, lsa_body.prefix_number)
        self.assertEqual(1, lsa_body.prefixes[0][0])
        lsa_body.add_prefix_info(3, 0, '::')
        self.assertEqual(2, len(lsa_body.prefixes))
        self.assertEqual(2, lsa_body.prefix_number)
        self.assertEqual(3, lsa_body.prefixes[1][0])

    #  Successful run - Instant
    def test_has_prefix_info(self):
        lsa_body = link.Link(1, 51, 'fe80::c004:18ff:fe30:0')
        lsa_body.add_prefix_info(1, 0, '::')
        self.assertTrue(lsa_body.has_prefix_info(1, 0, '::'))
        self.assertFalse(lsa_body.has_prefix_info(0, 0, '::'))
        self.assertFalse(lsa_body.has_prefix_info(1, 1, '::'))
        self.assertFalse(lsa_body.has_prefix_info(1, 0, '1::'))

    #  Successful run - Instant
    def test_delete_prefix_info(self):
        lsa_body = link.Link(1, 51, 'fe80::c004:18ff:fe30:0')
        lsa_body.add_prefix_info(1, 0, '::')
        lsa_body.add_prefix_info(3, 0, '::')
        self.assertEqual(2, len(lsa_body.prefixes))
        self.assertEqual(2, lsa_body.prefix_number)
        lsa_body.delete_prefix_info(1, 0, '::')
        self.assertEqual(1, len(lsa_body.prefixes))
        self.assertEqual(1, lsa_body.prefix_number)
        self.assertEqual(3, lsa_body.prefixes[0][0])
        lsa_body.delete_prefix_info(1, 0, '::')
        self.assertEqual(1, len(lsa_body.prefixes))
        self.assertEqual(1, lsa_body.prefix_number)
        self.assertEqual(3, lsa_body.prefixes[0][0])
        lsa_body.delete_prefix_info(3, 0, '::')
        self.assertEqual(0, len(lsa_body.prefixes))
        self.assertEqual(0, lsa_body.prefix_number)

    #  Successful run - Instant
    def test_pack_body(self):
        body_bytes = b'\x01\x00\x003\xfe\x80\x00\x00\x00\x00\x00\x00\xc0\x04\x18\xff\xfe0\x00\x00\x00\x00\x00\x00'
        lsa_body = link.Link(1, 51, 'fe80::c004:18ff:fe30:0')
        self.assertEqual(body_bytes, lsa_body.pack_lsa_body())

        body_bytes = b'\x01\x00\x003\xfe\x80\x00\x00\x00\x00\x00\x00\xc0\x04\x18\xff\xfe0\x00\x00\x00\x00\x00\t\x00' \
                     b'\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00 \x01\r\xb8!\x00\x00\x00 \x01\r\xb8' \
                     b'\x80\x00\x00\x00@\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x11A\x00\x00\x00 \x01\r\xb8\xca\xfe\x00' \
                     b'\x12\x00\x00\x00\x00`\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x13\x00\x00\x00\x00a\x00\x00\x00 \x01' \
                     b'\r\xb8\xca\xfe\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x80\x02\x00\x00 \x01\r\xb8\xca\xfe\x00' \
                     b'\x15\x00\x00\x00\x00\x00\x00\x00\x01'
        lsa_body = link.Link(1, 51, 'fe80::c004:18ff:fe30:0')
        lsa_body.add_prefix_info(0, 0, '::')
        lsa_body.add_prefix_info(1, 0, '::')
        lsa_body.add_prefix_info(32, 0, '2001:db8::')
        lsa_body.add_prefix_info(33, 0, '2001:db8:8000::')
        lsa_body.add_prefix_info(64, 0, '2001:db8:cafe:11::')
        lsa_body.add_prefix_info(65, 0, '2001:db8:cafe:12::')
        lsa_body.add_prefix_info(96, 0, '2001:db8:cafe:13::')
        lsa_body.add_prefix_info(97, 0, '2001:db8:cafe:14::')
        lsa_body.add_prefix_info(128, 2, '2001:db8:cafe:15::1')
        self.assertEqual(body_bytes, lsa_body.pack_lsa_body())

    #  Successful run - Instant
    def test_unpack_body(self):
        body_bytes = b'\x01\x00\x003\xfe\x80\x00\x00\x00\x00\x00\x00\xc0\x04\x18\xff\xfe0\x00\x00\x00\x00\x00\x00'
        unpacked_body = link.Link.unpack_lsa_body(body_bytes, 0)
        self.assertEqual(1, unpacked_body.router_priority)
        self.assertEqual(51, unpacked_body.options)
        self.assertEqual('fe80::c004:18ff:fe30:0', unpacked_body.link_local_address)
        self.assertEqual(0, unpacked_body.prefix_number)
        self.assertEqual(0, len(unpacked_body.prefixes))

        body_bytes = b'\x01\x00\x003\xfe\x80\x00\x00\x00\x00\x00\x00\xc0\x04\x18\xff\xfe0\x00\x00\x00\x00\x00\t\x00' \
                     b'\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00 \x01\r\xb8!\x00\x00\x00 \x01\r\xb8' \
                     b'\x80\x00\x00\x00@\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x11A\x00\x00\x00 \x01\r\xb8\xca\xfe\x00' \
                     b'\x12\x00\x00\x00\x00`\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x13\x00\x00\x00\x00a\x00\x00\x00 \x01' \
                     b'\r\xb8\xca\xfe\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x80\x02\x00\x00 \x01\r\xb8\xca\xfe\x00' \
                     b'\x15\x00\x00\x00\x00\x00\x00\x00\x01'
        unpacked_body = link.Link.unpack_lsa_body(body_bytes, 0)
        self.assertEqual(1, unpacked_body.router_priority)
        self.assertEqual(51, unpacked_body.options)
        self.assertEqual('fe80::c004:18ff:fe30:0', unpacked_body.link_local_address)
        self.assertEqual(9, unpacked_body.prefix_number)
        self.assertEqual(9, len(unpacked_body.prefixes))
        self.assertEqual([0, 0, '::'], unpacked_body.prefixes[0])
        self.assertEqual([1, 0, '::'], unpacked_body.prefixes[1])
        self.assertEqual([32, 0, '2001:db8::'], unpacked_body.prefixes[2])
        self.assertEqual([33, 0, '2001:db8:8000::'], unpacked_body.prefixes[3])
        self.assertEqual([64, 0, '2001:db8:cafe:11::'], unpacked_body.prefixes[4])
        self.assertEqual([65, 0, '2001:db8:cafe:12::'], unpacked_body.prefixes[5])
        self.assertEqual([96, 0, '2001:db8:cafe:13::'], unpacked_body.prefixes[6])
        self.assertEqual([97, 0, '2001:db8:cafe:14::'], unpacked_body.prefixes[7])
        self.assertEqual([128, 2, '2001:db8:cafe:15::1'], unpacked_body.prefixes[8])
