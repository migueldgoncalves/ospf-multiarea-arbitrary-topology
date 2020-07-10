import unittest
import queue
import threading

import conf.conf as conf
import general.utils as utils
import interface.interface as interface
import area.lsdb as lsdb
import lsa.lsa as lsa

'''
This class tests the LSDB operations in the router
'''


#  Full successful run - Instant
class TestLsdb(unittest.TestCase):
    
    def setUp(self):
        interface_identifier = conf.INTERFACE_NAMES[0]
        ipv4_address = utils.Utils.get_ipv4_address_from_interface_name(conf.INTERFACE_NAMES[0])
        ipv6_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(conf.INTERFACE_NAMES[0])
        network_mask = utils.Utils.get_ipv4_network_mask_from_interface_name(conf.INTERFACE_NAMES[0])
        link_prefixes = utils.Utils.get_ipv6_prefix_from_interface_name(conf.INTERFACE_NAMES[0])
        area_id = conf.INTERFACE_AREAS[0]
        interface_pipeline_v2 = queue.Queue()
        interface_pipeline_v3 = queue.Queue()
        interface_shutdown_v2 = threading.Event()
        interface_shutdown_v3 = threading.Event()
        self.interface_ospfv2 = interface.Interface(
            conf.ROUTER_ID, interface_identifier, ipv4_address, '', network_mask, [], area_id, interface_pipeline_v2,
            interface_shutdown_v2, conf.VERSION_IPV4, None, False)
        self.interface_ospfv3 = interface.Interface(
            conf.ROUTER_ID, interface_identifier, '', ipv6_address, '', link_prefixes, area_id, interface_pipeline_v3,
            interface_shutdown_v3, conf.VERSION_IPV6, None, False)

        self.lsa_ospfv2_1 = lsa.Lsa()
        self.lsa_ospfv2_2 = lsa.Lsa()
        self.lsa_ospfv3_1 = lsa.Lsa()
        self.lsa_ospfv3_2 = lsa.Lsa()
        self.lsa_ospfv3_3 = lsa.Lsa()
        self.lsa_ospfv3_4 = lsa.Lsa()
        self.lsa_ospfv2_1.create_header(1, 34, 1, '1.1.1.1', '1.1.1.1', 2147483654, conf.VERSION_IPV4)
        self.lsa_ospfv2_1.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        self.lsa_ospfv2_2.create_header(1, 34, 2, '222.222.3.2', '2.2.2.2', 2147483649, conf.VERSION_IPV4)
        self.lsa_ospfv2_2.create_network_lsa_body('255.255.255.0', 0, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV4)
        self.lsa_ospfv3_1.create_header(1, 0, 1, '0.0.0.0', '2.2.2.2', 2147483655, conf.VERSION_IPV6)
        self.lsa_ospfv3_1.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        self.lsa_ospfv3_2.create_header(1, 0, 2, '0.0.0.5', '2.2.2.2', 2147483650, conf.VERSION_IPV6)
        self.lsa_ospfv3_2.create_network_lsa_body('', 51, ['2.2.2.2', '1.1.1.1'], conf.VERSION_IPV6)
        self.lsa_ospfv3_3.create_header(1, 0, 9, '0.0.0.0', '2.2.2.2', 2147483653, conf.VERSION_IPV6)
        self.lsa_ospfv3_3.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '2.2.2.2')
        self.lsa_ospfv3_4.create_header(38, 0, 8, '0.0.0.4', '1.1.1.1', 2147483650, conf.VERSION_IPV6)
        self.lsa_ospfv3_4.create_link_lsa_body(1, 51, 'fe80::c001:18ff:fe34:0')

        self.lsdb_ospfv2 = lsdb.Lsdb(conf.VERSION_IPV4)
        self.lsdb_ospfv3 = lsdb.Lsdb(conf.VERSION_IPV6)

    #  Successful run - Instant
    def test_constructor_test(self):
        self.assertEqual(0, len(self.lsdb_ospfv2.router_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv2.network_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv2.intra_area_prefix_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv3.router_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv3.network_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv3.intra_area_prefix_lsa_list))

    #  Successful run - Instant
    def test_get_lsa(self):
        self.populate_lsdb()

        #  Get LSDB

        retrieved_lsdb = self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)
        self.assertEqual(2, len(retrieved_lsdb))
        self.assertEqual(1, retrieved_lsdb[0].header.ls_type)
        self.assertEqual(2, retrieved_lsdb[1].header.ls_type)
        retrieved_lsdb = self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], [[1, '1.1.1.1', '1.1.1.1']])
        self.assertEqual(1, len(retrieved_lsdb))
        self.assertEqual(1, retrieved_lsdb[0].header.ls_type)
        retrieved_lsdb = self.lsdb_ospfv2.get_lsdb(
            [self.interface_ospfv2], [[1, '1.1.1.1', '1.1.1.1'], [2, '222.222.3.2', '2.2.2.2']])
        self.assertEqual(2, len(retrieved_lsdb))
        self.assertEqual(1, retrieved_lsdb[0].header.ls_type)
        self.assertEqual(2, retrieved_lsdb[1].header.ls_type)

        retrieved_lsdb = self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)
        self.assertEqual(4, len(retrieved_lsdb))
        self.assertEqual(0x2001, retrieved_lsdb[0].header.ls_type)
        self.assertEqual(0x2002, retrieved_lsdb[1].header.ls_type)
        self.assertEqual(0x2009, retrieved_lsdb[2].header.ls_type)
        self.assertEqual(8, retrieved_lsdb[3].header.ls_type)
        retrieved_lsdb = self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], [[0x2001, '0.0.0.0', '2.2.2.2']])
        self.assertEqual(1, len(retrieved_lsdb))
        self.assertEqual(0x2001, retrieved_lsdb[0].header.ls_type)
        retrieved_lsdb = self.lsdb_ospfv3.get_lsdb(
            [self.interface_ospfv3], [[0x2002, '0.0.0.5', '2.2.2.2'], [8, '0.0.0.4', '1.1.1.1']])
        self.assertEqual(2, len(retrieved_lsdb))
        self.assertEqual(0x2002, retrieved_lsdb[0].header.ls_type)
        self.assertEqual(8, retrieved_lsdb[1].header.ls_type)

        #  Get a LSA

        retrieved_lsa = self.lsdb_ospfv2.get_lsa(1, '0.0.0.0', '0.0.0.0', [self.interface_ospfv2])
        self.assertIsNone(retrieved_lsa)
        retrieved_lsa = self.lsdb_ospfv2.get_lsa(1, '1.1.1.1', '1.1.1.1', [self.interface_ospfv2])
        self.assertEqual(1, retrieved_lsa.header.ls_type)

        retrieved_lsa = self.lsdb_ospfv3.get_lsa(8, '0.0.0.0', '0.0.0.0', [self.interface_ospfv3])
        self.assertIsNone(retrieved_lsa)
        retrieved_lsa = self.lsdb_ospfv3.get_lsa(8, '0.0.0.4', '1.1.1.1', [self.interface_ospfv3])
        self.assertEqual(8, retrieved_lsa.header.ls_type)
        retrieved_lsa = self.lsdb_ospfv3.get_lsa(1, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(0x2001, retrieved_lsa.header.ls_type)
        retrieved_lsa = self.lsdb_ospfv3.get_lsa(0x2001, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(0x2001, retrieved_lsa.header.ls_type)

        #  Get LSDB headers

        retrieved_headers = self.lsdb_ospfv2.get_lsa_headers([self.interface_ospfv2], None)
        self.assertEqual(2, len(retrieved_headers))
        self.assertEqual(1, retrieved_headers[0].ls_type)
        self.assertEqual(2, retrieved_headers[1].ls_type)
        retrieved_headers = self.lsdb_ospfv2.get_lsa_headers([self.interface_ospfv2], [[1, '1.1.1.1', '1.1.1.1']])
        self.assertEqual(1, len(retrieved_headers))
        self.assertEqual(1, retrieved_headers[0].ls_type)
        retrieved_headers = self.lsdb_ospfv2.get_lsa_headers(
            [self.interface_ospfv2], [[1, '1.1.1.1', '1.1.1.1'], [2, '222.222.3.2', '2.2.2.2']])
        self.assertEqual(2, len(retrieved_headers))
        self.assertEqual(1, retrieved_headers[0].ls_type)
        self.assertEqual(2, retrieved_headers[1].ls_type)

        retrieved_headers = self.lsdb_ospfv3.get_lsa_headers([self.interface_ospfv3], None)
        self.assertEqual(4, len(retrieved_headers))
        self.assertEqual(0x2001, retrieved_headers[0].ls_type)
        self.assertEqual(0x2002, retrieved_headers[1].ls_type)
        self.assertEqual(0x2009, retrieved_headers[2].ls_type)
        self.assertEqual(8, retrieved_headers[3].ls_type)
        retrieved_headers = self.lsdb_ospfv3.get_lsa_headers([self.interface_ospfv3], [[0x2001, '0.0.0.0', '2.2.2.2']])
        self.assertEqual(1, len(retrieved_headers))
        self.assertEqual(0x2001, retrieved_headers[0].ls_type)
        retrieved_headers = self.lsdb_ospfv3.get_lsa_headers(
            [self.interface_ospfv3], [[0x2002, '0.0.0.5', '2.2.2.2'], [8, '0.0.0.4', '1.1.1.1']])
        self.assertEqual(2, len(retrieved_headers))
        self.assertEqual(0x2002, retrieved_headers[0].ls_type)
        self.assertEqual(8, retrieved_headers[1].ls_type)

        #  Get a LSA header

        retrieved_header = self.lsdb_ospfv2.get_lsa_header(1, '0.0.0.0', '0.0.0.0', [self.interface_ospfv2])
        self.assertIsNone(retrieved_header)
        retrieved_header = self.lsdb_ospfv2.get_lsa_header(2, '222.222.3.2', '2.2.2.2', [self.interface_ospfv2])
        self.assertEqual(2, retrieved_header.ls_type)

        retrieved_header = self.lsdb_ospfv3.get_lsa_header(8, '0.0.0.0', '0.0.0.0', [self.interface_ospfv3])
        self.assertIsNone(retrieved_header)
        retrieved_header = self.lsdb_ospfv3.get_lsa_header(8, '0.0.0.4', '1.1.1.1', [self.interface_ospfv3])
        self.assertEqual(8, retrieved_header.ls_type)
        retrieved_header = self.lsdb_ospfv3.get_lsa_header(1, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(0x2001, retrieved_header.ls_type)
        retrieved_header = self.lsdb_ospfv3.get_lsa_header(0x2001, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(0x2001, retrieved_header.ls_type)

    #  Successful run - Instant
    def test_delete_lsa(self):
        self.populate_lsdb()

        #  Delete a LSA

        self.lsdb_ospfv2.delete_lsa(1, '0.0.0.0', '0.0.0.0', [self.interface_ospfv2])
        self.assertEqual(2, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.lsdb_ospfv2.delete_lsa(1, '1.1.1.1', '1.1.1.1', [self.interface_ospfv2])
        self.assertEqual(1, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual(2, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_type)
        self.lsdb_ospfv2.delete_lsa(1, '1.1.1.1', '1.1.1.1', [self.interface_ospfv2])
        self.assertEqual(1, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.lsdb_ospfv2.delete_lsa(2, '222.222.3.2', '2.2.2.2', [self.interface_ospfv2])
        self.assertEqual(0, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))

        self.lsdb_ospfv3.delete_lsa(0x2001, '0.0.0.0', '0.0.0.0', [self.interface_ospfv3])
        self.assertEqual(4, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.lsdb_ospfv3.delete_lsa(0x2001, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(3, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(0x2009, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[1].header.ls_type)
        self.lsdb_ospfv3.delete_lsa(0x2001, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(3, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.lsdb_ospfv3.delete_lsa(0x2002, '0.0.0.5', '2.2.2.2', [self.interface_ospfv3])
        self.lsdb_ospfv3.delete_lsa(0x2009, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.lsdb_ospfv3.delete_lsa(8, '0.0.0.4', '1.1.1.1', [self.interface_ospfv3])
        self.assertEqual(0, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))

        #  Clean LSDB

        self.populate_lsdb()

        self.lsdb_ospfv2.clean_lsdb([self.interface_ospfv2])
        self.assertEqual(0, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.lsdb_ospfv3.clean_lsdb([self.interface_ospfv3])
        self.assertEqual(0, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))

    #  Successful run - Instant
    def test_add_lsa(self):

        #  OSPFv2

        self.lsdb_ospfv2.add_lsa(self.lsa_ospfv2_1, None)
        self.assertEqual(1, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual(1, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_type)
        self.assertEqual(
            2147483654, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_sequence_number)
        lsa_ospfv2_3 = lsa.Lsa()
        lsa_ospfv2_3.create_header(1, 34, 1, '1.1.1.1', '1.1.1.1', 10000, conf.VERSION_IPV4)
        lsa_ospfv2_3.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        self.lsdb_ospfv2.add_lsa(lsa_ospfv2_3, None)
        self.assertEqual(1, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual(1, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_type)
        self.assertEqual(10000, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_sequence_number)
        lsa_ospfv2_4 = lsa.Lsa()
        lsa_ospfv2_4.create_header(1, 34, 1, '4.4.4.4', '1.1.1.1', 10000, conf.VERSION_IPV4)
        lsa_ospfv2_4.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        self.lsdb_ospfv2.add_lsa(lsa_ospfv2_4, None)
        self.assertEqual(2, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual('1.1.1.1', self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.link_state_id)
        self.assertEqual('4.4.4.4', self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[1].header.link_state_id)
        self.lsdb_ospfv2.add_lsa(self.lsa_ospfv2_2, None)
        self.assertEqual(3, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual(2, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[2].header.ls_type)

        #  OSPFv3 - Area scope LSAs

        self.lsdb_ospfv3.add_lsa(self.lsa_ospfv3_1, None)
        self.assertEqual(1, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(0x2001, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_type)
        self.assertEqual(
            2147483655, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_sequence_number)
        lsa_ospfv3_5 = lsa.Lsa()
        lsa_ospfv3_5.create_header(1, 0, 1, '0.0.0.0', '2.2.2.2', 10000, conf.VERSION_IPV6)
        lsa_ospfv3_5.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        self.lsdb_ospfv3.add_lsa(lsa_ospfv3_5, None)
        self.assertEqual(1, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(0x2001, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_type)
        self.assertEqual(10000, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_sequence_number)
        lsa_ospfv3_6 = lsa.Lsa()
        lsa_ospfv3_6.create_header(1, 0, 9, '5.5.5.5', '2.2.2.2', 2147483653, conf.VERSION_IPV6)
        lsa_ospfv3_6.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '2.2.2.2')
        self.lsdb_ospfv3.add_lsa(lsa_ospfv3_6, None)
        self.assertEqual(2, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual('0.0.0.0', self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.link_state_id)
        self.assertEqual('5.5.5.5', self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[1].header.link_state_id)
        self.lsdb_ospfv3.add_lsa(self.lsa_ospfv3_2, None)
        self.assertEqual(3, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(0x2001, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_type)
        self.assertEqual(0x2002, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[1].header.ls_type)
        self.assertEqual(0x2009, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[2].header.ls_type)

        #  OSPFv3 - Link-local scope LSAs

        self.interface_ospfv3.link_local_lsa_list = []
        self.lsdb_ospfv3.add_lsa(self.lsa_ospfv3_4, self.interface_ospfv3)
        self.assertEqual(4, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(1, len(self.interface_ospfv3.link_local_lsa_list))
        ls_type = self.lsa_ospfv3_4.header.ls_type
        link_state_id = self.lsa_ospfv3_4.header.link_state_id
        advertising_router = self.lsa_ospfv3_4.header.advertising_router
        self.assertEqual(8, self.interface_ospfv3.get_link_local_lsa(ls_type, link_state_id, advertising_router).
                         header.ls_type)

    def populate_lsdb(self):
        self.lsdb_ospfv2.router_lsa_list.append(self.lsa_ospfv2_1)
        self.lsdb_ospfv2.network_lsa_list.append(self.lsa_ospfv2_2)
        self.lsdb_ospfv3.router_lsa_list.append(self.lsa_ospfv3_1)
        self.lsdb_ospfv3.network_lsa_list.append(self.lsa_ospfv3_2)
        self.lsdb_ospfv3.intra_area_prefix_lsa_list.append(self.lsa_ospfv3_3)
        self.interface_ospfv3.link_local_lsa_list.append(self.lsa_ospfv3_4)

    #  Successful run - Instant
    #  This test is based on the GNS3 Network 1 at https://github.com/migueldgoncalves/ospf-multiarea-arbitrary-topology
    def test_get_directed_graph(self):
        lsdb_v2 = lsdb.Lsdb(conf.VERSION_IPV4)
        lsdb_v3 = lsdb.Lsdb(conf.VERSION_IPV6)
        router_id_1 = '1.1.1.1'
        router_id_2 = '2.2.2.2'
        router_id_3 = '3.3.3.3'
        router_id_4 = '4.4.4.4'
        network_mask = '255.255.255.0'
        prefix_length = 64
        r1_f0_0_v2 = '222.222.3.1'
        r1_f0_1_v2 = '222.222.2.1'
        r1_f1_0_v2 = '222.222.1.1'
        r1_s2_0_v2 = '222.222.6.1'
        r2_f0_0_v2 = '222.222.4.1'
        r2_f0_1_v2 = '222.222.3.2'
        r2_f1_0_v2 = '222.222.5.1'
        r3_f0_0_v2 = '222.222.5.2'
        r3_s1_0_v2 = '222.222.6.2'
        r4_e0_v2 = '222.222.1.2'
        r1_f0_0_v3 = '2001:db8:cafe:3::1'
        r1_f0_1_v3 = '2001:db8:cafe:2::1'
        r1_f1_0_v3 = '2001:db8:cafe:1::1'
        r1_s2_0_v3 = '2001:db8:cafe:6::1'
        r2_f0_0_v3 = '2001:db8:cafe:4::1'
        r2_f0_1_v3 = '2001:db8:cafe:3::2'
        r2_f1_0_v3 = '2001:db8:cafe:5::1'
        r3_f0_0_v3 = '2001:db8:cafe:5::2'
        r3_s1_0_v3 = '2001:db8:cafe:6::2'
        r4_e0_v3 = '2001:db8:cafe:1::2'
        r1_f0_0_local = 'fe80:3::1'
        r1_f0_1_local = 'fe80:2::1'
        r1_f1_0_local = 'fe80:1::1'
        r1_s2_0_local = 'fe80:6::1'
        r2_f0_0_local = 'fe80:4::1'
        r2_f0_1_local = 'fe80:3::2'
        r2_f1_0_local = 'fe80:5::1'
        r3_f0_0_local = 'fe80:5::2'
        r3_s1_0_local = 'fe80:6::2'
        r4_e0_local = 'fe80:1::2'
        prefix_1_v2 = '222.222.1.0'
        prefix_2_v2 = '222.222.2.0'
        prefix_3_v2 = '222.222.3.0'
        prefix_4_v2 = '222.222.4.0'
        prefix_5_v2 = '222.222.5.0'
        prefix_6_v2 = '222.222.6.0'
        prefix_1_v3 = '2001:db8:cafe:1::'
        prefix_2_v3 = '2001:db8:cafe:2::'
        prefix_3_v3 = '2001:db8:cafe:3::'
        prefix_4_v3 = '2001:db8:cafe:4::'
        prefix_5_v3 = '2001:db8:cafe:5::'
        prefix_6_v3 = '2001:db8:cafe:6::'
        r1_f0_0_id = 1
        r1_f0_1_id = 2
        r1_f1_0_id = 3
        r1_s2_0_id = 4
        r2_f0_0_id = 1
        r2_f0_1_id = 2
        r2_f1_0_id = 3
        r3_f0_0_id = 1
        r3_s1_0_id = 2
        r4_e0_id = 1
        network_1_id_v3 = router_id_4 + "|" + str(r4_e0_id)
        network_3_id_v3 = router_id_2 + "|" + str(r2_f0_1_id)
        network_5_id_v3 = router_id_3 + "|" + str(r3_f0_0_id)
        router_priority = 1
        prefix_options = 0
        cost_broadcast_link = 10
        cost_point_point_link = 64

        router_lsa_1_v2 = lsa.Lsa()
        router_lsa_2_v2 = lsa.Lsa()
        router_lsa_3_v2 = lsa.Lsa()
        router_lsa_4_v2 = lsa.Lsa()
        for lsa_data in [[router_id_1, router_lsa_1_v2], [router_id_2, router_lsa_2_v2], [router_id_3, router_lsa_3_v2],
                         [router_id_4, router_lsa_4_v2]]:
            lsa_data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_ROUTER, lsa_data[0], lsa_data[0],
                                      conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
            lsa_data[1].create_router_lsa_body(False, False, False, conf.OPTIONS, conf.VERSION_IPV4)
        network_lsa_1_v2 = lsa.Lsa()
        network_lsa_3_v2 = lsa.Lsa()
        network_lsa_5_v2 = lsa.Lsa()
        for lsa_data in [[router_id_4, network_lsa_1_v2, r4_e0_v2], [router_id_2, network_lsa_3_v2, r2_f0_1_v2],
                         [router_id_3, network_lsa_5_v2, r3_f0_0_v2]]:
            lsa_data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_NETWORK, lsa_data[2],
                                      lsa_data[0], conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
            lsa_data[1].create_network_lsa_body(network_mask, 0, [], conf.VERSION_IPV4)

        router_lsa_1_v3 = lsa.Lsa()
        router_lsa_2_v3 = lsa.Lsa()
        router_lsa_3_v3 = lsa.Lsa()
        router_lsa_4_v3 = lsa.Lsa()
        for lsa_data in [[router_id_1, router_lsa_1_v3], [router_id_2, router_lsa_2_v3], [router_id_3, router_lsa_3_v3],
                         [router_id_4, router_lsa_4_v3]]:
            lsa_data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_ROUTER, 0, lsa_data[0],
                                      conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
            lsa_data[1].create_router_lsa_body(False, False, False, conf.OPTIONS, conf.VERSION_IPV6)
        network_lsa_1_v3 = lsa.Lsa()
        network_lsa_3_v3 = lsa.Lsa()
        network_lsa_5_v3 = lsa.Lsa()
        for lsa_data in [[router_id_4, network_lsa_1_v3, r4_e0_id], [router_id_2, network_lsa_3_v3, r2_f0_1_id],
                         [router_id_3, network_lsa_5_v3, r3_f0_0_id]]:
            lsa_data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_NETWORK, lsa_data[2],
                                      lsa_data[0], conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
            lsa_data[1].create_network_lsa_body('', conf.OPTIONS, [], conf.VERSION_IPV6)
        intra_area_prefix_lsa_r1 = lsa.Lsa()
        intra_area_prefix_lsa_r2 = lsa.Lsa()
        intra_area_prefix_lsa_r3 = lsa.Lsa()
        intra_area_prefix_lsa_r4 = lsa.Lsa()
        intra_area_prefix_lsa_n1 = lsa.Lsa()
        intra_area_prefix_lsa_n3 = lsa.Lsa()
        intra_area_prefix_lsa_n5 = lsa.Lsa()
        for lsa_data in [[router_id_1, intra_area_prefix_lsa_r1, router_lsa_1_v3],
                         [router_id_2, intra_area_prefix_lsa_r2, router_lsa_2_v3],
                         [router_id_3, intra_area_prefix_lsa_r3, router_lsa_3_v3],
                         [router_id_4, intra_area_prefix_lsa_r4, router_lsa_4_v3],
                         [router_id_4, intra_area_prefix_lsa_n1, network_lsa_1_v3],
                         [router_id_2, intra_area_prefix_lsa_n3, network_lsa_3_v3],
                         [router_id_3, intra_area_prefix_lsa_n5, network_lsa_5_v3]]:
            lsa_data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_INTRA_AREA_PREFIX, 0,
                                      lsa_data[0], conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
            lsa_data[1].create_intra_area_prefix_lsa_body(
                lsa_data[2].header.ls_type, lsa_data[2].header.link_state_id, lsa_data[2].header.advertising_router)
        link_lsa_r1_1 = lsa.Lsa()
        link_lsa_r1_2 = lsa.Lsa()
        link_lsa_r1_3 = lsa.Lsa()
        link_lsa_r1_6 = lsa.Lsa()
        link_lsa_r2_3 = lsa.Lsa()
        link_lsa_r2_4 = lsa.Lsa()
        link_lsa_r2_5 = lsa.Lsa()
        link_lsa_r3_5 = lsa.Lsa()
        link_lsa_r3_6 = lsa.Lsa()
        link_lsa_r4_1 = lsa.Lsa()
        for lsa_data in [[router_id_1, link_lsa_r1_1, r1_f1_0_id, prefix_1_v3, r1_f1_0_local, cost_broadcast_link],
                         [router_id_1, link_lsa_r1_2, r1_f0_1_id, prefix_2_v3, r1_f0_1_local, cost_broadcast_link],
                         [router_id_1, link_lsa_r1_6, r1_s2_0_id, prefix_6_v3, r1_s2_0_local, cost_point_point_link],
                         [router_id_1, link_lsa_r1_3, r1_f0_0_id, prefix_3_v3, r1_f0_0_local, cost_broadcast_link],
                         [router_id_2, link_lsa_r2_3, r2_f0_1_id, prefix_3_v3, r2_f0_1_local, cost_broadcast_link],
                         [router_id_2, link_lsa_r2_4, r2_f0_0_id, prefix_4_v3, r2_f0_0_local, cost_broadcast_link],
                         [router_id_2, link_lsa_r2_5, r2_f1_0_id, prefix_5_v3, r2_f1_0_local, cost_broadcast_link],
                         [router_id_3, link_lsa_r3_5, r3_f0_0_id, prefix_5_v3, r3_f0_0_local, cost_broadcast_link],
                         [router_id_3, link_lsa_r3_6, r3_s1_0_id, prefix_6_v3, r3_s1_0_local, cost_point_point_link],
                         [router_id_4, link_lsa_r4_1, r4_e0_id, prefix_1_v3, r4_e0_local, cost_broadcast_link]]:
            lsa_data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_LINK, lsa_data[2], lsa_data[0],
                                      conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
            lsa_data[1].create_link_lsa_body(router_priority, conf.OPTIONS, lsa_data[4])
            lsa_data[1].add_prefix_info(prefix_length, 0, lsa_data[5], lsa_data[3], conf.LSA_TYPE_LINK)

        #  No LSAs

        self.assertEqual([{}, {}], lsdb_v2.get_directed_graph([self.interface_ospfv2]))
        self.assertEqual([{}, {}], lsdb_v3.get_directed_graph([self.interface_ospfv3]))

        #  LSAs for single router (1.1.1.1)

        for link_info in [[prefix_1_v2, cost_broadcast_link], [prefix_2_v2, cost_broadcast_link],
                          [prefix_3_v2, cost_broadcast_link], [prefix_6_v2, cost_point_point_link]]:
            router_lsa_1_v2.add_link_info_v2(
                link_info[0], network_mask, conf.LINK_TO_STUB_NETWORK, conf.DEFAULT_TOS, link_info[1])
        lsdb_v2.router_lsa_list.append(router_lsa_1_v2)
        self.assertEqual([{router_id_1: {}}, {router_id_1: [prefix_1_v2, prefix_2_v2, prefix_3_v2, prefix_6_v2]}],
                         lsdb_v2.get_directed_graph([self.interface_ospfv2]))

        lsdb_v3.router_lsa_list.append(router_lsa_1_v3)
        for prefix_data in [[prefix_1_v3, cost_broadcast_link], [prefix_2_v3, cost_broadcast_link],
                            [prefix_3_v3, cost_broadcast_link], [prefix_6_v3, cost_point_point_link]]:
            intra_area_prefix_lsa_r1.add_prefix_info(
                prefix_length, prefix_options, prefix_data[1], prefix_data[0], conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsdb_v3.intra_area_prefix_lsa_list.append(intra_area_prefix_lsa_r1)
        for prefix_data in [[prefix_1_v3, cost_broadcast_link, link_lsa_r1_1],
                            [prefix_2_v3, cost_broadcast_link, link_lsa_r1_2],
                            [prefix_3_v3, cost_broadcast_link, link_lsa_r1_3],
                            [prefix_6_v3, cost_point_point_link, link_lsa_r1_6]]:
            prefix_data[2].add_prefix_info(
                prefix_length, prefix_options, prefix_data[1], prefix_data[0], conf.LSA_TYPE_LINK)
            self.interface_ospfv3.link_local_lsa_list.append(prefix_data[2])
        self.assertEqual([{router_id_1: {}}, {router_id_1: [prefix_1_v3, prefix_2_v3, prefix_3_v3, prefix_6_v3]}],
                         lsdb_v3.get_directed_graph([self.interface_ospfv3]))

        #  LSAs for 2 connected routers (1.1.1.1 and 2.2.2.2)

        router_lsa_1_v2.body.links = []
        for link_info in [[prefix_1_v2, cost_broadcast_link, conf.LINK_TO_STUB_NETWORK],
                          [prefix_2_v2, cost_broadcast_link, conf.LINK_TO_STUB_NETWORK],
                          [prefix_3_v2, cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK],
                          [prefix_6_v2, cost_point_point_link, conf.LINK_TO_STUB_NETWORK]]:
            router_lsa_1_v2.add_link_info_v2(link_info[0], network_mask, link_info[2], conf.DEFAULT_TOS, link_info[1])
        lsdb_v2.router_lsa_list.append(router_lsa_1_v2)
        for link_info in [[prefix_3_v2, cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK],
                          [prefix_4_v2, cost_broadcast_link, conf.LINK_TO_STUB_NETWORK],
                          [prefix_5_v2, cost_broadcast_link, conf.LINK_TO_STUB_NETWORK]]:
            router_lsa_2_v2.add_link_info_v2(link_info[0], network_mask, link_info[2], conf.DEFAULT_TOS, link_info[1])
        lsdb_v2.router_lsa_list.append(router_lsa_2_v2)
        network_lsa_3_v2.body.attached_routers = [router_id_1, router_id_2]
        lsdb_v2.network_lsa_list.append(network_lsa_3_v2)
        self.assertEqual(
            [{router_id_1: {r2_f0_1_v2: cost_broadcast_link}, r2_f0_1_v2: {router_id_1: 0, router_id_2: 0},
              router_id_2: {r2_f0_1_v2: cost_broadcast_link}},
             {router_id_1: [prefix_1_v2, prefix_2_v2, prefix_6_v2], r2_f0_1_v2: [prefix_3_v2],
              router_id_2: [prefix_4_v2, prefix_5_v2]}], lsdb_v2.get_directed_graph([self.interface_ospfv2]))

        router_lsa_1_v3.add_link_info_v3(
            conf.LINK_TO_TRANSIT_NETWORK, cost_broadcast_link, r1_f0_0_id, r2_f0_1_id, router_id_2)
        lsdb_v3.router_lsa_list.append(router_lsa_1_v3)
        router_lsa_2_v3.add_link_info_v3(
            conf.LINK_TO_TRANSIT_NETWORK, cost_broadcast_link, r2_f0_1_id, r2_f0_1_id, router_id_2)
        lsdb_v3.router_lsa_list.append(router_lsa_2_v3)
        network_lsa_3_v3.body.attached_routers = [router_id_1, router_id_2]
        lsdb_v3.network_lsa_list.append(network_lsa_3_v3)
        intra_area_prefix_lsa_r1.body.prefixes = []
        for prefix_data in [[prefix_1_v3, cost_broadcast_link, intra_area_prefix_lsa_r1],
                            [prefix_2_v3, cost_broadcast_link, intra_area_prefix_lsa_r1],
                            [prefix_6_v3, cost_point_point_link, intra_area_prefix_lsa_r1],
                            [prefix_4_v3, cost_broadcast_link, intra_area_prefix_lsa_r2],
                            [prefix_5_v3, cost_broadcast_link, intra_area_prefix_lsa_r2],
                            [prefix_3_v3, cost_broadcast_link, intra_area_prefix_lsa_n3]]:
            prefix_data[2].add_prefix_info(
                prefix_length, prefix_options, prefix_data[1], prefix_data[0], conf.LSA_TYPE_INTRA_AREA_PREFIX)
        lsdb_v3.intra_area_prefix_lsa_list.append(intra_area_prefix_lsa_r1)
        lsdb_v3.intra_area_prefix_lsa_list.append(intra_area_prefix_lsa_r2)
        lsdb_v3.intra_area_prefix_lsa_list.append(intra_area_prefix_lsa_n3)
        for prefix_data in [[prefix_1_v3, cost_broadcast_link, link_lsa_r1_1],
                            [prefix_2_v3, cost_broadcast_link, link_lsa_r1_2],
                            [prefix_3_v3, cost_broadcast_link, link_lsa_r1_3],
                            [prefix_6_v3, cost_point_point_link, link_lsa_r1_6],
                            [prefix_4_v3, cost_broadcast_link, link_lsa_r2_4],
                            [prefix_5_v3, cost_broadcast_link, link_lsa_r2_5]]:
            prefix_data[2].add_prefix_info(
                prefix_length, prefix_options, prefix_data[1], prefix_data[0], conf.LSA_TYPE_LINK)
            self.interface_ospfv3.link_local_lsa_list.append(prefix_data[2])
        self.assertEqual(
            [{router_id_1: {network_3_id_v3: cost_broadcast_link}, network_3_id_v3: {router_id_1: 0, router_id_2: 0},
              router_id_2: {network_3_id_v3: cost_broadcast_link}},
             {router_id_1: [prefix_1_v3, prefix_2_v3, prefix_6_v3], network_3_id_v3: [prefix_3_v3],
              router_id_2: [prefix_4_v3, prefix_5_v3]}], lsdb_v3.get_directed_graph([self.interface_ospfv3]))

        #  TODO: Continue


