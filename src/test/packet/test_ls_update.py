import unittest

import lsa.lsa as lsa
import conf.conf as conf
import packet.ls_update as ls_update

'''
This class tests the OSPF Link State Update packet class and its operations
'''


#  Full successful run - Instant
class TestLSUpdate(unittest.TestCase):

    #  Successful run - Instant
    def test_pack_packet(self):
        #  OSPFv2

        body_bytes = b'\x00\x00\x00\x04\x00\x05"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x80\x00\x00\x04\x8c\xf3\x00T\x00' \
                     b'\x00\x00\x05\x03\x03\x03\x03\xde\xde\x06\x01\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00\x03' \
                     b'\x00\x00@\xde\xde\x03\x00\xff\xff\xff\x00\x03\x00\x00\n\xde\xde\x02\x00\xff\xff\xff\x00\x03' \
                     b'\x00\x00\n\xde\xde\x01\x00\xff\xff\xff\x00\x03\x00\x00\x01\x01!"\x01\x02\x02\x02\x02\x02\x02' \
                     b'\x02\x02\x80\x00\x00\x03\xf7&\x00<\x00\x00\x00\x03\xde\xde\x05\x02\xde\xde\x05\x01\x02\x00\x00' \
                     b'\x01\xde\xde\x04\x00\xff\xff\xff\x00\x03\x00\x00\n\xde\xde\x03\x02\xde\xde\x03\x02\x02\x00\x00' \
                     b'\n\x00\x06"\x01\x03\x03\x03\x03\x03\x03\x03\x03\x80\x00\x00\x05\x16\x08\x00<\x00\x00\x00\x03' \
                     b'\x01\x01\x01\x01\xde\xde\x06\x02\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00\x03\x00\x00@\xde' \
                     b'\xde\x05\x00\xff\xff\xff\x00\x03\x00\x00\n\x01!"\x02\xde\xde\x03\x02\x02\x02\x02\x02\x80\x00' \
                     b'\x00\x01\xe0\x82\x00 \xff\xff\xff\x00\x02\x02\x02\x02\x01\x01\x01\x01'

        lsa_1 = lsa.Lsa()
        lsa_2 = lsa.Lsa()
        lsa_3 = lsa.Lsa()
        lsa_4 = lsa.Lsa()
        lsa_1.create_header(5, 34, 1, '1.1.1.1', '1.1.1.1', 0x80000004, conf.VERSION_IPV4)
        lsa_2.create_header(289, 34, 1, '2.2.2.2', '2.2.2.2', 0x80000003, conf.VERSION_IPV4)
        lsa_3.create_header(6, 34, 1, '3.3.3.3', '3.3.3.3', 0x80000005, conf.VERSION_IPV4)
        lsa_4.create_header(289, 34, 2, '222.222.3.2', '2.2.2.2', 0x80000001, conf.VERSION_IPV4)
        lsa_1.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        lsa_1.add_link_info_v2('3.3.3.3', '222.222.6.1', 1, 0, 64)
        lsa_1.add_link_info_v2('222.222.6.0', '255.255.255.0', 3, 0, 64)
        lsa_1.add_link_info_v2('222.222.3.0', '255.255.255.0', 3, 0, 10)
        lsa_1.add_link_info_v2('222.222.2.0', '255.255.255.0', 3, 0, 10)
        lsa_1.add_link_info_v2('222.222.1.0', '255.255.255.0', 3, 0, 1)
        lsa_2.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        lsa_2.add_link_info_v2('222.222.5.2', '222.222.5.1', 2, 0, 1)
        lsa_2.add_link_info_v2('222.222.4.0', '255.255.255.0', 3, 0, 10)
        lsa_2.add_link_info_v2('222.222.3.2', '222.222.3.2', 2, 0, 10)
        lsa_3.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        lsa_3.add_link_info_v2('1.1.1.1', '222.222.6.2', 1, 0, 64)
        lsa_3.add_link_info_v2('222.222.6.0', '255.255.255.0', 3, 0, 64)
        lsa_3.add_link_info_v2('222.222.5.0', '255.255.255.0', 3, 0, 10)
        lsa_4.create_network_lsa_body('255.255.255.0', 0, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV4)

        packet_body = ls_update.LSUpdate(conf.VERSION_IPV4)
        packet_body.add_lsa(lsa_1)
        packet_body.add_lsa(lsa_2)
        packet_body.add_lsa(lsa_3)
        packet_body.add_lsa(lsa_4)
        self.assertEqual(body_bytes, packet_body.pack_packet_body())

        #  OSPFv3

        body_bytes = b'\x00\x00\x00\r\x00\n \x01\x00\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x06:\x0f\x00H\x00\x00' \
                     b'\x003\x01\x00\x00@\x00\x00\x00\x07\x00\x00\x00\x06\x03\x03\x03\x03\x02\x00\x00\n\x00\x00\x00' \
                     b'\x04\x00\x00\x00\x05\x02\x02\x02\x02\x02\x00\x00\n\x00\x00\x00\x04\x00\x00\x00\x04\x01\x01\x01' \
                     b'\x01\x01# \x01\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x042}\x008\x00\x00\x003\x02\x00\x00' \
                     b'\x01\x00\x00\x00\x06\x00\x00\x00\x04\x03\x03\x03\x03\x02\x00\x00\n\x00\x00\x00\x05\x00\x00\x00' \
                     b'\x05\x02\x02\x02\x02\x00\t \x01\x00\x00\x00\x00\x03\x03\x03\x03\x80\x00\x00\x06e\t\x008\x00' \
                     b'\x00\x003\x01\x00\x00@\x00\x00\x00\x06\x00\x00\x00\x07\x01\x01\x01\x01\x02\x00\x00\n\x00\x00' \
                     b'\x00\x04\x00\x00\x00\x04\x03\x03\x03\x03\x00\n \x02\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00' \
                     b'\x00\x011\xc3\x00 \x00\x00\x003\x01\x01\x01\x01\x02\x02\x02\x02\x01+ \x02\x00\x00\x00\x05\x02' \
                     b'\x02\x02\x02\x80\x00\x00\x01\xf8\xf6\x00 \x00\x00\x003\x02\x02\x02\x02\x01\x01\x01\x01\x01+ ' \
                     b'\x02\x00\x00\x00\x04\x03\x03\x03\x03\x80\x00\x00\x019\xab\x00 \x00\x00\x003\x03\x03\x03\x03' \
                     b'\x02\x02\x02\x02\x01N\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00\x00\x02\x80\xfe\x008\x01' \
                     b'\x00\x003\xfe\x80\x00\x00\x00\x00\x00\x00\xc0\x01\x18\xff\xfe4\x00\x00\x00\x00\x00\x01@\x00' \
                     b'\x00\x00 \x01\r\xb8\xca\xfe\x00\x03\x01* \t\x00\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x03' \
                     b'\x9c\x1f\x00D\x00\x03 \x01\x00\x00\x00\x00\x01\x01\x01\x01@\x00\x00@ \x01\r\xb8\xca\xfe\x00' \
                     b'\x06@\x00\x00\x01 \x01\r\xb8\xca\xfe\x00\x01@\x00\x00\n \x01\r\xb8\xca\xfe\x00\x02\x00\n \t' \
                     b'\x00\x00\x10\x00\x01\x01\x01\x01\x80\x00\x00\x01J\xab\x00,\x00\x01 \x02\x00\x00\x00\x04\x01' \
                     b'\x01\x01\x01@\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x03\x01+ \t\x00\x00\x00\x00\x02\x02\x02\x02' \
                     b'\x80\x00\x00\x03\xabJ\x00,\x00\x01 \x01\x00\x00\x00\x00\x02\x02\x02\x02@\x00\x00\n \x01\r\xb8' \
                     b'\xca\xfe\x00\x04\x01+ \t\x00\x00\x14\x00\x02\x02\x02\x02\x80\x00\x00\x01<\xac\x00,\x00\x01 ' \
                     b'\x02\x00\x00\x00\x05\x02\x02\x02\x02@\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x03\x01+ \t\x00\x00' \
                     b'\x00\x00\x03\x03\x03\x03\x80\x00\x00\x03\xc3\xf1\x00,\x00\x01 \x01\x00\x00\x00\x00\x03\x03\x03' \
                     b'\x03@\x00\x00@ \x01\r\xb8\xca\xfe\x00\x06\x01+ \t\x00\x00\x10\x00\x03\x03\x03\x03\x80\x00\x00' \
                     b'\x01\xa6=\x00,\x00\x01 \x02\x00\x00\x00\x04\x03\x03\x03\x03@\x00\x00\x00 \x01\r\xb8\xca\xfe' \
                     b'\x00\x05'

        lsa_1 = lsa.Lsa()
        lsa_2 = lsa.Lsa()
        lsa_3 = lsa.Lsa()
        lsa_4 = lsa.Lsa()
        lsa_5 = lsa.Lsa()
        lsa_6 = lsa.Lsa()
        lsa_7 = lsa.Lsa()
        lsa_8 = lsa.Lsa()
        lsa_9 = lsa.Lsa()
        lsa_10 = lsa.Lsa()
        lsa_11 = lsa.Lsa()
        lsa_12 = lsa.Lsa()
        lsa_13 = lsa.Lsa()
        lsa_1.create_header(10, 0, 1, '0.0.0.0', '1.1.1.1', 0x80000006, conf.VERSION_IPV6)
        lsa_2.create_header(291, 0, 1, '0.0.0.0', '2.2.2.2', 0x80000004, conf.VERSION_IPV6)
        lsa_3.create_header(9, 0, 1, '0.0.0.0', '3.3.3.3', 0x80000006, conf.VERSION_IPV6)
        lsa_4.create_header(10, 0, 2, '0.0.0.4', '1.1.1.1', 0x80000001, conf.VERSION_IPV6)
        lsa_5.create_header(299, 0, 2, '0.0.0.5', '2.2.2.2', 0x80000001, conf.VERSION_IPV6)
        lsa_6.create_header(299, 0, 2, '0.0.0.4', '3.3.3.3', 0x80000001, conf.VERSION_IPV6)
        lsa_7.create_header(334, 0, 8, '0.0.0.4', '1.1.1.1', 0x80000002, conf.VERSION_IPV6)
        lsa_8.create_header(298, 0, 9, '0.0.0.0', '1.1.1.1', 0x80000003, conf.VERSION_IPV6)
        lsa_9.create_header(10, 0, 9, '0.0.16.0', '1.1.1.1', 0x80000001, conf.VERSION_IPV6)
        lsa_10.create_header(299, 0, 9, '0.0.0.0', '2.2.2.2', 0x80000003, conf.VERSION_IPV6)
        lsa_11.create_header(299, 0, 9, '0.0.20.0', '2.2.2.2', 0x80000001, conf.VERSION_IPV6)
        lsa_12.create_header(299, 0, 9, '0.0.0.0', '3.3.3.3', 0x80000003, conf.VERSION_IPV6)
        lsa_13.create_header(299, 0, 9, '0.0.16.0', '3.3.3.3', 0x80000001, conf.VERSION_IPV6)
        lsa_1.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        lsa_1.add_link_info_v3(1, 64, 7, 6, '3.3.3.3')
        lsa_1.add_link_info_v3(2, 10, 4, 5, '2.2.2.2')
        lsa_1.add_link_info_v3(2, 10, 4, 4, '1.1.1.1')
        lsa_2.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        lsa_2.add_link_info_v3(2, 1, 6, 4, '3.3.3.3')
        lsa_2.add_link_info_v3(2, 10, 5, 5, '2.2.2.2')
        lsa_3.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        lsa_3.add_link_info_v3(1, 64, 6, 7, '1.1.1.1')
        lsa_3.add_link_info_v3(2, 10, 4, 4, '3.3.3.3')
        lsa_4.create_network_lsa_body('', 51, ['1.1.1.1', '2.2.2.2'], conf.VERSION_IPV6)
        lsa_5.create_network_lsa_body('', 51, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV6)
        lsa_6.create_network_lsa_body('', 51, ['3.3.3.3', '2.2.2.2'], conf.VERSION_IPV6)
        lsa_7.create_link_lsa_body(1, 51, 'fe80::c001:18ff:fe34:0')
        lsa_7.add_prefix_info(64, 0, 0, '2001:db8:cafe:3::', conf.LSA_TYPE_LINK)
        lsa_8.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '1.1.1.1')
        lsa_8.add_prefix_info(64, 0, 64, '2001:db8:cafe:6::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsa_8.add_prefix_info(64, 0, 1, '2001:db8:cafe:1::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsa_8.add_prefix_info(64, 0, 10, '2001:db8:cafe:2::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsa_9.create_intra_area_prefix_lsa_body(2, '0.0.0.4', '1.1.1.1')
        lsa_9.add_prefix_info(64, 0, 0, '2001:db8:cafe:3::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsa_10.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '2.2.2.2')
        lsa_10.add_prefix_info(64, 0, 10, '2001:db8:cafe:4::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsa_11.create_intra_area_prefix_lsa_body(2, '0.0.0.5', '2.2.2.2')
        lsa_11.add_prefix_info(64, 0, 0, '2001:db8:cafe:3::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsa_12.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '3.3.3.3')
        lsa_12.add_prefix_info(64, 0, 64, '2001:db8:cafe:6::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsa_13.create_intra_area_prefix_lsa_body(2, '0.0.0.4', '3.3.3.3')
        lsa_13.add_prefix_info(64, 0, 0, '2001:db8:cafe:5::', conf.LSA_TYPE_INTRA_AREA_PREFIX)

        packet_body = ls_update.LSUpdate(conf.VERSION_IPV6)
        packet_body.add_lsa(lsa_1)
        packet_body.add_lsa(lsa_2)
        packet_body.add_lsa(lsa_3)
        packet_body.add_lsa(lsa_4)
        packet_body.add_lsa(lsa_5)
        packet_body.add_lsa(lsa_6)
        packet_body.add_lsa(lsa_7)
        packet_body.add_lsa(lsa_8)
        packet_body.add_lsa(lsa_9)
        packet_body.add_lsa(lsa_10)
        packet_body.add_lsa(lsa_11)
        packet_body.add_lsa(lsa_12)
        packet_body.add_lsa(lsa_13)
        self.assertEqual(body_bytes, packet_body.pack_packet_body())

    #  Successful run - Instant
    def test_unpack_packet(self):
        #  OSPFv2

        body_bytes = b'\x00\x00\x00\x04\x00\x05"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x80\x00\x00\x04\x8c\xf3\x00T\x00' \
                     b'\x00\x00\x05\x03\x03\x03\x03\xde\xde\x06\x01\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00\x03' \
                     b'\x00\x00@\xde\xde\x03\x00\xff\xff\xff\x00\x03\x00\x00\n\xde\xde\x02\x00\xff\xff\xff\x00\x03' \
                     b'\x00\x00\n\xde\xde\x01\x00\xff\xff\xff\x00\x03\x00\x00\x01\x01!"\x01\x02\x02\x02\x02\x02\x02' \
                     b'\x02\x02\x80\x00\x00\x03\xf7&\x00<\x00\x00\x00\x03\xde\xde\x05\x02\xde\xde\x05\x01\x02\x00\x00' \
                     b'\x01\xde\xde\x04\x00\xff\xff\xff\x00\x03\x00\x00\n\xde\xde\x03\x02\xde\xde\x03\x02\x02\x00\x00' \
                     b'\n\x00\x06"\x01\x03\x03\x03\x03\x03\x03\x03\x03\x80\x00\x00\x05\x16\x08\x00<\x00\x00\x00\x03' \
                     b'\x01\x01\x01\x01\xde\xde\x06\x02\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00\x03\x00\x00@\xde' \
                     b'\xde\x05\x00\xff\xff\xff\x00\x03\x00\x00\n\x01!"\x02\xde\xde\x03\x02\x02\x02\x02\x02\x80\x00' \
                     b'\x00\x01\xe0\x82\x00 \xff\xff\xff\x00\x02\x02\x02\x02\x01\x01\x01\x01'

        unpacked_body = ls_update.LSUpdate.unpack_packet_body(body_bytes, conf.VERSION_IPV4)
        self.assertEqual(4, unpacked_body.lsa_number)
        self.assertEqual(4, len(unpacked_body.lsa_list))
        self.assertEqual(5, unpacked_body.lsa_list[0].header.ls_age)
        self.assertEqual(34, unpacked_body.lsa_list[0].header.options)
        self.assertEqual(1, unpacked_body.lsa_list[0].header.ls_type)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[0].header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[0].header.advertising_router)
        self.assertEqual(0x80000004, unpacked_body.lsa_list[0].header.ls_sequence_number)
        self.assertEqual(36083, unpacked_body.lsa_list[0].header.ls_checksum)
        self.assertEqual(84, unpacked_body.lsa_list[0].header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.lsa_list[0].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.version)
        self.assertFalse(unpacked_body.lsa_list[0].body.bit_v)
        self.assertFalse(unpacked_body.lsa_list[0].body.bit_e)
        self.assertFalse(unpacked_body.lsa_list[0].body.bit_b)
        self.assertEqual(5, unpacked_body.lsa_list[0].body.link_number)
        self.assertEqual([['3.3.3.3', '222.222.6.1', 1, 0, 64], ['222.222.6.0', '255.255.255.0', 3, 0, 64],
                          ['222.222.3.0', '255.255.255.0', 3, 0, 10], ['222.222.2.0', '255.255.255.0', 3, 0, 10],
                          ['222.222.1.0', '255.255.255.0', 3, 0, 1]], unpacked_body.lsa_list[0].body.links)

        self.assertEqual(289, unpacked_body.lsa_list[1].header.ls_age)
        self.assertEqual(34, unpacked_body.lsa_list[1].header.options)
        self.assertEqual(1, unpacked_body.lsa_list[1].header.ls_type)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[1].header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[1].header.advertising_router)
        self.assertEqual(0x80000003, unpacked_body.lsa_list[1].header.ls_sequence_number)
        self.assertEqual(63270, unpacked_body.lsa_list[1].header.ls_checksum)
        self.assertEqual(60, unpacked_body.lsa_list[1].header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.lsa_list[1].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.version)
        self.assertFalse(unpacked_body.lsa_list[1].body.bit_v)
        self.assertFalse(unpacked_body.lsa_list[1].body.bit_e)
        self.assertFalse(unpacked_body.lsa_list[1].body.bit_b)
        self.assertEqual(3, unpacked_body.lsa_list[1].body.link_number)
        self.assertEqual([['222.222.5.2', '222.222.5.1', 2, 0, 1], ['222.222.4.0', '255.255.255.0', 3, 0, 10],
                          ['222.222.3.2', '222.222.3.2', 2, 0, 10]], unpacked_body.lsa_list[1].body.links)

        self.assertEqual(6, unpacked_body.lsa_list[2].header.ls_age)
        self.assertEqual(34, unpacked_body.lsa_list[2].header.options)
        self.assertEqual(1, unpacked_body.lsa_list[2].header.ls_type)
        self.assertEqual('3.3.3.3', unpacked_body.lsa_list[2].header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_body.lsa_list[2].header.advertising_router)
        self.assertEqual(0x80000005, unpacked_body.lsa_list[2].header.ls_sequence_number)
        self.assertEqual(5640, unpacked_body.lsa_list[2].header.ls_checksum)
        self.assertEqual(60, unpacked_body.lsa_list[2].header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.lsa_list[2].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.version)
        self.assertFalse(unpacked_body.lsa_list[2].body.bit_v)
        self.assertFalse(unpacked_body.lsa_list[2].body.bit_e)
        self.assertFalse(unpacked_body.lsa_list[2].body.bit_b)
        self.assertEqual(3, unpacked_body.lsa_list[2].body.link_number)
        self.assertEqual([['1.1.1.1', '222.222.6.2', 1, 0, 64], ['222.222.6.0', '255.255.255.0', 3, 0, 64],
                          ['222.222.5.0', '255.255.255.0', 3, 0, 10]], unpacked_body.lsa_list[2].body.links)

        self.assertEqual(289, unpacked_body.lsa_list[3].header.ls_age)
        self.assertEqual(34, unpacked_body.lsa_list[3].header.options)
        self.assertEqual(2, unpacked_body.lsa_list[3].header.ls_type)
        self.assertEqual('222.222.3.2', unpacked_body.lsa_list[3].header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[3].header.advertising_router)
        self.assertEqual(0x80000001, unpacked_body.lsa_list[3].header.ls_sequence_number)
        self.assertEqual(57474, unpacked_body.lsa_list[3].header.ls_checksum)
        self.assertEqual(32, unpacked_body.lsa_list[3].header.length)
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.lsa_list[3].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV4, unpacked_body.version)
        self.assertEqual('255.255.255.0', unpacked_body.lsa_list[3].body.network_mask)
        self.assertEqual(['2.2.2.2', '1.1.1.1'], unpacked_body.lsa_list[3].body.attached_routers)

        #  OSPFv3

        body_bytes = b'\x00\x00\x00\r\x00\n \x01\x00\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x06:\x0f\x00H\x00\x00' \
                     b'\x003\x01\x00\x00@\x00\x00\x00\x07\x00\x00\x00\x06\x03\x03\x03\x03\x02\x00\x00\n\x00\x00\x00' \
                     b'\x04\x00\x00\x00\x05\x02\x02\x02\x02\x02\x00\x00\n\x00\x00\x00\x04\x00\x00\x00\x04\x01\x01\x01' \
                     b'\x01\x01# \x01\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x042}\x008\x00\x00\x003\x02\x00\x00' \
                     b'\x01\x00\x00\x00\x06\x00\x00\x00\x04\x03\x03\x03\x03\x02\x00\x00\n\x00\x00\x00\x05\x00\x00\x00' \
                     b'\x05\x02\x02\x02\x02\x00\t \x01\x00\x00\x00\x00\x03\x03\x03\x03\x80\x00\x00\x06e\t\x008\x00' \
                     b'\x00\x003\x01\x00\x00@\x00\x00\x00\x06\x00\x00\x00\x07\x01\x01\x01\x01\x02\x00\x00\n\x00\x00' \
                     b'\x00\x04\x00\x00\x00\x04\x03\x03\x03\x03\x00\n \x02\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00' \
                     b'\x00\x011\xc3\x00 \x00\x00\x003\x01\x01\x01\x01\x02\x02\x02\x02\x01+ \x02\x00\x00\x00\x05\x02' \
                     b'\x02\x02\x02\x80\x00\x00\x01\xf8\xf6\x00 \x00\x00\x003\x02\x02\x02\x02\x01\x01\x01\x01\x01+ ' \
                     b'\x02\x00\x00\x00\x04\x03\x03\x03\x03\x80\x00\x00\x019\xab\x00 \x00\x00\x003\x03\x03\x03\x03' \
                     b'\x02\x02\x02\x02\x01N\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00\x00\x02\x80\xfe\x008\x01' \
                     b'\x00\x003\xfe\x80\x00\x00\x00\x00\x00\x00\xc0\x01\x18\xff\xfe4\x00\x00\x00\x00\x00\x01@\x00' \
                     b'\x00\x00 \x01\r\xb8\xca\xfe\x00\x03\x01* \t\x00\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x03' \
                     b'\x9c\x1f\x00D\x00\x03 \x01\x00\x00\x00\x00\x01\x01\x01\x01@\x00\x00@ \x01\r\xb8\xca\xfe\x00' \
                     b'\x06@\x00\x00\x01 \x01\r\xb8\xca\xfe\x00\x01@\x00\x00\n \x01\r\xb8\xca\xfe\x00\x02\x00\n \t' \
                     b'\x00\x00\x10\x00\x01\x01\x01\x01\x80\x00\x00\x01J\xab\x00,\x00\x01 \x02\x00\x00\x00\x04\x01' \
                     b'\x01\x01\x01@\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x03\x01+ \t\x00\x00\x00\x00\x02\x02\x02\x02' \
                     b'\x80\x00\x00\x03\xabJ\x00,\x00\x01 \x01\x00\x00\x00\x00\x02\x02\x02\x02@\x00\x00\n \x01\r\xb8' \
                     b'\xca\xfe\x00\x04\x01+ \t\x00\x00\x14\x00\x02\x02\x02\x02\x80\x00\x00\x01<\xac\x00,\x00\x01 ' \
                     b'\x02\x00\x00\x00\x05\x02\x02\x02\x02@\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x03\x01+ \t\x00\x00' \
                     b'\x00\x00\x03\x03\x03\x03\x80\x00\x00\x03\xc3\xf1\x00,\x00\x01 \x01\x00\x00\x00\x00\x03\x03\x03' \
                     b'\x03@\x00\x00@ \x01\r\xb8\xca\xfe\x00\x06\x01+ \t\x00\x00\x10\x00\x03\x03\x03\x03\x80\x00\x00' \
                     b'\x01\xa6=\x00,\x00\x01 \x02\x00\x00\x00\x04\x03\x03\x03\x03@\x00\x00\x00 \x01\r\xb8\xca\xfe' \
                     b'\x00\x05'

        unpacked_body = ls_update.LSUpdate.unpack_packet_body(body_bytes, conf.VERSION_IPV6)
        self.assertEqual(13, unpacked_body.lsa_number)
        self.assertEqual(13, len(unpacked_body.lsa_list))
        self.assertEqual(10, unpacked_body.lsa_list[0].header.ls_age)
        self.assertEqual(0x2001, unpacked_body.lsa_list[0].header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[0].header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[0].header.advertising_router)
        self.assertEqual(0x80000006, unpacked_body.lsa_list[0].header.ls_sequence_number)
        self.assertEqual(14863, unpacked_body.lsa_list[0].header.ls_checksum)
        self.assertEqual(72, unpacked_body.lsa_list[0].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[0].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertFalse(unpacked_body.lsa_list[0].body.bit_v)
        self.assertFalse(unpacked_body.lsa_list[0].body.bit_e)
        self.assertFalse(unpacked_body.lsa_list[0].body.bit_b)
        self.assertEqual(51, unpacked_body.lsa_list[0].body.options)
        self.assertEqual([[1, 64, 7, 6, '3.3.3.3'], [2, 10, 4, 5, '2.2.2.2'], [2, 10, 4, 4, '1.1.1.1']],
                         unpacked_body.lsa_list[0].body.links)

        self.assertEqual(291, unpacked_body.lsa_list[1].header.ls_age)
        self.assertEqual(0x2001, unpacked_body.lsa_list[1].header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[1].header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[1].header.advertising_router)
        self.assertEqual(0x80000004, unpacked_body.lsa_list[1].header.ls_sequence_number)
        self.assertEqual(12925, unpacked_body.lsa_list[1].header.ls_checksum)
        self.assertEqual(56, unpacked_body.lsa_list[1].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[1].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertFalse(unpacked_body.lsa_list[1].body.bit_v)
        self.assertFalse(unpacked_body.lsa_list[1].body.bit_e)
        self.assertFalse(unpacked_body.lsa_list[1].body.bit_b)
        self.assertEqual(51, unpacked_body.lsa_list[1].body.options)
        self.assertEqual([[2, 1, 6, 4, '3.3.3.3'], [2, 10, 5, 5, '2.2.2.2']], unpacked_body.lsa_list[1].body.links)

        self.assertEqual(9, unpacked_body.lsa_list[2].header.ls_age)
        self.assertEqual(0x2001, unpacked_body.lsa_list[2].header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[2].header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_body.lsa_list[2].header.advertising_router)
        self.assertEqual(0x80000006, unpacked_body.lsa_list[2].header.ls_sequence_number)
        self.assertEqual(25865, unpacked_body.lsa_list[2].header.ls_checksum)
        self.assertEqual(56, unpacked_body.lsa_list[2].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[2].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertFalse(unpacked_body.lsa_list[2].body.bit_v)
        self.assertFalse(unpacked_body.lsa_list[2].body.bit_e)
        self.assertFalse(unpacked_body.lsa_list[2].body.bit_b)
        self.assertEqual(51, unpacked_body.lsa_list[2].body.options)
        self.assertEqual([[1, 64, 6, 7, '1.1.1.1'], [2, 10, 4, 4, '3.3.3.3']], unpacked_body.lsa_list[2].body.links)

        self.assertEqual(10, unpacked_body.lsa_list[3].header.ls_age)
        self.assertEqual(0x2002, unpacked_body.lsa_list[3].header.ls_type)
        self.assertEqual('0.0.0.4', unpacked_body.lsa_list[3].header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[3].header.advertising_router)
        self.assertEqual(0x80000001, unpacked_body.lsa_list[3].header.ls_sequence_number)
        self.assertEqual(12739, unpacked_body.lsa_list[3].header.ls_checksum)
        self.assertEqual(32, unpacked_body.lsa_list[3].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[3].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(51, unpacked_body.lsa_list[3].body.options)
        self.assertEqual(['1.1.1.1', '2.2.2.2'], unpacked_body.lsa_list[3].body.attached_routers)

        self.assertEqual(299, unpacked_body.lsa_list[4].header.ls_age)
        self.assertEqual(0x2002, unpacked_body.lsa_list[4].header.ls_type)
        self.assertEqual('0.0.0.5', unpacked_body.lsa_list[4].header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[4].header.advertising_router)
        self.assertEqual(0x80000001, unpacked_body.lsa_list[4].header.ls_sequence_number)
        self.assertEqual(63734, unpacked_body.lsa_list[4].header.ls_checksum)
        self.assertEqual(32, unpacked_body.lsa_list[4].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[4].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(51, unpacked_body.lsa_list[4].body.options)
        self.assertEqual(['2.2.2.2', '1.1.1.1'], unpacked_body.lsa_list[4].body.attached_routers)

        self.assertEqual(299, unpacked_body.lsa_list[5].header.ls_age)
        self.assertEqual(0x2002, unpacked_body.lsa_list[5].header.ls_type)
        self.assertEqual('0.0.0.4', unpacked_body.lsa_list[5].header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_body.lsa_list[5].header.advertising_router)
        self.assertEqual(0x80000001, unpacked_body.lsa_list[5].header.ls_sequence_number)
        self.assertEqual(14763, unpacked_body.lsa_list[5].header.ls_checksum)
        self.assertEqual(32, unpacked_body.lsa_list[5].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[5].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(51, unpacked_body.lsa_list[5].body.options)
        self.assertEqual(['3.3.3.3', '2.2.2.2'], unpacked_body.lsa_list[5].body.attached_routers)

        self.assertEqual(334, unpacked_body.lsa_list[6].header.ls_age)
        self.assertEqual(8, unpacked_body.lsa_list[6].header.ls_type)
        self.assertEqual('0.0.0.4', unpacked_body.lsa_list[6].header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[6].header.advertising_router)
        self.assertEqual(0x80000002, unpacked_body.lsa_list[6].header.ls_sequence_number)
        self.assertEqual(33022, unpacked_body.lsa_list[6].header.ls_checksum)
        self.assertEqual(56, unpacked_body.lsa_list[6].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[6].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(1, unpacked_body.lsa_list[6].body.router_priority)
        self.assertEqual(51, unpacked_body.lsa_list[6].body.options)
        self.assertEqual('fe80::c001:18ff:fe34:0', unpacked_body.lsa_list[6].body.link_local_address)
        self.assertEqual(1, unpacked_body.lsa_list[6].body.prefix_number)
        self.assertEqual([[64, 0, '2001:db8:cafe:3::']], unpacked_body.lsa_list[6].body.prefixes)

        self.assertEqual(298, unpacked_body.lsa_list[7].header.ls_age)
        self.assertEqual(0x2009, unpacked_body.lsa_list[7].header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[7].header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[7].header.advertising_router)
        self.assertEqual(0x80000003, unpacked_body.lsa_list[7].header.ls_sequence_number)
        self.assertEqual(39967, unpacked_body.lsa_list[7].header.ls_checksum)
        self.assertEqual(68, unpacked_body.lsa_list[7].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[7].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(3, unpacked_body.lsa_list[7].body.prefix_number)
        self.assertEqual(0x2001, unpacked_body.lsa_list[7].body.referenced_ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[7].body.referenced_link_state_id)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[7].body.referenced_advertising_router)
        self.assertEqual([[64, 0, 64, '2001:db8:cafe:6::'], [64, 0, 1, '2001:db8:cafe:1::'],
                          [64, 0, 10, '2001:db8:cafe:2::']], unpacked_body.lsa_list[7].body.prefixes)

        self.assertEqual(10, unpacked_body.lsa_list[8].header.ls_age)
        self.assertEqual(0x2009, unpacked_body.lsa_list[8].header.ls_type)
        self.assertEqual('0.0.16.0', unpacked_body.lsa_list[8].header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[8].header.advertising_router)
        self.assertEqual(0x80000001, unpacked_body.lsa_list[8].header.ls_sequence_number)
        self.assertEqual(19115, unpacked_body.lsa_list[8].header.ls_checksum)
        self.assertEqual(44, unpacked_body.lsa_list[8].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[8].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(1, unpacked_body.lsa_list[8].body.prefix_number)
        self.assertEqual(0x2002, unpacked_body.lsa_list[8].body.referenced_ls_type)
        self.assertEqual('0.0.0.4', unpacked_body.lsa_list[8].body.referenced_link_state_id)
        self.assertEqual('1.1.1.1', unpacked_body.lsa_list[8].body.referenced_advertising_router)
        self.assertEqual([[64, 0, 0, '2001:db8:cafe:3::']], unpacked_body.lsa_list[8].body.prefixes)

        self.assertEqual(299, unpacked_body.lsa_list[9].header.ls_age)
        self.assertEqual(0x2009, unpacked_body.lsa_list[9].header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[9].header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[9].header.advertising_router)
        self.assertEqual(0x80000003, unpacked_body.lsa_list[9].header.ls_sequence_number)
        self.assertEqual(43850, unpacked_body.lsa_list[9].header.ls_checksum)
        self.assertEqual(44, unpacked_body.lsa_list[9].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[9].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(1, unpacked_body.lsa_list[9].body.prefix_number)
        self.assertEqual(0x2001, unpacked_body.lsa_list[9].body.referenced_ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[9].body.referenced_link_state_id)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[9].body.referenced_advertising_router)
        self.assertEqual([[64, 0, 10, '2001:db8:cafe:4::']], unpacked_body.lsa_list[9].body.prefixes)

        self.assertEqual(299, unpacked_body.lsa_list[10].header.ls_age)
        self.assertEqual(0x2009, unpacked_body.lsa_list[10].header.ls_type)
        self.assertEqual('0.0.20.0', unpacked_body.lsa_list[10].header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[10].header.advertising_router)
        self.assertEqual(0x80000001, unpacked_body.lsa_list[10].header.ls_sequence_number)
        self.assertEqual(15532, unpacked_body.lsa_list[10].header.ls_checksum)
        self.assertEqual(44, unpacked_body.lsa_list[10].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[10].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(1, unpacked_body.lsa_list[10].body.prefix_number)
        self.assertEqual(0x2002, unpacked_body.lsa_list[10].body.referenced_ls_type)
        self.assertEqual('0.0.0.5', unpacked_body.lsa_list[10].body.referenced_link_state_id)
        self.assertEqual('2.2.2.2', unpacked_body.lsa_list[10].body.referenced_advertising_router)
        self.assertEqual([[64, 0, 0, '2001:db8:cafe:3::']], unpacked_body.lsa_list[10].body.prefixes)

        self.assertEqual(299, unpacked_body.lsa_list[11].header.ls_age)
        self.assertEqual(0x2009, unpacked_body.lsa_list[11].header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[11].header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_body.lsa_list[11].header.advertising_router)
        self.assertEqual(0x80000003, unpacked_body.lsa_list[11].header.ls_sequence_number)
        self.assertEqual(50161, unpacked_body.lsa_list[11].header.ls_checksum)
        self.assertEqual(44, unpacked_body.lsa_list[11].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[11].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(1, unpacked_body.lsa_list[11].body.prefix_number)
        self.assertEqual(0x2001, unpacked_body.lsa_list[11].body.referenced_ls_type)
        self.assertEqual('0.0.0.0', unpacked_body.lsa_list[11].body.referenced_link_state_id)
        self.assertEqual('3.3.3.3', unpacked_body.lsa_list[11].body.referenced_advertising_router)
        self.assertEqual([[64, 0, 64, '2001:db8:cafe:6::']], unpacked_body.lsa_list[11].body.prefixes)

        self.assertEqual(299, unpacked_body.lsa_list[12].header.ls_age)
        self.assertEqual(0x2009, unpacked_body.lsa_list[12].header.ls_type)
        self.assertEqual('0.0.16.0', unpacked_body.lsa_list[12].header.link_state_id)
        self.assertEqual('3.3.3.3', unpacked_body.lsa_list[12].header.advertising_router)
        self.assertEqual(0x80000001, unpacked_body.lsa_list[12].header.ls_sequence_number)
        self.assertEqual(42557, unpacked_body.lsa_list[12].header.ls_checksum)
        self.assertEqual(44, unpacked_body.lsa_list[12].header.length)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.lsa_list[12].header.ospf_version)
        self.assertEqual(conf.VERSION_IPV6, unpacked_body.version)
        self.assertEqual(1, unpacked_body.lsa_list[12].body.prefix_number)
        self.assertEqual(0x2002, unpacked_body.lsa_list[12].body.referenced_ls_type)
        self.assertEqual('0.0.0.4', unpacked_body.lsa_list[12].body.referenced_link_state_id)
        self.assertEqual('3.3.3.3', unpacked_body.lsa_list[12].body.referenced_advertising_router)
        self.assertEqual([[64, 0, 0, '2001:db8:cafe:5::']], unpacked_body.lsa_list[12].body.prefixes)
