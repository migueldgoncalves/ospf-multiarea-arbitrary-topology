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
            interface_shutdown_v2, conf.VERSION_IPV4, None, False, False)
        self.interface_ospfv3 = interface.Interface(
            conf.ROUTER_ID, interface_identifier, '', ipv6_address, '', link_prefixes, area_id, interface_pipeline_v3,
            interface_shutdown_v3, conf.VERSION_IPV6, None, False, False)

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

        self.lsdb_ospfv2 = lsdb.Lsdb(conf.VERSION_IPV4, conf.BACKBONE_AREA)
        self.lsdb_ospfv3 = lsdb.Lsdb(conf.VERSION_IPV6, conf.BACKBONE_AREA)

    #  Successful run - Instant
    def test_constructor_test(self):
        self.assertEqual(0, len(self.lsdb_ospfv2.router_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv2.network_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv2.intra_area_prefix_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv3.router_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv3.network_lsa_list))
        self.assertEqual(0, len(self.lsdb_ospfv3.intra_area_prefix_lsa_list))
        self.assertFalse(self.lsdb_ospfv2.is_modified.is_set())
        self.assertFalse(self.lsdb_ospfv3.is_modified.is_set())

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
        self.assertFalse(self.lsdb_ospfv2.is_modified.is_set())

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
        self.assertFalse(self.lsdb_ospfv3.is_modified.is_set())

        #  Get a LSA

        retrieved_lsa = self.lsdb_ospfv2.get_lsa(1, '0.0.0.0', '0.0.0.0', [self.interface_ospfv2])
        self.assertIsNone(retrieved_lsa)
        retrieved_lsa = self.lsdb_ospfv2.get_lsa(1, '1.1.1.1', '1.1.1.1', [self.interface_ospfv2])
        self.assertEqual(1, retrieved_lsa.header.ls_type)
        self.assertFalse(self.lsdb_ospfv2.is_modified.is_set())

        retrieved_lsa = self.lsdb_ospfv3.get_lsa(8, '0.0.0.0', '0.0.0.0', [self.interface_ospfv3])
        self.assertIsNone(retrieved_lsa)
        retrieved_lsa = self.lsdb_ospfv3.get_lsa(8, '0.0.0.4', '1.1.1.1', [self.interface_ospfv3])
        self.assertEqual(8, retrieved_lsa.header.ls_type)
        retrieved_lsa = self.lsdb_ospfv3.get_lsa(1, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(0x2001, retrieved_lsa.header.ls_type)
        retrieved_lsa = self.lsdb_ospfv3.get_lsa(0x2001, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(0x2001, retrieved_lsa.header.ls_type)
        self.assertFalse(self.lsdb_ospfv3.is_modified.is_set())

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
        self.assertFalse(self.lsdb_ospfv2.is_modified.is_set())

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
        self.assertFalse(self.lsdb_ospfv3.is_modified.is_set())

        #  Get a LSA header

        retrieved_header = self.lsdb_ospfv2.get_lsa_header(1, '0.0.0.0', '0.0.0.0', [self.interface_ospfv2])
        self.assertIsNone(retrieved_header)
        retrieved_header = self.lsdb_ospfv2.get_lsa_header(2, '222.222.3.2', '2.2.2.2', [self.interface_ospfv2])
        self.assertEqual(2, retrieved_header.ls_type)
        self.assertFalse(self.lsdb_ospfv2.is_modified.is_set())

        retrieved_header = self.lsdb_ospfv3.get_lsa_header(8, '0.0.0.0', '0.0.0.0', [self.interface_ospfv3])
        self.assertIsNone(retrieved_header)
        retrieved_header = self.lsdb_ospfv3.get_lsa_header(8, '0.0.0.4', '1.1.1.1', [self.interface_ospfv3])
        self.assertEqual(8, retrieved_header.ls_type)
        retrieved_header = self.lsdb_ospfv3.get_lsa_header(1, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(0x2001, retrieved_header.ls_type)
        retrieved_header = self.lsdb_ospfv3.get_lsa_header(0x2001, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(0x2001, retrieved_header.ls_type)
        self.assertFalse(self.lsdb_ospfv3.is_modified.is_set())

    #  Successful run - Instant
    def test_delete_lsa(self):
        self.populate_lsdb()

        #  Delete a LSA

        self.lsdb_ospfv2.delete_lsa(1, '0.0.0.0', '0.0.0.0', [self.interface_ospfv2])
        self.assertEqual(2, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv2.is_modified.clear()
        self.lsdb_ospfv2.delete_lsa(1, '1.1.1.1', '1.1.1.1', [self.interface_ospfv2])
        self.assertEqual(1, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual(2, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_type)
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv2.is_modified.clear()
        self.lsdb_ospfv2.delete_lsa(1, '1.1.1.1', '1.1.1.1', [self.interface_ospfv2])
        self.assertEqual(1, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv2.is_modified.clear()
        self.lsdb_ospfv2.delete_lsa(2, '222.222.3.2', '2.2.2.2', [self.interface_ospfv2])
        self.assertEqual(0, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv2.is_modified.clear()

        self.lsdb_ospfv3.delete_lsa(0x2001, '0.0.0.0', '0.0.0.0', [self.interface_ospfv3])
        self.assertEqual(4, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()
        self.lsdb_ospfv3.delete_lsa(0x2001, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(3, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(0x2009, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[1].header.ls_type)
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()
        self.lsdb_ospfv3.delete_lsa(0x2001, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertEqual(3, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()
        self.lsdb_ospfv3.delete_lsa(0x2002, '0.0.0.5', '2.2.2.2', [self.interface_ospfv3])
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()
        self.lsdb_ospfv3.delete_lsa(0x2009, '0.0.0.0', '2.2.2.2', [self.interface_ospfv3])
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()
        self.lsdb_ospfv3.delete_lsa(8, '0.0.0.4', '1.1.1.1', [self.interface_ospfv3])
        self.assertEqual(0, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()

        #  Clean LSDB

        self.populate_lsdb()

        self.lsdb_ospfv2.clean_lsdb([self.interface_ospfv2])
        self.assertEqual(0, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv3.clean_lsdb([self.interface_ospfv3])
        self.assertEqual(0, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())

    #  Successful run - Instant
    def test_add_lsa(self):

        #  OSPFv2

        self.lsdb_ospfv2.add_lsa(self.lsa_ospfv2_1, None)
        self.assertEqual(1, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual(1, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_type)
        self.assertEqual(
            2147483654, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_sequence_number)
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv2.is_modified.clear()
        lsa_ospfv2_3 = lsa.Lsa()
        lsa_ospfv2_3.create_header(1, 34, 1, '1.1.1.1', '1.1.1.1', 10000, conf.VERSION_IPV4)
        lsa_ospfv2_3.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        self.lsdb_ospfv2.add_lsa(lsa_ospfv2_3, None)
        self.assertEqual(1, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual(1, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_type)
        self.assertEqual(10000, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.ls_sequence_number)
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv2.is_modified.clear()
        lsa_ospfv2_4 = lsa.Lsa()
        lsa_ospfv2_4.create_header(1, 34, 1, '4.4.4.4', '1.1.1.1', 10000, conf.VERSION_IPV4)
        lsa_ospfv2_4.create_router_lsa_body(False, False, False, 0, conf.VERSION_IPV4)
        self.lsdb_ospfv2.add_lsa(lsa_ospfv2_4, None)
        self.assertEqual(2, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual('1.1.1.1', self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[0].header.link_state_id)
        self.assertEqual('4.4.4.4', self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[1].header.link_state_id)
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv2.is_modified.clear()
        self.lsdb_ospfv2.add_lsa(self.lsa_ospfv2_2, None)
        self.assertEqual(3, len(self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)))
        self.assertEqual(2, self.lsdb_ospfv2.get_lsdb([self.interface_ospfv2], None)[2].header.ls_type)
        self.assertTrue(self.lsdb_ospfv2.is_modified.is_set())
        self.lsdb_ospfv2.is_modified.clear()

        #  OSPFv3 - Area scope LSAs

        self.lsdb_ospfv3.add_lsa(self.lsa_ospfv3_1, None)
        self.assertEqual(1, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(0x2001, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_type)
        self.assertEqual(
            2147483655, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_sequence_number)
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()
        lsa_ospfv3_5 = lsa.Lsa()
        lsa_ospfv3_5.create_header(1, 0, 1, '0.0.0.0', '2.2.2.2', 10000, conf.VERSION_IPV6)
        lsa_ospfv3_5.create_router_lsa_body(False, False, False, 51, conf.VERSION_IPV6)
        self.lsdb_ospfv3.add_lsa(lsa_ospfv3_5, None)
        self.assertEqual(1, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(0x2001, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_type)
        self.assertEqual(10000, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_sequence_number)
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()
        lsa_ospfv3_6 = lsa.Lsa()
        lsa_ospfv3_6.create_header(1, 0, 9, '5.5.5.5', '2.2.2.2', 2147483653, conf.VERSION_IPV6)
        lsa_ospfv3_6.create_intra_area_prefix_lsa_body(1, '0.0.0.0', '2.2.2.2')
        self.lsdb_ospfv3.add_lsa(lsa_ospfv3_6, None)
        self.assertEqual(2, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual('0.0.0.0', self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.link_state_id)
        self.assertEqual('5.5.5.5', self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[1].header.link_state_id)
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()
        self.lsdb_ospfv3.add_lsa(self.lsa_ospfv3_2, None)
        self.assertEqual(3, len(self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)))
        self.assertEqual(0x2001, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[0].header.ls_type)
        self.assertEqual(0x2002, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[1].header.ls_type)
        self.assertEqual(0x2009, self.lsdb_ospfv3.get_lsdb([self.interface_ospfv3], None)[2].header.ls_type)
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()

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
        self.assertTrue(self.lsdb_ospfv3.is_modified.is_set())
        self.lsdb_ospfv3.is_modified.clear()

    def populate_lsdb(self):
        self.lsdb_ospfv2.router_lsa_list.append(self.lsa_ospfv2_1)
        self.lsdb_ospfv2.network_lsa_list.append(self.lsa_ospfv2_2)
        self.lsdb_ospfv3.router_lsa_list.append(self.lsa_ospfv3_1)
        self.lsdb_ospfv3.network_lsa_list.append(self.lsa_ospfv3_2)
        self.lsdb_ospfv3.intra_area_prefix_lsa_list.append(self.lsa_ospfv3_3)
        self.interface_ospfv3.link_local_lsa_list.append(self.lsa_ospfv3_4)


if __name__ == '__main__':
    unittest.main()
