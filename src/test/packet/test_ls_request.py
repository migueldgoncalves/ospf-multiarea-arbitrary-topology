import unittest

import packet.ls_request as ls_request
import conf.conf as conf

'''
This class tests the OSPF Link State Request packet class and its operations
'''


#  Full successful run - Instant
class TestLSRequest(unittest.TestCase):

    #  Successful run - Instant
    def test_pack_packet(self):
        body_bytes = b'\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x01\x02\x02\x02\x02\x02\x02\x02' \
                     b'\x02\x00\x00\x00\x01\x03\x03\x03\x03\x03\x03\x03\x03\x00\x00\x00\x02\xde\xde\x03\x02\x02\x02' \
                     b'\x02\x02'
        packet_body = ls_request.LSRequest(conf.VERSION_IPV4)
        packet_body.add_lsa_info(1, '1.1.1.1', '1.1.1.1')
        packet_body.add_lsa_info(1, '2.2.2.2', '2.2.2.2')
        packet_body.add_lsa_info(1, '3.3.3.3', '3.3.3.3')
        packet_body.add_lsa_info(2, '222.222.3.2', '2.2.2.2')
        self.assertEqual(body_bytes, packet_body.pack_packet_body())

        body_bytes = b'\x00\x00 \x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00 \x01\x00\x00\x00\x00\x02\x02\x02\x02' \
                     b'\x00\x00 \x01\x00\x00\x00\x00\x03\x03\x03\x03\x00\x00 \x02\x00\x00\x00\x05\x02\x02\x02\x02\x00' \
                     b'\x00 \x02\x00\x00\x00\x04\x03\x03\x03\x03\x00\x00\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x00' \
                     b'\x00\x00\x08\x00\x00\x00\x05\x02\x02\x02\x02\x00\x00 \t\x00\x00\x00\x00\x01\x01\x01\x01\x00' \
                     b'\x00 \t\x00\x00\x00\x00\x02\x02\x02\x02\x00\x00 \t\x00\x00\x14\x00\x02\x02\x02\x02\x00\x00 \t' \
                     b'\x00\x00\x00\x00\x03\x03\x03\x03\x00\x00 \t\x00\x00\x10\x00\x03\x03\x03\x03'
        packet_body = ls_request.LSRequest(conf.VERSION_IPV6)
        packet_body.add_lsa_info(1, '0.0.0.0', '1.1.1.1')
        packet_body.add_lsa_info(1, '0.0.0.0', '2.2.2.2')
        packet_body.add_lsa_info(1, '0.0.0.0', '3.3.3.3')
        packet_body.add_lsa_info(2, '0.0.0.5', '2.2.2.2')
        packet_body.add_lsa_info(2, '0.0.0.4', '3.3.3.3')
        packet_body.add_lsa_info(8, '0.0.0.4', '1.1.1.1')
        packet_body.add_lsa_info(8, '0.0.0.5', '2.2.2.2')
        packet_body.add_lsa_info(9, '0.0.0.0', '1.1.1.1')
        packet_body.add_lsa_info(9, '0.0.0.0', '2.2.2.2')
        packet_body.add_lsa_info(9, '0.0.20.0', '2.2.2.2')
        packet_body.add_lsa_info(9, '0.0.0.0', '3.3.3.3')
        packet_body.add_lsa_info(9, '0.0.16.0', '3.3.3.3')
        self.assertEqual(body_bytes, packet_body.pack_packet_body())

    #  Successful run - Instant
    def test_unpack_packet(self):
        body_bytes = b'\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x01\x02\x02\x02\x02\x02\x02\x02' \
                     b'\x02\x00\x00\x00\x01\x03\x03\x03\x03\x03\x03\x03\x03\x00\x00\x00\x02\xde\xde\x03\x02\x02\x02' \
                     b'\x02\x02'
        packet_body = ls_request.LSRequest.unpack_packet_body(body_bytes, conf.VERSION_IPV4)
        self.assertEqual(4, len(packet_body.lsa_identifiers))
        self.assertEqual([[1, '1.1.1.1', '1.1.1.1'], [1, '2.2.2.2', '2.2.2.2'], [1, '3.3.3.3', '3.3.3.3'],
                          [2, '222.222.3.2', '2.2.2.2']], packet_body.lsa_identifiers)
        self.assertEqual(conf.VERSION_IPV4, packet_body.version)

        body_bytes = b'\x00\x00 \x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00 \x01\x00\x00\x00\x00\x02\x02\x02\x02' \
                     b'\x00\x00 \x01\x00\x00\x00\x00\x03\x03\x03\x03\x00\x00 \x02\x00\x00\x00\x05\x02\x02\x02\x02\x00' \
                     b'\x00 \x02\x00\x00\x00\x04\x03\x03\x03\x03\x00\x00\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x00' \
                     b'\x00\x00\x08\x00\x00\x00\x05\x02\x02\x02\x02\x00\x00 \t\x00\x00\x00\x00\x01\x01\x01\x01\x00' \
                     b'\x00 \t\x00\x00\x00\x00\x02\x02\x02\x02\x00\x00 \t\x00\x00\x14\x00\x02\x02\x02\x02\x00\x00 \t' \
                     b'\x00\x00\x00\x00\x03\x03\x03\x03\x00\x00 \t\x00\x00\x10\x00\x03\x03\x03\x03'
        packet_body = ls_request.LSRequest.unpack_packet_body(body_bytes, conf.VERSION_IPV6)
        self.assertEqual(12, len(packet_body.lsa_identifiers))
        self.assertEqual(
            [[0x2001, '0.0.0.0', '1.1.1.1'], [0x2001, '0.0.0.0', '2.2.2.2'], [0x2001, '0.0.0.0', '3.3.3.3'],
             [0x2002, '0.0.0.5', '2.2.2.2'], [0x2002, '0.0.0.4', '3.3.3.3'], [8, '0.0.0.4', '1.1.1.1'],
             [8, '0.0.0.5', '2.2.2.2'], [0x2009, '0.0.0.0', '1.1.1.1'], [0x2009, '0.0.0.0', '2.2.2.2'],
             [0x2009, '0.0.20.0', '2.2.2.2'], [0x2009, '0.0.0.0', '3.3.3.3'], [0x2009, '0.0.16.0', '3.3.3.3']],
            packet_body.lsa_identifiers)
        self.assertEqual(conf.VERSION_IPV6, packet_body.version)


if __name__ == '__main__':
    unittest.main()
