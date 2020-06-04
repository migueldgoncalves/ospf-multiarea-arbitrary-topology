import unittest

import lsa.lsa as lsa
import lsa.header as header
import conf.conf as conf

'''
This class tests the interface to LSA creation, storage and manipulation
'''


#  Full successful run - Instant
class TestLsa(unittest.TestCase):

    #  Successful run - Instant
    def test_pack_lsa(self):
        #  Router-LSA - OSPFv2
        body_bytes = b'\x00\x01"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x80\x00\x00\x06\x0b\xb0\x00T\x00\x00\x00\x05\x03' \
                     b'\x03\x03\x03\xde\xde\x06\x01\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00\x03\x00\x00@\xde\xde' \
                     b'\x03\x02\xde\xde\x03\x01\x02\x00\x00\n\xde\xde\x02\x00\xff\xff\xff\x00\x03\x00\x00\n\xde\xde' \
                     b'\x01\x00\xff\xff\xff\x00\x03\x00\x00\x01'
        router_lsa = lsa.Lsa()
        router_lsa.create_header(1, 34, 1, '1.1.1.1', '1.1.1.1', 2147483654, conf.VERSION_IPV4)
        router_lsa.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        router_lsa.add_link_info_v2('3.3.3.3', '222.222.6.1', 1, 0, 64)
        router_lsa.add_link_info_v2('222.222.6.0', '255.255.255.0', 3, 0, 64)
        router_lsa.add_link_info_v2('222.222.3.2', '222.222.3.1', 2, 0, 10)
        router_lsa.add_link_info_v2('222.222.2.0', '255.255.255.0', 3, 0, 10)
        router_lsa.add_link_info_v2('222.222.1.0', '255.255.255.0', 3, 0, 1)
        self.assertEqual(body_bytes, router_lsa.pack_lsa())

        #  Router-LSA - OSPFv3
        body_bytes = b'\x00\x01 \x01\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x07,\x80\x008\x00\x00\x003\x02\x00' \
                     b'\x00\x01\x00\x00\x00\x06\x00\x00\x00\x04\x03\x03\x03\x03\x02\x00\x00\n\x00\x00\x00\x05\x00\x00' \
                     b'\x00\x05\x02\x02\x02\x02'
        router_lsa = lsa.Lsa()
        router_lsa.create_header(1, 0, 1, '0.0.0.0', '2.2.2.2', 2147483655, conf.VERSION_IPV6)
        router_lsa.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        router_lsa.add_link_info_v3(2, 1, 6, 4, '3.3.3.3')
        router_lsa.add_link_info_v3(2, 10, 5, 5, '2.2.2.2')
        self.assertEqual(body_bytes, router_lsa.pack_lsa())

        #  Network-LSA - OSPFv2
        body_bytes = b'\x00\x01"\x02\xde\xde\x03\x02\x02\x02\x02\x02\x80\x00\x00\x01\xe0\x82\x00 \xff\xff\xff\x00\x02' \
                     b'\x02\x02\x02\x01\x01\x01\x01'
        network_lsa = lsa.Lsa()
        network_lsa.create_header(1, 34, 2, '222.222.3.2', '2.2.2.2', 2147483649, conf.VERSION_IPV4)
        network_lsa.create_network_lsa_body('255.255.255.0', 0, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV4)
        self.assertEqual(body_bytes, network_lsa.pack_lsa())

        #  Network-LSA - OSPFv3
        body_bytes = b'\x00\x01 \x02\x00\x00\x00\x05\x02\x02\x02\x02\x80\x00\x00\x02\xf6\xf7\x00 \x00\x00\x003\x02' \
                     b'\x02\x02\x02\x01\x01\x01\x01'
        network_lsa = lsa.Lsa()
        network_lsa.create_header(1, 0, 2, '0.0.0.5', '2.2.2.2', 2147483650, conf.VERSION_IPV6)
        network_lsa.create_network_lsa_body('', 51, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV6)
        self.assertEqual(body_bytes, network_lsa.pack_lsa())

        #  Intra-Area-Prefix-LSA
        body_bytes = b'\x00\x01 \t\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x05\xa7L\x00,\x00\x01 \x01\x00\x00\x00' \
                     b'\x00\x02\x02\x02\x02@\x00\x00\n \x01\r\xb8\xca\xfe\x00\x04'
        intra_area_prefix_lsa = lsa.Lsa()
        intra_area_prefix_lsa.create_header(1, 0, 9, '0.0.0.0', '2.2.2.2', 2147483653, conf.VERSION_IPV6)
        intra_area_prefix_lsa.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '2.2.2.2')
        intra_area_prefix_lsa.add_prefix_info(64, 0, 10, '2001:db8:cafe:4::', conf.LSA_TYPE_INTRA_AREA_PREFIX)
        self.assertEqual(body_bytes, intra_area_prefix_lsa.pack_lsa())

        #  Link-LSA
        body_bytes = b'\x00&\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00\x00\x02\x80\xfe\x008\x01\x00\x003\xfe' \
                     b'\x80\x00\x00\x00\x00\x00\x00\xc0\x01\x18\xff\xfe4\x00\x00\x00\x00\x00\x01@\x00\x00\x00 \x01\r' \
                     b'\xb8\xca\xfe\x00\x03'
        link_lsa = lsa.Lsa()
        link_lsa.create_header(38, 0, 8, '0.0.0.4', '1.1.1.1', 2147483650, conf.VERSION_IPV6)
        link_lsa.create_link_lsa_body(1, 51, 'fe80::c001:18ff:fe34:0')
        link_lsa.add_prefix_info(64, 0, 0, '2001:db8:cafe:3::', conf.LSA_TYPE_LINK)
        self.assertEqual(body_bytes, link_lsa.pack_lsa())

    #  Successful run - Instant
    def test_unpack_lsa(self):
        #  Router-LSA - OSPFv2
        body_bytes = b'\x00\x01"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x80\x00\x00\x06\x0b\xb0\x00T\x00\x00\x00\x05\x03' \
                     b'\x03\x03\x03\xde\xde\x06\x01\x01\x00\x00@\xde\xde\x06\x00\xff\xff\xff\x00\x03\x00\x00@\xde\xde' \
                     b'\x03\x02\xde\xde\x03\x01\x02\x00\x00\n\xde\xde\x02\x00\xff\xff\xff\x00\x03\x00\x00\n\xde\xde' \
                     b'\x01\x00\xff\xff\xff\x00\x03\x00\x00\x01'
        unpacked_lsa = lsa.Lsa.unpack_lsa(body_bytes, conf.VERSION_IPV4)
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
        body_bytes = b'\x00\x01 \x01\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x07,\x80\x008\x00\x00\x003\x02\x00' \
                     b'\x00\x01\x00\x00\x00\x06\x00\x00\x00\x04\x03\x03\x03\x03\x02\x00\x00\n\x00\x00\x00\x05\x00\x00' \
                     b'\x00\x05\x02\x02\x02\x02'
        unpacked_lsa = lsa.Lsa.unpack_lsa(body_bytes, conf.VERSION_IPV6)
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
        body_bytes = b'\x00\x01"\x02\xde\xde\x03\x02\x02\x02\x02\x02\x80\x00\x00\x01\xe0\x82\x00 \xff\xff\xff\x00\x02' \
                     b'\x02\x02\x02\x01\x01\x01\x01'
        unpacked_lsa = lsa.Lsa.unpack_lsa(body_bytes, conf.VERSION_IPV4)
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
        body_bytes = b'\x00\x01 \x02\x00\x00\x00\x05\x02\x02\x02\x02\x80\x00\x00\x02\xf6\xf7\x00 \x00\x00\x003\x02' \
                     b'\x02\x02\x02\x01\x01\x01\x01'
        unpacked_lsa = lsa.Lsa.unpack_lsa(body_bytes, conf.VERSION_IPV6)
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
        body_bytes = b'\x00\x01 \t\x00\x00\x00\x00\x02\x02\x02\x02\x80\x00\x00\x05\xa7L\x00,\x00\x01 \x01\x00\x00\x00' \
                     b'\x00\x02\x02\x02\x02@\x00\x00\n \x01\r\xb8\xca\xfe\x00\x04'
        unpacked_lsa = lsa.Lsa.unpack_lsa(body_bytes, conf.VERSION_IPV6)
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
        body_bytes = b'\x00&\x00\x08\x00\x00\x00\x04\x01\x01\x01\x01\x80\x00\x00\x02\x80\xfe\x008\x01\x00\x003\xfe' \
                     b'\x80\x00\x00\x00\x00\x00\x00\xc0\x01\x18\xff\xfe4\x00\x00\x00\x00\x00\x01@\x00\x00\x00 \x01\r' \
                     b'\xb8\xca\xfe\x00\x03'
        unpacked_lsa = lsa.Lsa.unpack_lsa(body_bytes, conf.VERSION_IPV6)
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

    #  Successful run - Instant
    def test_get_fresher_lsa_successful(self):
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
        first, second = self.reset_lsa_instances()
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(None, second)
        with self.assertRaises(ValueError):
            lsa.Lsa.get_fresher_lsa(first, None)
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
