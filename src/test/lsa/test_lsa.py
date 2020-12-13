import unittest

import lsa.lsa as lsa
import lsa.header as header
import conf.conf as conf
import general.utils as utils
import general.sock as sock
import packet.packet as packet

'''
This class tests the interface to LSA creation, storage and manipulation
'''


#  Full successful run - Instant
class TestLsa(unittest.TestCase):

    router_lsa_v2_bytes = b'\x00\x01"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x80\x00\x00\x06\x0b\xb0\x00T\x00\x00\x00' \
                          b'\x05\x03\x03\x03\x03\xde\xde\x06\x01\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00\x03\x00' \
                          b'\x00@\xde\xde\x03\x02\xde\xde\x03\x01\x02\x00\x00\n\xde\xde\x02\x00\xff\xff\xff\x00\x03' \
                          b'\x00\x00\n\xde\xde\x01\x00\xff\xff\xff\x00\x03\x00\x00\x01'
    router_lsa_v3_bytes = b'\x00\x01 \x01\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x07,\x80\x008\x00\x00\x003\x02' \
                          b'\x00\x00\x01\x00\x00\x00\x06\x00\x00\x00\x04\x03\x03\x03\x03\x02\x00\x00\n\x00\x00\x00' \
                          b'\x05\x00\x00\x00\x05\x02\x02\x02\x02'
    network_lsa_v2_bytes = b'\x00\x01"\x02\xde\xde\x03\x02\x02\x02\x02\x02\x80\x00\x00\x01\xe0\x82\x00 \xff\xff\xff' \
                           b'\x00\x02\x02\x02\x02\x01\x01\x01\x01'
    network_lsa_v3_bytes = b'\x00\x01 \x02\x00\x00\x00\x05\x02\x02\x02\x02\x80\x00\x00\x02\xf6\xf7\x00 \x00\x00\x003' \
                           b'\x02\x02\x02\x02\x01\x01\x01\x01'
    intra_area_prefix_lsa_bytes = b'\x00\x01 \t\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x05\xa7L\x00,\x00\x01 ' \
                                  b'\x01\x00\x00\x00\x00\x02\x02\x02\x02@\x00\x00\n \x01\r\xb8\xca\xfe\x00\x04'
    link_lsa_bytes = b'\x00&\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00\x00\x02\x80\xfe\x008\x01\x00\x003\xfe' \
                     b'\x80\x00\x00\x00\x00\x00\x00\xc0\x01\x18\xff\xfe4\x00\x00\x00\x00\x00\x01@\x00\x00\x00 \x01\r' \
                     b'\xb8\xca\xfe\x00\x03'
    summary_lsa_3_bytes = b'\x00\x14\x00\x03\xde\xde\x01\x00\x04\x04\x04\x04\x80\x00\x00\x01\xa6\xdf\x00\x1c\xff\xff' \
                          b'\xff\x00\x00\x00\x00\n'
    summary_lsa_4_bytes = b'\x00\x14\x00\x04\xde\xde\x01\x00\x04\x04\x04\x04\x80\x00\x00\x01\x98\xec\x00\x1c\xff\xff' \
                          b'\xff\x00\x00\x00\x00\n'
    inter_area_prefix_lsa_bytes = b'\x00\x14 \x03\x00\x00\x00\x01\x04\x04\x04\x04\x80\x00\x00\x01H\xe1\x00$\x00\x00' \
                                  b'\x00\n@\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x01'
    extension_abr_lsa_v2_bytes = b'\x00\x01\x00\x0b\x0b\x00\x00\x00\x04\x04\x04\x04\x80\x00\x00\x01\x1d\xec\x00$\x00' \
                                 b'\x00\x00\n\x01\x01\x01\x01\x00\x00\x00\x14\x02\x02\x02\x02'
    extension_abr_lsa_v3_bytes = b'\x00\n\xc0\x11\x00\x00\x00\x00\x04\x04\x04\x04\x80\x00\x00\x02e\xaf\x00$\x00\x00' \
                                 b'\x00\x1e\x03\x03\x03\x03\x00\x00\x00(\x04\x04\x04\x04'
    extension_prefix_lsa_v2_bytes = b'\x00\n\x00\x0b\x0c\x00\x00\x00\x01\x01\x01\x01\x80\x00\x00\x01\xc6T\x00D\x00' \
                                    b'\x00\x00\n\xff\xff\xff\x00\xde\xde\x01\x00\x00\x00\x00\x14\xff\xff\x00\x00\xde' \
                                    b'\x01\x00\x00\x00\x00\x00\x1e\xff\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00(\x00' \
                                    b'\x00\x00\x00\x00\x00\x00\x00'
    extension_prefix_lsa_v3_bytes = b'\x00\n\xc0\x12\x00\x00\x00\x00\x04\x04\x04\x04\x80\x00\x00\x02\xf7a\x00h\x00' \
                                    b'\x00\x00\x05\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x14 \x00\x00\x00 \x01\r' \
                                    b'\xb8\x00\x00\x00\x1e@\x00\x00\x00 \x01\r\xb8\xca\xfe\x00\x01\x00\x00\x00(`\x00' \
                                    b'\x00\x00 \x01\r\xb8\xca\xfe\x00\x01\x00\x00\x00\x00\x00\x00\x002\x80\x00\x00' \
                                    b'\x00 \x01\r\xb8\xca\xfe\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00'

    #  Successful run - Instant
    def test_pack_lsa(self):
        #  Router-LSA - OSPFv2
        router_lsa = lsa.Lsa()
        router_lsa.create_header(1, 34, 1, '1.1.1.1', '1.1.1.1', 2147483654, conf.VERSION_IPV4)
        router_lsa.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        router_lsa.add_link_info_v2('3.3.3.3', '222.222.6.1', 1, 0, 64)
        router_lsa.add_link_info_v2('222.222.6.0', '255.255.255.0', 3, 0, 64)
        router_lsa.add_link_info_v2('222.222.3.2', '222.222.3.1', 2, 0, 10)
        router_lsa.add_link_info_v2('222.222.2.0', '255.255.255.0', 3, 0, 10)
        router_lsa.add_link_info_v2('222.222.1.0', '255.255.255.0', 3, 0, 1)
        self.assertEqual(TestLsa.router_lsa_v2_bytes, router_lsa.pack_lsa())

        #  Router-LSA - OSPFv3
        router_lsa = lsa.Lsa()
        router_lsa.create_header(1, 0, 1, '0.0.0.0', '2.2.2.2', 2147483655, conf.VERSION_IPV6)
        router_lsa.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        router_lsa.add_link_info_v3(2, 1, 6, 4, '3.3.3.3')
        router_lsa.add_link_info_v3(2, 10, 5, 5, '2.2.2.2')
        self.assertEqual(TestLsa.router_lsa_v3_bytes, router_lsa.pack_lsa())

        #  Network-LSA - OSPFv2
        network_lsa = lsa.Lsa()
        network_lsa.create_header(1, 34, 2, '222.222.3.2', '2.2.2.2', 2147483649, conf.VERSION_IPV4)
        network_lsa.create_network_lsa_body('255.255.255.0', 0, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV4)
        self.assertEqual(TestLsa.network_lsa_v2_bytes, network_lsa.pack_lsa())

        #  Network-LSA - OSPFv3
        network_lsa = lsa.Lsa()
        network_lsa.create_header(1, 0, 2, '0.0.0.5', '2.2.2.2', 2147483650, conf.VERSION_IPV6)
        network_lsa.create_network_lsa_body('', 51, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV6)
        self.assertEqual(TestLsa.network_lsa_v3_bytes, network_lsa.pack_lsa())

        #  Intra-Area-Prefix-LSA
        intra_area_prefix_lsa = lsa.Lsa()
        intra_area_prefix_lsa.create_header(1, 0, 9, '0.0.0.0', '2.2.2.2', 2147483653, conf.VERSION_IPV6)
        intra_area_prefix_lsa.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '2.2.2.2')
        intra_area_prefix_lsa.add_prefix_info(64, 0, 10, '2001:db8:cafe:4::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        self.assertEqual(TestLsa.intra_area_prefix_lsa_bytes, intra_area_prefix_lsa.pack_lsa())

        #  Link-LSA
        link_lsa = lsa.Lsa()
        link_lsa.create_header(38, 0, 8, '0.0.0.4', '1.1.1.1', 2147483650, conf.VERSION_IPV6)
        link_lsa.create_link_lsa_body(1, 51, 'fe80::c001:18ff:fe34:0')
        link_lsa.add_prefix_info(64, 0, 0, '2001:db8:cafe:3::', conf.LSA_TYPE_LINK)
        self.assertEqual(TestLsa.link_lsa_bytes, link_lsa.pack_lsa())

        #  Summary-LSA
        summary_lsa_3 = lsa.Lsa()
        summary_lsa_4 = lsa.Lsa()
        summary_lsa_3.create_header(20, 0, 3, '222.222.1.0', '4.4.4.4', 2147483649, conf.VERSION_IPV4)
        summary_lsa_4.create_header(20, 0, 4, '222.222.1.0', '4.4.4.4', 2147483649, conf.VERSION_IPV4)
        summary_lsa_3.create_summary_lsa_body('255.255.255.0', 10)
        summary_lsa_4.create_summary_lsa_body('255.255.255.0', 10)
        self.assertEqual(TestLsa.summary_lsa_3_bytes, summary_lsa_3.pack_lsa())
        self.assertEqual(TestLsa.summary_lsa_4_bytes, summary_lsa_4.pack_lsa())

        #  Inter-Area-Prefix LSA
        inter_area_prefix_lsa = lsa.Lsa()
        inter_area_prefix_lsa.create_header(20, 0, 3, '0.0.0.1', '4.4.4.4', 2147483649, conf.VERSION_IPV6)
        inter_area_prefix_lsa.create_inter_area_prefix_lsa_body(10, 64, 0, '2001:db8:cafe:1::')
        self.assertEqual(TestLsa.inter_area_prefix_lsa_bytes, inter_area_prefix_lsa.pack_lsa())

        #  Extension ABR-LSA - OSPFv2
        extension_abr_lsa = lsa.Lsa()
        extension_abr_lsa.create_extension_header(
            1, 0, conf.OPAQUE_TYPE_ABR_LSA, 0, '4.4.4.4', 2147483649, conf.VERSION_IPV4)
        extension_abr_lsa.create_extension_abr_lsa_body()
        extension_abr_lsa.add_abr_info(10, '1.1.1.1')
        extension_abr_lsa.add_abr_info(20, '2.2.2.2')
        self.assertEqual(TestLsa.extension_abr_lsa_v2_bytes, extension_abr_lsa.pack_lsa())

        #  Extension ABR-LSA - OSPFv3
        extension_abr_lsa = lsa.Lsa()
        extension_abr_lsa.create_extension_header(
            10, 0, 0, conf.LSA_TYPE_EXTENSION_ABR_LSA, '4.4.4.4', 2147483650, conf.VERSION_IPV6)
        extension_abr_lsa.create_extension_abr_lsa_body()
        extension_abr_lsa.add_abr_info(30, '3.3.3.3')
        extension_abr_lsa.add_abr_info(40, '4.4.4.4')
        self.assertEqual(TestLsa.extension_abr_lsa_v3_bytes, extension_abr_lsa.pack_lsa())

        #  Extension Prefix-LSA - OSPFv2
        extension_prefix_lsa = lsa.Lsa()
        extension_prefix_lsa.create_extension_header(
            10, 0, conf.OPAQUE_TYPE_PREFIX_LSA, 0, '1.1.1.1', 2147483649, conf.VERSION_IPV4)
        extension_prefix_lsa.create_extension_prefix_lsa_body(conf.VERSION_IPV4)
        extension_prefix_lsa.add_subnet_info(10, '255.255.255.0', '222.222.1.0')
        extension_prefix_lsa.add_subnet_info(20, '255.255.0.0', '222.1.0.0')
        extension_prefix_lsa.add_subnet_info(30, '255.0.0.0', '1.0.0.0')
        extension_prefix_lsa.add_subnet_info(40, '0.0.0.0', '0.0.0.0')
        self.assertEqual(TestLsa.extension_prefix_lsa_v2_bytes, extension_prefix_lsa.pack_lsa())

        #  Extension Prefix-LSA - OSPFv3
        extension_prefix_lsa = lsa.Lsa()
        extension_prefix_lsa.create_extension_header(
            10, 0, 0, conf.LSA_TYPE_EXTENSION_PREFIX_LSA, '4.4.4.4', 2147483650, conf.VERSION_IPV6)
        extension_prefix_lsa.create_extension_prefix_lsa_body(conf.VERSION_IPV6)
        extension_prefix_lsa.add_prefix_info_extension(10, 0, 0, '::')
        extension_prefix_lsa.add_prefix_info_extension(20, 32, 0, '2001:db8::')
        extension_prefix_lsa.add_prefix_info_extension(30, 64, 0, '2001:db8:cafe:1::')
        extension_prefix_lsa.add_prefix_info_extension(40, 96, 0, '2001:db8:cafe:1::')
        extension_prefix_lsa.add_prefix_info_extension(50, 128, 0, '2001:db8:cafe:1::')
        self.assertEqual(TestLsa.extension_prefix_lsa_v3_bytes, extension_prefix_lsa.pack_lsa())

    #  Successful run - Instant
    def test_unpack_lsa(self):
        #  Router-LSA - OSPFv2
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.router_lsa_v2_bytes, conf.VERSION_IPV4)
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(34, unpacked_lsa.header.options)
        self.assertEqual(1, unpacked_lsa.header.ls_type)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483654, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)
        self.assertEqual(2992, unpacked_lsa.header.ls_checksum)
        self.assertEqual(84, unpacked_lsa.header.length)
        self.assertFalse(unpacked_lsa.body.bit_v)
        self.assertFalse(unpacked_lsa.body.bit_e)
        self.assertFalse(unpacked_lsa.body.bit_b)
        self.assertEqual(5, unpacked_lsa.body.link_number)
        self.assertEqual([['3.3.3.3', '222.222.6.1', 1, 0, 64], ['222.222.6.0', '255.255.255.0', 3, 0, 64],
                          ['222.222.3.2', '222.222.3.1', 2, 0, 10], ['222.222.2.0', '255.255.255.0', 3, 0, 10],
                          ['222.222.1.0', '255.255.255.0', 3, 0, 1]], unpacked_lsa.body.links)

        #  Router-LSA - OSPFv3
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.router_lsa_v3_bytes, conf.VERSION_IPV6)
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2001, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483655, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)
        self.assertEqual(11392, unpacked_lsa.header.ls_checksum)
        self.assertEqual(56, unpacked_lsa.header.length)
        self.assertFalse(unpacked_lsa.body.bit_v)
        self.assertFalse(unpacked_lsa.body.bit_e)
        self.assertFalse(unpacked_lsa.body.bit_b)
        self.assertEqual(51, unpacked_lsa.body.options)
        self.assertEqual([[2, 1, 6, 4, '3.3.3.3'], [2, 10, 5, 5, '2.2.2.2']], unpacked_lsa.body.links)

        #  Network-LSA - OSPFv2
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.network_lsa_v2_bytes, conf.VERSION_IPV4)
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(34, unpacked_lsa.header.options)
        self.assertEqual(2, unpacked_lsa.header.ls_type)
        self.assertEqual('222.222.3.2', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483649, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)
        self.assertEqual(57474, unpacked_lsa.header.ls_checksum)
        self.assertEqual(32, unpacked_lsa.header.length)
        self.assertEqual('255.255.255.0', unpacked_lsa.body.network_mask)
        self.assertEqual(['2.2.2.2', '1.1.1.1'], unpacked_lsa.body.attached_routers)

        #  Network-LSA - OSPFv3
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.network_lsa_v3_bytes, conf.VERSION_IPV6)
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2002, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.5', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483650, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)
        self.assertEqual(63223, unpacked_lsa.header.ls_checksum)
        self.assertEqual(32, unpacked_lsa.header.length)
        self.assertEqual(51, unpacked_lsa.body.options)
        self.assertEqual(['2.2.2.2', '1.1.1.1'], unpacked_lsa.body.attached_routers)

        #  Intra-Area-Prefix-LSA
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.intra_area_prefix_lsa_bytes, conf.VERSION_IPV6)
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2009, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483653, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)
        self.assertEqual(42828, unpacked_lsa.header.ls_checksum)
        self.assertEqual(44, unpacked_lsa.header.length)
        self.assertEqual(1, unpacked_lsa.body.prefix_number)
        self.assertEqual(0x2001, unpacked_lsa.body.referenced_ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.body.referenced_link_state_id)
        self.assertEqual('2.2.2.2', unpacked_lsa.body.referenced_advertising_router)
        self.assertEqual([[64, 0, 10, '2001:db8:cafe:4::']], unpacked_lsa.body.prefixes)

        #  Link-LSA
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.link_lsa_bytes, conf.VERSION_IPV6)
        self.assertEqual(38, unpacked_lsa.header.ls_age)
        self.assertEqual(8, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.4', unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483650, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)
        self.assertEqual(33022, unpacked_lsa.header.ls_checksum)
        self.assertEqual(56, unpacked_lsa.header.length)
        self.assertEqual(1, unpacked_lsa.body.router_priority)
        self.assertEqual(51, unpacked_lsa.body.options)
        self.assertEqual('fe80::c001:18ff:fe34:0', unpacked_lsa.body.link_local_address)
        self.assertEqual(1, unpacked_lsa.body.prefix_number)
        self.assertEqual([[64, 0, '2001:db8:cafe:3::']], unpacked_lsa.body.prefixes)

        #  Summary-LSA
        unpacked_lsa_3 = lsa.Lsa.unpack_lsa(TestLsa.summary_lsa_3_bytes, conf.VERSION_IPV4)
        unpacked_lsa_4 = lsa.Lsa.unpack_lsa(TestLsa.summary_lsa_4_bytes, conf.VERSION_IPV4)
        self.assertEqual(20, unpacked_lsa_3.header.ls_age)
        self.assertEqual(20, unpacked_lsa_4.header.ls_age)
        self.assertEqual(3, unpacked_lsa_3.header.ls_type)
        self.assertEqual(4, unpacked_lsa_4.header.ls_type)
        self.assertEqual('222.222.1.0', unpacked_lsa_3.header.link_state_id)
        self.assertEqual('222.222.1.0', unpacked_lsa_4.header.link_state_id)
        self.assertEqual('4.4.4.4', unpacked_lsa_3.header.advertising_router)
        self.assertEqual('4.4.4.4', unpacked_lsa_4.header.advertising_router)
        self.assertEqual(2147483649, unpacked_lsa_3.header.ls_sequence_number)
        self.assertEqual(2147483649, unpacked_lsa_4.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa_3.header.ospf_version)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa_4.header.ospf_version)
        self.assertEqual(42719, unpacked_lsa_3.header.ls_checksum)
        self.assertEqual(39148, unpacked_lsa_4.header.ls_checksum)
        self.assertEqual(28, unpacked_lsa_3.header.length)
        self.assertEqual(28, unpacked_lsa_4.header.length)
        self.assertEqual('255.255.255.0', unpacked_lsa_3.body.network_mask)
        self.assertEqual('255.255.255.0', unpacked_lsa_4.body.network_mask)
        self.assertEqual(10, unpacked_lsa_3.body.metric)
        self.assertEqual(10, unpacked_lsa_4.body.metric)

        #  Inter-Area-Prefix LSA
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.inter_area_prefix_lsa_bytes, conf.VERSION_IPV6)
        self.assertEqual(20, unpacked_lsa.header.ls_age)
        self.assertEqual(0x2003, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.1', unpacked_lsa.header.link_state_id)
        self.assertEqual('4.4.4.4', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483649, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)
        self.assertEqual(18657, unpacked_lsa.header.ls_checksum)
        self.assertEqual(36, unpacked_lsa.header.length)
        self.assertEqual(10, unpacked_lsa.body.metric)
        self.assertEqual(64, unpacked_lsa.body.prefix_length)
        self.assertEqual(0, unpacked_lsa.body.prefix_options)
        self.assertEqual('2001:db8:cafe:1::', unpacked_lsa.body.address_prefix)

        #  Extension ABR-LSA - OSPFv2
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.extension_abr_lsa_v2_bytes, conf.VERSION_IPV4)
        self.assertEqual(1, unpacked_lsa.header.ls_age)
        self.assertEqual(0, unpacked_lsa.header.options)
        self.assertEqual(11, unpacked_lsa.header.ls_type)
        self.assertEqual(utils.Utils.decimal_to_ipv4(conf.OPAQUE_TYPE_ABR_LSA << 3 * conf.BYTE_SIZE),
                         unpacked_lsa.header.link_state_id)
        self.assertEqual('4.4.4.4', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483649, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)
        self.assertEqual(7660, unpacked_lsa.header.ls_checksum)
        self.assertEqual(36, unpacked_lsa.header.length)
        self.assertEqual([[10, '1.1.1.1'], [20, '2.2.2.2']], unpacked_lsa.body.abr_list)

        #  Extension ABR-LSA - OSPFv3
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.extension_abr_lsa_v3_bytes, conf.VERSION_IPV6)
        self.assertEqual(10, unpacked_lsa.header.ls_age)
        self.assertEqual(0xc011, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('4.4.4.4', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483650, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)
        self.assertEqual(26031, unpacked_lsa.header.ls_checksum)
        self.assertEqual(36, unpacked_lsa.header.length)
        self.assertEqual([[30, '3.3.3.3'], [40, '4.4.4.4']], unpacked_lsa.body.abr_list)

        #  Extension Prefix-LSA - OSPFv2
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.extension_prefix_lsa_v2_bytes, conf.VERSION_IPV4)
        self.assertEqual(10, unpacked_lsa.header.ls_age)
        self.assertEqual(0, unpacked_lsa.header.options)
        self.assertEqual(11, unpacked_lsa.header.ls_type)
        self.assertEqual(utils.Utils.decimal_to_ipv4(conf.OPAQUE_TYPE_PREFIX_LSA << 3 * conf.BYTE_SIZE),
                         unpacked_lsa.header.link_state_id)
        self.assertEqual('1.1.1.1', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483649, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV4, unpacked_lsa.header.ospf_version)
        self.assertEqual(50772, unpacked_lsa.header.ls_checksum)
        self.assertEqual(68, unpacked_lsa.header.length)
        self.assertEqual([[10, '255.255.255.0', '222.222.1.0'], [20, '255.255.0.0', '222.1.0.0'],
                          [30, '255.0.0.0', '1.0.0.0'], [40, '0.0.0.0', '0.0.0.0']], unpacked_lsa.body.subnet_list)

        #  Extension Prefix-LSA - OSPFv3
        unpacked_lsa = lsa.Lsa.unpack_lsa(TestLsa.extension_prefix_lsa_v3_bytes, conf.VERSION_IPV6)
        self.assertEqual(10, unpacked_lsa.header.ls_age)
        self.assertEqual(0xc012, unpacked_lsa.header.ls_type)
        self.assertEqual('0.0.0.0', unpacked_lsa.header.link_state_id)
        self.assertEqual('4.4.4.4', unpacked_lsa.header.advertising_router)
        self.assertEqual(2147483650, unpacked_lsa.header.ls_sequence_number)
        self.assertEqual(conf.VERSION_IPV6, unpacked_lsa.header.ospf_version)
        self.assertEqual(63329, unpacked_lsa.header.ls_checksum)
        self.assertEqual(104, unpacked_lsa.header.length)
        self.assertEqual(5, unpacked_lsa.body.prefix_number)
        self.assertEqual([[10, 0, 0, '::'], [20, 32, 0, '2001:db8::'], [30, 64, 0, '2001:db8:cafe:1::'],
                          [40, 96, 0, '2001:db8:cafe:1::'], [50, 128, 0, '2001:db8:cafe:1::']],
                         unpacked_lsa.body.prefix_list)

    #  Successful run - Instant
    def test_is_lsa_checksum_valid(self):
        new_lsa = lsa.Lsa()
        self.assertFalse(new_lsa.is_lsa_checksum_valid())
        new_lsa.create_header(1, 2, 1, '0.0.0.0', '1.1.1.1', 0, conf.VERSION_IPV4)
        self.assertFalse(new_lsa.is_lsa_checksum_valid())
        new_lsa.create_router_lsa_body(False, False, False, 2, conf.VERSION_IPV4)
        self.assertTrue(new_lsa.is_lsa_checksum_valid())
        new_lsa.header.ls_age = 2
        self.assertTrue(new_lsa.is_lsa_checksum_valid())
        new_lsa.header.options = 3
        self.assertFalse(new_lsa.is_lsa_checksum_valid())
        new_lsa.set_lsa_checksum()
        self.assertTrue(new_lsa.is_lsa_checksum_valid())
        new_lsa.header.ls_checksum = 1
        self.assertFalse(new_lsa.is_lsa_checksum_valid())
        new_lsa.set_lsa_checksum()
        self.assertTrue(new_lsa.is_lsa_checksum_valid())

    #  Successful run - Instant
    def test_is_lsa_identifier_equal(self):
        first, second = self.reset_lsa_instances()
        first_id = first.get_lsa_identifier()
        second_id = second.get_lsa_identifier()
        self.assertTrue(first.is_lsa_identifier_equal(second_id[0], second_id[1], second_id[2]))
        self.assertTrue(second.is_lsa_identifier_equal(first_id[0], first_id[1], first_id[2]))

        first.header.ls_type = conf.LSA_TYPE_NETWORK
        first_id = first.get_lsa_identifier()
        self.assertFalse(first.is_lsa_identifier_equal(second_id[0], second_id[1], second_id[2]))
        self.assertFalse(second.is_lsa_identifier_equal(first_id[0], first_id[1], first_id[2]))

        first.header.ls_type = conf.LSA_TYPE_ROUTER
        first.header.link_state_id = '255.255.255.255'
        first_id = first.get_lsa_identifier()
        self.assertFalse(first.is_lsa_identifier_equal(second_id[0], second_id[1], second_id[2]))
        self.assertFalse(second.is_lsa_identifier_equal(first_id[0], first_id[1], first_id[2]))

        first.header.link_state_id = '0.0.0.0'
        first.header.advertising_router = '255.255.255.255'
        first_id = first.get_lsa_identifier()
        self.assertFalse(first.is_lsa_identifier_equal(second_id[0], second_id[1], second_id[2]))
        self.assertFalse(second.is_lsa_identifier_equal(first_id[0], first_id[1], first_id[2]))

    #  Successful run - Instant
    def test_is_extension_lsa_identifier_equal(self):
        #  OSPFv2

        initial_opaque_type = conf.OPAQUE_TYPE_ABR_LSA
        initial_ls_type = conf.LSA_TYPE_EXTENSION_ABR_LSA
        initial_advertising_router = '1.1.1.1'

        first = lsa.Lsa()
        first.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.OPAQUE_TYPE_ABR_LSA, initial_opaque_type,
            initial_advertising_router, conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        second = lsa.Lsa()
        second.create_extension_header(
            conf.INITIAL_LS_AGE + 1, conf.OPTIONS_V2 + 1, conf.OPAQUE_TYPE_ABR_LSA, initial_opaque_type,
            initial_advertising_router, conf.INITIAL_SEQUENCE_NUMBER + 1, conf.VERSION_IPV4)
        self.assertTrue(first.is_lsa_identifier_equal(
            second.header.ls_type, second.header.link_state_id, second.header.advertising_router))
        self.assertTrue(second.is_lsa_identifier_equal(
            first.header.ls_type, first.header.link_state_id, first.header.advertising_router))

        first.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.OPAQUE_TYPE_PREFIX_LSA, conf.LSA_TYPE_OPAQUE_AS,
            initial_advertising_router, conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        self.assertFalse(first.is_lsa_identifier_equal(
            second.header.ls_type, second.header.link_state_id, second.header.advertising_router))
        self.assertFalse(second.is_lsa_identifier_equal(
            first.header.ls_type, first.header.link_state_id, first.header.advertising_router))

        first.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V2, initial_opaque_type, conf.LSA_TYPE_OPAQUE_AS, '2.2.2.2',
            conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        self.assertFalse(first.is_lsa_identifier_equal(
            second.header.ls_type, second.header.link_state_id, second.header.advertising_router))
        self.assertFalse(second.is_lsa_identifier_equal(
            first.header.ls_type, first.header.link_state_id, first.header.advertising_router))

        #  OSPFv3

        first.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, initial_ls_type, initial_advertising_router,
            conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
        second.create_extension_header(
            conf.INITIAL_LS_AGE + 1, conf.OPTIONS_V3 + 1, 0, initial_ls_type, initial_advertising_router,
            conf.INITIAL_SEQUENCE_NUMBER + 1, conf.VERSION_IPV6)
        self.assertTrue(first.is_lsa_identifier_equal(
            second.header.ls_type, second.header.link_state_id, second.header.advertising_router))
        self.assertTrue(second.is_lsa_identifier_equal(
            first.header.ls_type, first.header.link_state_id, first.header.advertising_router))

        first.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, conf.LSA_TYPE_EXTENSION_PREFIX_LSA, initial_advertising_router,
            conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
        self.assertFalse(first.is_lsa_identifier_equal(
            second.header.ls_type, second.header.link_state_id, second.header.advertising_router))
        self.assertFalse(second.is_lsa_identifier_equal(
            first.header.ls_type, first.header.link_state_id, first.header.advertising_router))

        first.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, initial_ls_type, '2.2.2.2', conf.INITIAL_SEQUENCE_NUMBER,
            conf.VERSION_IPV6)
        self.assertFalse(first.is_lsa_identifier_equal(
            second.header.ls_type, second.header.link_state_id, second.header.advertising_router))
        self.assertFalse(second.is_lsa_identifier_equal(
            first.header.ls_type, first.header.link_state_id, first.header.advertising_router))

    #  Successful run - Instant
    def test_get_fresher_lsa_successful(self):
        first, second = self.reset_lsa_instances()
        #  One of the provided LSA instances is None
        self.assertEqual(header.FIRST, lsa.Lsa.get_fresher_lsa(first, None))
        self.assertEqual(header.SECOND, lsa.Lsa.get_fresher_lsa(None, second))

        first, second = self.reset_lsa_instances()
        #  Sequence Numbers are different
        first.header.ls_sequence_number += 1
        self.assertEqual(header.FIRST, lsa.Lsa.get_fresher_lsa(first, second))
        second.header.ls_sequence_number += 2
        self.assertEqual(header.SECOND, lsa.Lsa.get_fresher_lsa(first, second))
        second.header.ls_sequence_number = 0xFFFFFFFF
        self.assertEqual(header.SECOND, lsa.Lsa.get_fresher_lsa(first, second))
        first.header.ls_sequence_number = 0
        self.assertEqual(header.FIRST, lsa.Lsa.get_fresher_lsa(first, second))
        second.header.ls_sequence_number = 1
        self.assertEqual(header.SECOND, lsa.Lsa.get_fresher_lsa(first, second))
        first.header.ls_sequence_number = 0x7FFFFFFF
        self.assertEqual(header.FIRST, lsa.Lsa.get_fresher_lsa(first, second))

        first, second = self.reset_lsa_instances()
        #  Sequence Numbers are the same
        #  Checksums are different
        first.header.ls_checksum += 1
        self.assertEqual(header.FIRST, lsa.Lsa.get_fresher_lsa(first, second))
        second.header.ls_checksum += 2
        self.assertEqual(header.SECOND, lsa.Lsa.get_fresher_lsa(first, second))

        first, second = self.reset_lsa_instances()
        #  Sequence Numbers are the same
        #  Checksums are the same
        #  One LS Age field is equal to 1 h and other is smaller
        first.header.ls_age = conf.MAX_AGE
        self.assertEqual(header.FIRST, lsa.Lsa.get_fresher_lsa(first, second))
        first.header.ls_age = conf.MAX_AGE - 1
        second.header.ls_age = conf.MAX_AGE
        self.assertEqual(header.SECOND, lsa.Lsa.get_fresher_lsa(first, second))

        first, second = self.reset_lsa_instances()
        #  Sequence Numbers are the same
        #  Checksums are the same
        #  LS Age fields are different and smaller than 1 h
        #  Difference between LS Age fields is larger than 15 min
        first.header.ls_age = conf.MAX_AGE_DIFF + 1
        self.assertEqual(header.SECOND, lsa.Lsa.get_fresher_lsa(first, second))
        first.header.ls_age = 0
        second.header.ls_age = conf.MAX_AGE_DIFF + 1
        self.assertEqual(header.FIRST, lsa.Lsa.get_fresher_lsa(first, second))

        first, second = self.reset_lsa_instances()
        #  Sequence Numbers are the same
        #  Checksums are the same
        #  LS Age fields are smaller than 1 h
        #  Difference between LS Age fields is 15 min or smaller
        self.assertEqual(header.BOTH, lsa.Lsa.get_fresher_lsa(first, second))
        first.header.ls_age = conf.MAX_AGE_DIFF
        self.assertEqual(header.BOTH, lsa.Lsa.get_fresher_lsa(first, second))
        first.header.ls_age = 0
        second.header.ls_age = conf.MAX_AGE_DIFF
        self.assertEqual(header.BOTH, lsa.Lsa.get_fresher_lsa(first, second))

        first, second = self.reset_lsa_instances()
        #  Sequence Numbers are the same
        #  Checksums are the same
        #  LS Age fields are equal to 1 h
        first.header.ls_age = conf.MAX_AGE
        second.header.ls_age = conf.MAX_AGE
        self.assertEqual(header.BOTH, lsa.Lsa.get_fresher_lsa(first, second))

    #  Successful run - Instant
    def test_get_fresher_lsa_invalid_parameters(self):
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(None, None)
        first, second = self.reset_lsa_instances()
        first.header.ls_sequence_number = 0x80000000
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        first.header.ls_sequence_number = -1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        first.header.ls_sequence_number = conf.MAX_VALUE_32_BITS + 1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        first, second = self.reset_lsa_instances()
        second.header.ls_sequence_number = 0x80000000
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        second.header.ls_sequence_number = -1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        second.header.ls_sequence_number = conf.MAX_VALUE_32_BITS + 1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)

        first, second = self.reset_lsa_instances()
        first.header.ls_checksum = -1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        first.header.ls_checksum = conf.MAX_VALUE_32_BITS + 1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        first, second = self.reset_lsa_instances()
        second.header.ls_checksum = -1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        second.header.ls_checksum = conf.MAX_VALUE_32_BITS + 1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)

        first, second = self.reset_lsa_instances()
        first.header.ls_age = -1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        first.header.ls_age = conf.MAX_AGE + 1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        first, second = self.reset_lsa_instances()
        second.header.ls_age = -1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)
        second.header.ls_age = conf.MAX_AGE + 1
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, second)

    @staticmethod
    def reset_lsa_instances():
        first = lsa.Lsa()
        first.create_header(0, 0, conf.LSA_TYPE_ROUTER, '0.0.0.0', conf.ROUTER_ID, conf.INITIAL_SEQUENCE_NUMBER,
                            conf.VERSION_IPV4)
        second = lsa.Lsa()
        second.create_header(0, 0, conf.LSA_TYPE_ROUTER, '0.0.0.0', conf.ROUTER_ID, conf.INITIAL_SEQUENCE_NUMBER,
                             conf.VERSION_IPV4)
        return first, second

    #  Successful run - Instant
    def test_is_ls_type_valid(self):
        self.assertFalse(lsa.Lsa.is_ls_type_valid(1, 1))
        self.assertFalse(lsa.Lsa.is_ls_type_valid(1, 4))

        self.assertFalse(lsa.Lsa.is_ls_type_valid(0, 2))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(1, 2))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(2, 2))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(3, 2))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(4, 2))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(5, 2))
        self.assertFalse(lsa.Lsa.is_ls_type_valid(6, 2))
        self.assertFalse(lsa.Lsa.is_ls_type_valid(7, 2))
        self.assertFalse(lsa.Lsa.is_ls_type_valid(8, 2))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(9, 2))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(10, 2))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(11, 2))
        self.assertFalse(lsa.Lsa.is_ls_type_valid(12, 2))

        self.assertFalse(lsa.Lsa.is_ls_type_valid(0, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(1, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(2, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(3, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(4, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(5, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid(6, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid(7, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(8, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(9, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(conf.LSA_TYPE_EXTENSION_ABR_LSA, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(conf.LSA_TYPE_EXTENSION_PREFIX_LSA, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid(conf.LSA_TYPE_EXTENSION_ASBR_LSA, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid(conf.LSA_TYPE_EXTENSION_ASBR_LSA + 1, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid((1 << 13) + 1, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid((1 << 13) + conf.LSA_TYPE_EXTENSION_ASBR_LSA + 1, 3))
        self.assertTrue(lsa.Lsa.is_ls_type_valid((2 << 13) + 1, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid((2 << 13) + conf.LSA_TYPE_EXTENSION_ASBR_LSA + 1, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid((3 << 13) + 1, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid((3 << 13) + conf.LSA_TYPE_EXTENSION_ASBR_LSA + 1, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid((1 << 15) + (3 << 13) + 1, 3))
        self.assertFalse(lsa.Lsa.is_ls_type_valid((1 << 15) + (3 << 13) + conf.LSA_TYPE_EXTENSION_ASBR_LSA + 1, 3))

    #  Successful run - Instant
    def test_is_opaque_type_valid(self):
        self.assertFalse(lsa.Lsa.is_opaque_type_valid(0))
        self.assertTrue(lsa.Lsa.is_opaque_type_valid(conf.OPAQUE_TYPE_ABR_LSA))
        self.assertTrue(lsa.Lsa.is_opaque_type_valid(conf.OPAQUE_TYPE_PREFIX_LSA))
        self.assertTrue(lsa.Lsa.is_opaque_type_valid(conf.OPAQUE_TYPE_ASBR_LSA))
        self.assertFalse(lsa.Lsa.is_opaque_type_valid(conf.OPAQUE_TYPE_ASBR_LSA + 1))

    #  Successful run - Instant
    def test_get_next_ls_sequence_number(self):
        with self.assertRaises(ValueError):
            lsa.Lsa.get_next_ls_sequence_number(-1)
        with self.assertRaises(ValueError):
            lsa.Lsa.get_next_ls_sequence_number(0x80000000)
        with self.assertRaises(ValueError):
            lsa.Lsa.get_next_ls_sequence_number(conf.MAX_VALUE_32_BITS + 1)

        ls_sequence_number = 0x80000001  # Initial LS Sequence Number
        self.assertEqual(ls_sequence_number + 1, lsa.Lsa.get_next_ls_sequence_number(ls_sequence_number))
        ls_sequence_number = 0xFFFFFFFE
        self.assertEqual(ls_sequence_number + 1, lsa.Lsa.get_next_ls_sequence_number(ls_sequence_number))
        ls_sequence_number = 0xFFFFFFFF
        self.assertEqual(0, lsa.Lsa.get_next_ls_sequence_number(ls_sequence_number))
        ls_sequence_number = 0
        self.assertEqual(ls_sequence_number + 1, lsa.Lsa.get_next_ls_sequence_number(ls_sequence_number))
        ls_sequence_number = 0x7FFFFFFE
        self.assertEqual(ls_sequence_number + 1, lsa.Lsa.get_next_ls_sequence_number(ls_sequence_number))
        ls_sequence_number = 0x7FFFFFFF
        self.assertEqual(0x80000001, lsa.Lsa.get_next_ls_sequence_number(ls_sequence_number))

    #  Successful run - Instant
    #  The goal of this test is to send to network all types of LSAs in order to allow their observation using Wireshark
    def test_send_all_lsa_to_network(self):
        sending_socket = sock.Socket()
        interface_name = conf.INTERFACE_NAMES[0]

        #  OSPFv2
        sending_packet = packet.Packet()
        sending_packet.create_header_v2(conf.PACKET_TYPE_LS_UPDATE, conf.ROUTER_ID, conf.BACKBONE_AREA,
                                        conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)
        sending_packet.create_ls_update_packet_body(conf.VERSION_IPV4)
        router_lsa_v2 = lsa.Lsa.unpack_lsa(TestLsa.router_lsa_v2_bytes, conf.VERSION_IPV4)
        sending_packet.add_lsa(router_lsa_v2)
        network_lsa_v2 = lsa.Lsa.unpack_lsa(TestLsa.network_lsa_v2_bytes, conf.VERSION_IPV4)
        sending_packet.add_lsa(network_lsa_v2)
        summary_lsa_3 = lsa.Lsa.unpack_lsa(TestLsa.summary_lsa_3_bytes, conf.VERSION_IPV4)
        sending_packet.add_lsa(summary_lsa_3)
        summary_lsa_4 = lsa.Lsa.unpack_lsa(TestLsa.summary_lsa_4_bytes, conf.VERSION_IPV4)
        sending_packet.add_lsa(summary_lsa_4)
        extension_abr_lsa_v2 = lsa.Lsa.unpack_lsa(TestLsa.extension_abr_lsa_v2_bytes, conf.VERSION_IPV4)
        sending_packet.add_lsa(extension_abr_lsa_v2)
        extension_prefix_lsa_v2 = lsa.Lsa.unpack_lsa(TestLsa.extension_prefix_lsa_v2_bytes, conf.VERSION_IPV4)
        sending_packet.add_lsa(extension_prefix_lsa_v2)
        sending_socket.send_ipv4(sending_packet.pack_packet(), conf.ALL_OSPF_ROUTERS_IPV4, interface_name, False)

        #  OSPFv3
        sending_packet = packet.Packet()
        sending_packet.create_header_v3(
            conf.PACKET_TYPE_LS_UPDATE, conf.ROUTER_ID, conf.BACKBONE_AREA, 0,
            utils.Utils.interface_name_to_ipv6_link_local_address(interface_name), conf.ALL_OSPF_ROUTERS_IPV6)
        sending_packet.create_ls_update_packet_body(conf.VERSION_IPV6)
        router_lsa_v3 = lsa.Lsa.unpack_lsa(TestLsa.router_lsa_v3_bytes, conf.VERSION_IPV6)
        sending_packet.add_lsa(router_lsa_v3)
        network_lsa_v3 = lsa.Lsa.unpack_lsa(TestLsa.network_lsa_v3_bytes, conf.VERSION_IPV6)
        sending_packet.add_lsa(network_lsa_v3)
        intra_area_prefix_lsa = lsa.Lsa.unpack_lsa(TestLsa.intra_area_prefix_lsa_bytes, conf.VERSION_IPV6)
        sending_packet.add_lsa(intra_area_prefix_lsa)
        link_lsa = lsa.Lsa.unpack_lsa(TestLsa.link_lsa_bytes, conf.VERSION_IPV6)
        sending_packet.add_lsa(link_lsa)
        inter_area_prefix_lsa = lsa.Lsa.unpack_lsa(TestLsa.inter_area_prefix_lsa_bytes, conf.VERSION_IPV6)
        sending_packet.add_lsa(inter_area_prefix_lsa)
        extension_abr_lsa_v3 = lsa.Lsa.unpack_lsa(TestLsa.extension_abr_lsa_v3_bytes, conf.VERSION_IPV6)
        sending_packet.add_lsa(extension_abr_lsa_v3)
        extension_prefix_lsa_v3 = lsa.Lsa.unpack_lsa(TestLsa.extension_prefix_lsa_v3_bytes, conf.VERSION_IPV6)
        sending_packet.add_lsa(extension_prefix_lsa_v3)
        sending_socket.send_ipv6(sending_packet.pack_packet(), conf.ALL_OSPF_ROUTERS_IPV6, interface_name, False)


if __name__ == '__main__':
    unittest.main()
