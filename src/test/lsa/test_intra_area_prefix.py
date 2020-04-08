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
        self.assertEqual(body_bytes, intra_area_prefix.IntraAreaPrefix(1, '0.0.0.0', '8.8.8.8').pack_lsa_body())

        body_bytes = b'\x00\t \x01\x00\x00\x00\x00\x07\x07\x07\x07\x00\x00\x00\n\x01\x00\x00\n\x00\x00\x00\x00 \x00' \
                     b'\x00\n \x01\r\xb8!\x00\x00\n \x01\r\xb8\x80\x00\x00\x00@\x00\x00\n \x01\r\xb8\xca\xfe\x00\x11A' \
                     b'\x00\x00\n \x01\r\xb8\xca\xfe\x00\x12\x00\x00\x00\x00`\x00\x00\n \x01\r\xb8\xca\xfe\x00\x13' \
                     b'\x00\x00\x00\x00a\x00\x00\n \x01\r\xb8\xca\xfe\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x80\x02' \
                     b'\x00\x00 \x01\r\xb8\xca\xfe\x00\x15\x00\x00\x00\x00\x00\x00\x00\x01'
        lsa_body = intra_area_prefix.IntraAreaPrefix(1, '0.0.0.0', '7.7.7.7')
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
