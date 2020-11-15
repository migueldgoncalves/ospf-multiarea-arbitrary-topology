import unittest

import lsa.lsa as lsa
import conf.conf as conf
import packet.ls_acknowledgment as ls_acknowledgment

'''
This class tests the OSPF Link State Acknowledgement packet class and its operations
'''


#  Full successful run - Instant
class TestLSAcknowledgement(unittest.TestCase):

    #  Successful run - Instant
    def test_pack_packet(self):
        #  OSPFv2

        body_bytes = b'\x01!"\x01\x02\x02\x02\x02\x02\x02\x02\x02\x80\x00\x00\x03\xf7&\x00<\x0e\x10"\x02\xde\xde\x03' \
                     b'\x02\x02\x02\x02\x02\x80\x00\x00\x02\xde\x83\x00 \x00\x02"\x01\x03\x03\x03\x03\x03\x03\x03\x03' \
                     b'\x80\x00\x00\x06\x07P\x00<\x00\x01"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x80\x00\x00\x05\xea' \
                     b'\xd2\x00T\x00\x01"\x02\xde\xde\x03\x01\x01\x01\x01\x01\x80\x00\x00\x01\x19O\x00 \x00\x02"\x02' \
                     b'\xde\xde\x05\x02\x03\x03\x03\x03\x80\x00\x00\x03\xfcV\x00 '
        lsa_header_1 = lsa.Lsa()
        lsa_header_2 = lsa.Lsa()
        lsa_header_3 = lsa.Lsa()
        lsa_header_4 = lsa.Lsa()
        lsa_header_5 = lsa.Lsa()
        lsa_header_6 = lsa.Lsa()
        lsa_header_1.create_header(289, 34, 1, '2.2.2.2', '2.2.2.2', 0x80000003, conf.VERSION_IPV4)
        lsa_header_1.header.ls_checksum = 63270
        lsa_header_1.header.length = 60
        lsa_header_2.create_header(3600, 34, 2, '222.222.3.2', '2.2.2.2', 0x80000002, conf.VERSION_IPV4)
        lsa_header_2.header.ls_checksum = 56963
        lsa_header_2.header.length = 32
        lsa_header_3.create_header(2, 34, 1, '3.3.3.3', '3.3.3.3', 0x80000006, conf.VERSION_IPV4)
        lsa_header_3.header.ls_checksum = 1872
        lsa_header_3.header.length = 60
        lsa_header_4.create_header(1, 34, 1, '1.1.1.1', '1.1.1.1', 0x80000005, conf.VERSION_IPV4)
        lsa_header_4.header.ls_checksum = 60114
        lsa_header_4.header.length = 84
        lsa_header_5.create_header(1, 34, 2, '222.222.3.1', '1.1.1.1', 0x80000001, conf.VERSION_IPV4)
        lsa_header_5.header.ls_checksum = 6479
        lsa_header_5.header.length = 32
        lsa_header_6.create_header(2, 34, 2, '222.222.5.2', '3.3.3.3', 0x80000003, conf.VERSION_IPV4)
        lsa_header_6.header.ls_checksum = 64598
        lsa_header_6.header.length = 32
        packet_body = ls_acknowledgment.LSAcknowledgement(conf.VERSION_IPV4)
        packet_body.add_lsa_header(lsa_header_1)
        packet_body.add_lsa_header(lsa_header_2)
        packet_body.add_lsa_header(lsa_header_3)
        packet_body.add_lsa_header(lsa_header_4)
        packet_body.add_lsa_header(lsa_header_5)
        packet_body.add_lsa_header(lsa_header_6)
        self.assertEqual(body_bytes, packet_body.pack_packet_body())

        #  OSPFv3

        body_bytes = b'\x00\n \x01\x00\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x06:\x0f\x00H\x01# \x01\x00\x00\x00' \
                     b'\x00\x02\x02\x02\x02\x80\x00\x00\x042}\x008\x00\t \x01\x00\x00\x00\x00\x03\x03\x03\x03\x80\x00' \
                     b'\x00\x06e\t\x008\x00\n \x02\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00\x00\x011\xc3\x00 \x01+ ' \
                     b'\x02\x00\x00\x00\x05\x02\x02\x02\x02\x80\x00\x00\x01\xf8\xf6\x00 \x01+ \x02\x00\x00\x00\x04' \
                     b'\x03\x03\x03\x03\x80\x00\x00\x019\xab\x00 \x01N\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x80' \
                     b'\x00\x00\x02\x80\xfe\x008\x01* \t\x00\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x03\x9c\x1f\x00D' \
                     b'\x00\n \t\x00\x00\x10\x00\x01\x01\x01\x01\x80\x00\x00\x01J\xab\x00,\x01+ \t\x00\x00\x00\x00' \
                     b'\x02\x02\x02\x02\x80\x00\x00\x03\xabJ\x00,\x01+ \t\x00\x00\x14\x00\x02\x02\x02\x02\x80\x00\x00' \
                     b'\x01<\xac\x00,\x01+ \t\x00\x00\x00\x00\x03\x03\x03\x03\x80\x00\x00\x03\xc3\xf1\x00,\x01+ \t' \
                     b'\x00\x00\x10\x00\x03\x03\x03\x03\x80\x00\x00\x01\xa6=\x00,\x00\x01 \x01\x00\x00\x00\x00\x01' \
                     b'\x01\x01\x01\x80\x00\x00\x078\x10\x00H\x00\x02 \x01\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00' \
                     b'\x00\x05\x1e\xbe\x00(\x00\x02 \t\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x04\x9aV\x008'
        lsa_header_1 = lsa.Lsa()
        lsa_header_2 = lsa.Lsa()
        lsa_header_3 = lsa.Lsa()
        lsa_header_4 = lsa.Lsa()
        lsa_header_5 = lsa.Lsa()
        lsa_header_6 = lsa.Lsa()
        lsa_header_7 = lsa.Lsa()
        lsa_header_8 = lsa.Lsa()
        lsa_header_9 = lsa.Lsa()
        lsa_header_10 = lsa.Lsa()
        lsa_header_11 = lsa.Lsa()
        lsa_header_12 = lsa.Lsa()
        lsa_header_13 = lsa.Lsa()
        lsa_header_14 = lsa.Lsa()
        lsa_header_15 = lsa.Lsa()
        lsa_header_16 = lsa.Lsa()
        lsa_header_1.create_header(10, 0, 1, '0.0.0.0', '1.1.1.1', 0x80000006, conf.VERSION_IPV6)
        lsa_header_1.header.ls_checksum = 14863
        lsa_header_1.header.length = 72
        lsa_header_2.create_header(291, 0, 1, '0.0.0.0', '2.2.2.2', 0x80000004, conf.VERSION_IPV6)
        lsa_header_2.header.ls_checksum = 12925
        lsa_header_2.header.length = 56
        lsa_header_3.create_header(9, 0, 1, '0.0.0.0', '3.3.3.3', 0x80000006, conf.VERSION_IPV6)
        lsa_header_3.header.ls_checksum = 25865
        lsa_header_3.header.length = 56
        lsa_header_4.create_header(10, 0, 2, '0.0.0.4', '1.1.1.1', 0x80000001, conf.VERSION_IPV6)
        lsa_header_4.header.ls_checksum = 12739
        lsa_header_4.header.length = 32
        lsa_header_5.create_header(299, 0, 2, '0.0.0.5', '2.2.2.2', 0x80000001, conf.VERSION_IPV6)
        lsa_header_5.header.ls_checksum = 63734
        lsa_header_5.header.length = 32
        lsa_header_6.create_header(299, 0, 2, '0.0.0.4', '3.3.3.3', 0x80000001, conf.VERSION_IPV6)
        lsa_header_6.header.ls_checksum = 14763
        lsa_header_6.header.length = 32
        lsa_header_7.create_header(334, 0, 8, '0.0.0.4', '1.1.1.1', 0x80000002, conf.VERSION_IPV6)
        lsa_header_7.header.ls_checksum = 33022
        lsa_header_7.header.length = 56
        lsa_header_8.create_header(298, 0, 9, '0.0.0.0', '1.1.1.1', 0x80000003, conf.VERSION_IPV6)
        lsa_header_8.header.ls_checksum = 39967
        lsa_header_8.header.length = 68
        lsa_header_9.create_header(10, 0, 9, '0.0.16.0', '1.1.1.1', 0x80000001, conf.VERSION_IPV6)
        lsa_header_9.header.ls_checksum = 19115
        lsa_header_9.header.length = 44
        lsa_header_10.create_header(299, 0, 9, '0.0.0.0', '2.2.2.2', 0x80000003, conf.VERSION_IPV6)
        lsa_header_10.header.ls_checksum = 43850
        lsa_header_10.header.length = 44
        lsa_header_11.create_header(299, 0, 9, '0.0.20.0', '2.2.2.2', 0x80000001, conf.VERSION_IPV6)
        lsa_header_11.header.ls_checksum = 15532
        lsa_header_11.header.length = 44
        lsa_header_12.create_header(299, 0, 9, '0.0.0.0', '3.3.3.3', 0x80000003, conf.VERSION_IPV6)
        lsa_header_12.header.ls_checksum = 50161
        lsa_header_12.header.length = 44
        lsa_header_13.create_header(299, 0, 9, '0.0.16.0', '3.3.3.3', 0x80000001, conf.VERSION_IPV6)
        lsa_header_13.header.ls_checksum = 42557
        lsa_header_13.header.length = 44
        lsa_header_14.create_header(1, 0, 1, '0.0.0.0', '1.1.1.1', 0x80000007, conf.VERSION_IPV6)
        lsa_header_14.header.ls_checksum = 14352
        lsa_header_14.header.length = 72
        lsa_header_15.create_header(2, 0, 1, '0.0.0.0', '2.2.2.2', 0x80000005, conf.VERSION_IPV6)
        lsa_header_15.header.ls_checksum = 7870
        lsa_header_15.header.length = 40
        lsa_header_16.create_header(2, 0, 9, '0.0.0.0', '2.2.2.2', 0x80000004, conf.VERSION_IPV6)
        lsa_header_16.header.ls_checksum = 39510
        lsa_header_16.header.length = 56
        packet_body = ls_acknowledgment.LSAcknowledgement(conf.VERSION_IPV6)
        packet_body.add_lsa_header(lsa_header_1)
        packet_body.add_lsa_header(lsa_header_2)
        packet_body.add_lsa_header(lsa_header_3)
        packet_body.add_lsa_header(lsa_header_4)
        packet_body.add_lsa_header(lsa_header_5)
        packet_body.add_lsa_header(lsa_header_6)
        packet_body.add_lsa_header(lsa_header_7)
        packet_body.add_lsa_header(lsa_header_8)
        packet_body.add_lsa_header(lsa_header_9)
        packet_body.add_lsa_header(lsa_header_10)
        packet_body.add_lsa_header(lsa_header_11)
        packet_body.add_lsa_header(lsa_header_12)
        packet_body.add_lsa_header(lsa_header_13)
        packet_body.add_lsa_header(lsa_header_14)
        packet_body.add_lsa_header(lsa_header_15)
        packet_body.add_lsa_header(lsa_header_16)
        self.assertEqual(body_bytes, packet_body.pack_packet_body())

    #  Successful run - Instant
    def test_unpack_packet(self):
        #  OSPFv2

        body_bytes = b'\x01!"\x01\x02\x02\x02\x02\x02\x02\x02\x02\x80\x00\x00\x03\xf7&\x00<\x0e\x10"\x02\xde\xde\x03' \
                     b'\x02\x02\x02\x02\x02\x80\x00\x00\x02\xde\x83\x00 \x00\x02"\x01\x03\x03\x03\x03\x03\x03\x03\x03' \
                     b'\x80\x00\x00\x06\x07P\x00<\x00\x01"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x80\x00\x00\x05\xea' \
                     b'\xd2\x00T\x00\x01"\x02\xde\xde\x03\x01\x01\x01\x01\x01\x80\x00\x00\x01\x19O\x00 \x00\x02"\x02' \
                     b'\xde\xde\x05\x02\x03\x03\x03\x03\x80\x00\x00\x03\xfcV\x00 '
        unpacked_body = ls_acknowledgment.LSAcknowledgement.unpack_packet_body(body_bytes, conf.VERSION_IPV4)
        self.assertEqual(6, len(unpacked_body.lsa_headers))
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.version)

        unpacked_lsa = unpacked_body.lsa_headers[0]
        self.assertEqual(289, unpacked_lsa.header.ls_age)
        self.assertEqual(34, unpacked_lsa.header.options)
        self.assertEqual(1, unpacked_lsa.header.ls_type)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000003, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(63270, unpacked_lsa.header.ls_checksum)
        self.assertEqual(60, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[1]
        self.assertEqual(3600, unpacked_lsa.header.ls_age)
        self.assertEqual(34, unpacked_lsa.header.options)
        self.assertEqual(2, unpacked_lsa.header.ls_type)
        self.assertEqual('222.222.3.2', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000002, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(56963, unpacked_lsa.header.ls_checksum)
        self.assertEqual(32, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[2]
        self.assertEqual(2, unpacked_lsa.header.ls_age)
        self.assertEqual(34, unpacked_lsa.header.options)
        self.assertEqual(1, unpacked_lsa.header.ls_type)
        self.assertEqual('3.3.3.3', unpacked_lsa.header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000006, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(1872, unpacked_lsa.header.ls_checksum)
        self.assertEqual(60, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[3]
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(34, unpacked_lsa.header.options)
        self.assertEqual(1, unpacked_lsa.header.ls_type)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000005, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(60114, unpacked_lsa.header.ls_checksum)
        self.assertEqual(84, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[4]
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(34, unpacked_lsa.header.options)
        self.assertEqual(2, unpacked_lsa.header.ls_type)
        self.assertEqual('222.222.3.1', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000001, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(6479, unpacked_lsa.header.ls_checksum)
        self.assertEqual(32, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[5]
        self.assertEqual(2, unpacked_lsa.header.ls_age)
        self.assertEqual(34, unpacked_lsa.header.options)
        self.assertEqual(2, unpacked_lsa.header.ls_type)
        self.assertEqual('222.222.5.2', unpacked_lsa.header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000003, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(64598, unpacked_lsa.header.ls_checksum)
        self.assertEqual(32, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)

        #  OSPFv3

        body_bytes = b'\x00\n \x01\x00\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x06:\x0f\x00H\x01# \x01\x00\x00\x00' \
                     b'\x00\x02\x02\x02\x02\x80\x00\x00\x042}\x008\x00\t \x01\x00\x00\x00\x00\x03\x03\x03\x03\x80\x00' \
                     b'\x00\x06e\t\x008\x00\n \x02\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00\x00\x011\xc3\x00 \x01+ ' \
                     b'\x02\x00\x00\x00\x05\x02\x02\x02\x02\x80\x00\x00\x01\xf8\xf6\x00 \x01+ \x02\x00\x00\x00\x04' \
                     b'\x03\x03\x03\x03\x80\x00\x00\x019\xab\x00 \x01N\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x80' \
                     b'\x00\x00\x02\x80\xfe\x008\x01* \t\x00\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x03\x9c\x1f\x00D' \
                     b'\x00\n \t\x00\x00\x10\x00\x01\x01\x01\x01\x80\x00\x00\x01J\xab\x00,\x01+ \t\x00\x00\x00\x00' \
                     b'\x02\x02\x02\x02\x80\x00\x00\x03\xabJ\x00,\x01+ \t\x00\x00\x14\x00\x02\x02\x02\x02\x80\x00\x00' \
                     b'\x01<\xac\x00,\x01+ \t\x00\x00\x00\x00\x03\x03\x03\x03\x80\x00\x00\x03\xc3\xf1\x00,\x01+ \t' \
                     b'\x00\x00\x10\x00\x03\x03\x03\x03\x80\x00\x00\x01\xa6=\x00,\x00\x01 \x01\x00\x00\x00\x00\x01' \
                     b'\x01\x01\x01\x80\x00\x00\x078\x10\x00H\x00\x02 \x01\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00' \
                     b'\x00\x05\x1e\xbe\x00(\x00\x02 \t\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x04\x9aV\x008'
        unpacked_body = ls_acknowledgment.LSAcknowledgement.unpack_packet_body(body_bytes, conf.VERSION_IPV6)
        self.assertEqual(16, len(unpacked_body.lsa_headers))
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)

        unpacked_lsa = unpacked_body.lsa_headers[0]
        self.assertEqual(10, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2001, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000006, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(14863, unpacked_lsa.header.ls_checksum)
        self.assertEqual(72, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[1]
        self.assertEqual(291, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2001, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000004, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(12925, unpacked_lsa.header.ls_checksum)
        self.assertEqual(56, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[2]
        self.assertEqual(9, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2001, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000006, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(25865, unpacked_lsa.header.ls_checksum)
        self.assertEqual(56, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[3]
        self.assertEqual(10, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2002, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.4', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000001, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(12739, unpacked_lsa.header.ls_checksum)
        self.assertEqual(32, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[4]
        self.assertEqual(299, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2002, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.5', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000001, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(63734, unpacked_lsa.header.ls_checksum)
        self.assertEqual(32, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[5]
        self.assertEqual(299, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2002, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.4', unpacked_lsa.header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000001, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(14763, unpacked_lsa.header.ls_checksum)
        self.assertEqual(32, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[6]
        self.assertEqual(334, unpacked_lsa.header.ls_age)
        self.assertEqual(8, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.4', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000002, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(33022, unpacked_lsa.header.ls_checksum)
        self.assertEqual(56, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[7]
        self.assertEqual(298, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2009, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000003, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(39967, unpacked_lsa.header.ls_checksum)
        self.assertEqual(68, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[8]
        self.assertEqual(10, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2009, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.16.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000001, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(19115, unpacked_lsa.header.ls_checksum)
        self.assertEqual(44, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[9]
        self.assertEqual(299, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2009, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000003, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(43850, unpacked_lsa.header.ls_checksum)
        self.assertEqual(44, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[10]
        self.assertEqual(299, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2009, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.20.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000001, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(15532, unpacked_lsa.header.ls_checksum)
        self.assertEqual(44, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[11]
        self.assertEqual(299, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2009, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000003, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(50161, unpacked_lsa.header.ls_checksum)
        self.assertEqual(44, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[12]
        self.assertEqual(299, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2009, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.16.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000001, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(42557, unpacked_lsa.header.ls_checksum)
        self.assertEqual(44, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[13]
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2001, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000007, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(14352, unpacked_lsa.header.ls_checksum)
        self.assertEqual(72, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[14]
        self.assertEqual(2, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2001, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000005, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(7870, unpacked_lsa.header.ls_checksum)
        self.assertEqual(40, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)

        unpacked_lsa = unpacked_body.lsa_headers[15]
        self.assertEqual(2, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2009, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(0x80000004, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(39510, unpacked_lsa.header.ls_checksum)
        self.assertEqual(56, unpacked_lsa.header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)


if __name__ == '__main__':
    unittest.main()
