import unittest

import lsa.intra_area_prefix as intra_area_prefix

'''
This class tests the OSPF Intra-Area-Prefix-LSA body class and its operations
'''


#  Full successful run - Instant
class TestIntraAreaPrefix(unittest.TestCase):

    #  Successful run - Instant
    def test_pack_body(self):
        body_bytes = b'\x00\x00 \x01\x00\x00\x00\x00\x08\x08\x08\x08'
        self.assertEqual(body_bytes, intra_area_prefix.IntraAreaPrefix(0x2001, '0.0.0.0', '8.8.8.8').pack_lsa_body())

        body_bytes = b'\x00\t \x01\x00\x00\x00\x00\x07\x07\x07\x07\x00\x00\x00\n\x01\x00\x00\n\x00\x00\x00\x00 \x00' \
                     b'\x00\n \x01\r\xb8!\x00\x00\n \x01\r\xb8\x80\x00\x00\x00@\x00\x00\n \x01\r\xb8\xca\xfe\x00\x11A' \
                     b'\x00\x00\n \x01\r\xb8\xca\xfe\x00\x12\x00\x00\x00\x00`\x00\x00\n \x01\r\xb8\xca\xfe\x00\x13' \
                     b'\x00\x00\x00\x00a\x00\x00\n \x01\r\xb8\xca\xfe\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x80\x02' \
                     b'\x00\x00 \x01\r\xb8\xca\xfe\x00\x15\x00\x00\x00\x00\x00\x00\x00\x01'
        lsa_body = intra_area_prefix.IntraAreaPrefix(0x2001, '0.0.0.0', '7.7.7.7')
        lsa_body.add_prefix_info(0, 0, 10, '::')
        lsa_body.add_prefix_info(1, 0, 10, '::')
        lsa_body.add_prefix_info(32, 0, 10, '2001:db8::')
        lsa_body.add_prefix_info(33, 0, 10, '2001:db8:8000::')
        lsa_body.add_prefix_info(64, 0, 10, '2001:db8:cafe:11::')
        lsa_body.add_prefix_info(65, 0, 10, '2001:db8:cafe:12::')
        lsa_body.add_prefix_info(96, 0, 10, '2001:db8:cafe:13::')
        lsa_body.add_prefix_info(97, 0, 10, '2001:db8:cafe:14::')
        lsa_body.add_prefix_info(128, 2, 0, '2001:db8:cafe:15::1')
        self.assertEqual(body_bytes, lsa_body.pack_lsa_body())

    #  Successful run - Instant
    def test_unpack_body(self):
        body_bytes = b'\x00\x00 \x01\x00\x00\x00\x00\x08\x08\x08\x08'
        unpacked_body = intra_area_prefix.IntraAreaPrefix.unpack_lsa_body(body_bytes, 0)
        self.assertEqual(0, unpacked_body.prefix_number)
        self.assertEqual(0x2001, unpacked_body.referenced_ls_type)
        self.assertEqual(0, unpacked_body.get_referenced_u_bit())
        self.assertEqual(1, unpacked_body.get_referenced_s1_s2_bits())
        self.assertEqual(1, unpacked_body.get_referenced_ls_type())
        self.assertEqual('0.0.0.0', unpacked_body.referenced_link_state_id)
        self.assertEqual('8.8.8.8', unpacked_body.referenced_advertising_router)
        self.assertEqual(0, len(unpacked_body.prefixes))

        body_bytes = b'\x00\t \x01\x00\x00\x00\x00\x07\x07\x07\x07\x00\x00\x00\n\x01\x00\x00\n\x00\x00\x00\x00 \x00' \
                     b'\x00\n \x01\r\xb8!\x00\x00\n \x01\r\xb8\x80\x00\x00\x00@\x00\x00\n \x01\r\xb8\xca\xfe\x00\x11A' \
                     b'\x00\x00\n \x01\r\xb8\xca\xfe\x00\x12\x00\x00\x00\x00`\x00\x00\n \x01\r\xb8\xca\xfe\x00\x13' \
                     b'\x00\x00\x00\x00a\x00\x00\n \x01\r\xb8\xca\xfe\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x80\x02' \
                     b'\x00\x00 \x01\r\xb8\xca\xfe\x00\x15\x00\x00\x00\x00\x00\x00\x00\x01'
        unpacked_body = intra_area_prefix.IntraAreaPrefix.unpack_lsa_body(body_bytes, 0)
        self.assertEqual(9, unpacked_body.prefix_number)
        self.assertEqual(0x2001, unpacked_body.referenced_ls_type)
        self.assertEqual(0, unpacked_body.get_referenced_u_bit())
        self.assertEqual(1, unpacked_body.get_referenced_s1_s2_bits())
        self.assertEqual(1, unpacked_body.get_referenced_ls_type())
        self.assertEqual('0.0.0.0', unpacked_body.referenced_link_state_id)
        self.assertEqual('7.7.7.7', unpacked_body.referenced_advertising_router)
        self.assertEqual(9, len(unpacked_body.prefixes))
        self.assertEqual([0, 0, 10, '::'], unpacked_body.prefixes[0])
        self.assertEqual([1, 0, 10, '::'], unpacked_body.prefixes[1])
        self.assertEqual([32, 0, 10, '2001:db8::'], unpacked_body.prefixes[2])
        self.assertEqual([33, 0, 10, '2001:db8:8000::'], unpacked_body.prefixes[3])
        self.assertEqual([64, 0, 10, '2001:db8:cafe:11::'], unpacked_body.prefixes[4])
        self.assertEqual([65, 0, 10, '2001:db8:cafe:12::'], unpacked_body.prefixes[5])
        self.assertEqual([96, 0, 10, '2001:db8:cafe:13::'], unpacked_body.prefixes[6])
        self.assertEqual([97, 0, 10, '2001:db8:cafe:14::'], unpacked_body.prefixes[7])
        self.assertEqual([128, 2, 0, '2001:db8:cafe:15::1'], unpacked_body.prefixes[8])
