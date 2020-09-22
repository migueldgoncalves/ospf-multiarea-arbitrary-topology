import unittest
import time
import threading

import router.routing_table as routing_table
import router.router as router
import router.kernel_table as kernel_table
import conf.conf as conf
import area.lsdb as lsdb
import interface.interface as interface
import lsa.lsa as lsa
import general.utils as utils

'''
This class tests the OSPF routing table classes and their operations
'''


#  Full successful run - 42-43 s
class TestRoutingTable(unittest.TestCase):

    #  Setup based on the GNS3 Network 1 at https://github.com/migueldgoncalves/ospf-multiarea-arbitrary-topology
    def setUp(self):
        #  Network variables

        self.router_id_1 = '1.1.1.1'
        self.router_id_2 = '2.2.2.2'
        self.router_id_3 = '3.3.3.3'
        self.router_id_4 = '4.4.4.4'
        self.network_mask = '255.255.255.0'
        self.prefix_length = 64
        self.r1_f0_0_v2 = '222.222.3.1'
        self.r1_f0_1_v2 = '222.222.2.1'
        self.r1_f1_0_v2 = '222.222.1.1'
        self.r1_s2_0_v2 = '222.222.6.1'
        self.r2_f0_0_v2 = '222.222.4.1'
        self.r2_f0_1_v2 = '222.222.3.2'
        self.r2_f1_0_v2 = '222.222.5.1'
        self.r3_f0_0_v2 = '222.222.5.2'
        self.r3_s1_0_v2 = '222.222.6.2'
        self.r4_e0_v2 = '222.222.1.2'
        self.r1_f0_0_v3 = '2001:db8:cafe:3::1'
        self.r1_f0_1_v3 = '2001:db8:cafe:2::1'
        self.r1_f1_0_v3 = '2001:db8:cafe:1::1'
        self.r1_s2_0_v3 = '2001:db8:cafe:6::1'
        self.r2_f0_0_v3 = '2001:db8:cafe:4::1'
        self.r2_f0_1_v3 = '2001:db8:cafe:3::2'
        self.r2_f1_0_v3 = '2001:db8:cafe:5::1'
        self.r3_f0_0_v3 = '2001:db8:cafe:5::2'
        self.r3_s1_0_v3 = '2001:db8:cafe:6::2'
        self.r4_e0_v3 = '2001:db8:cafe:1::2'
        self.r1_f0_0_local = 'fe80:3::1'
        self.r1_f0_1_local = 'fe80:2::1'
        self.r1_f1_0_local = 'fe80:1::1'
        self.r1_s2_0_local = 'fe80:6::1'
        self.r2_f0_0_local = 'fe80:4::1'
        self.r2_f0_1_local = 'fe80:3::2'
        self.r2_f1_0_local = 'fe80:5::1'
        self.r3_f0_0_local = 'fe80:5::2'
        self.r3_s1_0_local = 'fe80:6::2'
        self.r4_e0_local = 'fe80:1::2'
        self.prefix_1_v2 = '222.222.1.0'
        self.prefix_2_v2 = '222.222.2.0'
        self.prefix_3_v2 = '222.222.3.0'
        self.prefix_4_v2 = '222.222.4.0'
        self.prefix_5_v2 = '222.222.5.0'
        self.prefix_6_v2 = '222.222.6.0'
        self.prefix_1_v3 = '2001:db8:cafe:1::'
        self.prefix_2_v3 = '2001:db8:cafe:2::'
        self.prefix_3_v3 = '2001:db8:cafe:3::'
        self.prefix_4_v3 = '2001:db8:cafe:4::'
        self.prefix_5_v3 = '2001:db8:cafe:5::'
        self.prefix_6_v3 = '2001:db8:cafe:6::'
        self.r1_f0_0_id = 1
        self.r1_f0_1_id = 2
        self.r1_f1_0_id = 3
        self.r1_s2_0_id = 4
        self.r2_f0_0_id = 5
        self.r2_f0_1_id = 6
        self.r2_f1_0_id = 7
        self.r3_f0_0_id = 8
        self.r3_s1_0_id = 9
        self.r4_e0_id = 10
        self.network_1_id_v3 = self.router_id_4 + "|" + str(self.r4_e0_id)
        self.network_3_id_v3 = self.router_id_2 + "|" + str(self.r2_f0_1_id)
        self.network_5_id_v3 = self.router_id_3 + "|" + str(self.r3_f0_0_id)

        self.interface_r1_f0_0_v2 = interface.Interface(
            self.router_id_1, 'f0/0', self.r1_f0_0_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r1_f0_1_v2 = interface.Interface(
            self.router_id_1, 'f0/1', self.r1_f0_1_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r1_f1_0_v2 = interface.Interface(
            self.router_id_1, 'f1/0', self.r1_f1_0_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r1_s2_0_v2 = interface.Interface(
            self.router_id_1, 's2/0', self.r1_s2_0_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r2_f0_0_v2 = interface.Interface(
            self.router_id_2, 'f0/0', self.r2_f0_0_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r2_f0_1_v2 = interface.Interface(
            self.router_id_2, 'f0/1', self.r2_f0_1_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r2_f1_0_v2 = interface.Interface(
            self.router_id_2, 'f1/0', self.r2_f1_0_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r3_f0_0_v2 = interface.Interface(
            self.router_id_3, 'f0/0', self.r3_f0_0_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r3_s1_0_v2 = interface.Interface(
            self.router_id_3, 's1/0', self.r3_s1_0_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)
        self.interface_r4_e0_v2 = interface.Interface(
            self.router_id_4, 'e0', self.r4_e0_v2, '', self.network_mask, [], conf.BACKBONE_AREA, None, None,
            conf.VERSION_IPV4, None, False)

        #  Implementation requires physical interface identifier for OSPFv3 to match a VM interface
        self.interface_r1_f0_0_v3 = interface.Interface(
            self.router_id_1, conf.INTERFACE_NAMES[0], '', self.r1_f0_0_v3, '',
            [[self.prefix_3_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r1_f0_1_v3 = interface.Interface(
            self.router_id_1, conf.INTERFACE_NAMES[0], '', self.r1_f0_1_v3, '',
            [[self.prefix_2_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r1_f1_0_v3 = interface.Interface(
            self.router_id_1, conf.INTERFACE_NAMES[0], '', self.r1_f1_0_v3, '',
            [[self.prefix_1_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r1_s2_0_v3 = interface.Interface(
            self.router_id_1, conf.INTERFACE_NAMES[0], '', self.r1_s2_0_v3, '',
            [[self.prefix_6_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r2_f0_0_v3 = interface.Interface(
            self.router_id_2, conf.INTERFACE_NAMES[0], '', self.r2_f0_0_v3, '',
            [[self.prefix_4_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r2_f0_1_v3 = interface.Interface(
            self.router_id_2, conf.INTERFACE_NAMES[0], '', self.r2_f0_1_v3, '',
            [[self.prefix_3_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r2_f1_0_v3 = interface.Interface(
            self.router_id_2, conf.INTERFACE_NAMES[0], '', self.r2_f1_0_v3, '',
            [[self.prefix_5_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r3_f0_0_v3 = interface.Interface(
            self.router_id_3, conf.INTERFACE_NAMES[0], '', self.r3_f0_0_v3, '',
            [[self.prefix_5_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r3_s1_0_v3 = interface.Interface(
            self.router_id_3, conf.INTERFACE_NAMES[0], '', self.r3_s1_0_v3, '',
            [[self.prefix_6_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)
        self.interface_r4_e0_v3 = interface.Interface(
            self.router_id_4, conf.INTERFACE_NAMES[0], '', self.r4_e0_v3, '',
            [[self.prefix_1_v3, self.prefix_length]], conf.BACKBONE_AREA, None, None, conf.VERSION_IPV6, None, False)

        self.interfaces_r1_v2 = [self.interface_r1_f0_0_v2, self.interface_r1_f0_1_v2, self.interface_r1_f1_0_v2,
                                 self.interface_r1_s2_0_v2]
        self.interfaces_r2_v2 = [self.interface_r2_f0_0_v2, self.interface_r2_f0_1_v2, self.interface_r2_f1_0_v2]
        self.interfaces_r3_v2 = [self.interface_r3_f0_0_v2, self.interface_r3_s1_0_v2]
        self.interfaces_r4_v2 = [self.interface_r4_e0_v2]
        self.interfaces_r1_v3 = [self.interface_r1_f0_0_v3, self.interface_r1_f0_1_v3, self.interface_r1_f1_0_v3,
                                 self.interface_r1_s2_0_v3]
        self.interfaces_r2_v3 = [self.interface_r2_f0_0_v3, self.interface_r2_f0_1_v3, self.interface_r2_f1_0_v3]
        self.interfaces_r3_v3 = [self.interface_r3_f0_0_v3, self.interface_r3_s1_0_v3]
        self.interfaces_r4_v3 = [self.interface_r4_e0_v3]

        self.lsdb_v2 = lsdb.Lsdb(conf.VERSION_IPV4, conf.BACKBONE_AREA)
        self.lsdb_v3 = lsdb.Lsdb(conf.VERSION_IPV6, conf.BACKBONE_AREA)

        self.router_priority = 1
        self.prefix_options = 0
        self.cost_broadcast_link = 10
        self.cost_point_point_link = 64

        #  LSA creation

        self.router_lsa_1_v2 = lsa.Lsa()
        self.router_lsa_2_v2 = lsa.Lsa()
        self.router_lsa_3_v2 = lsa.Lsa()
        self.router_lsa_4_v2 = lsa.Lsa()
        for data in [[self.router_id_1, self.router_lsa_1_v2], [self.router_id_2, self.router_lsa_2_v2],
                     [self.router_id_3, self.router_lsa_3_v2], [self.router_id_4, self.router_lsa_4_v2]]:
            data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_ROUTER, data[0], data[0],
                                  conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
            data[1].create_router_lsa_body(False, False, False, conf.OPTIONS, conf.VERSION_IPV4)
        self.network_lsa_1_v2 = lsa.Lsa()
        self.network_lsa_3_v2 = lsa.Lsa()
        self.network_lsa_5_v2 = lsa.Lsa()
        for data in [[self.router_id_4, self.network_lsa_1_v2, self.r4_e0_v2],
                     [self.router_id_2, self.network_lsa_3_v2, self.r2_f0_1_v2],
                     [self.router_id_3, self.network_lsa_5_v2, self.r3_f0_0_v2]]:
            data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_NETWORK, data[2], data[0],
                                  conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
            data[1].create_network_lsa_body(self.network_mask, 0, [], conf.VERSION_IPV4)

        self.router_lsa_1_v3 = lsa.Lsa()
        self.router_lsa_2_v3 = lsa.Lsa()
        self.router_lsa_3_v3 = lsa.Lsa()
        self.router_lsa_4_v3 = lsa.Lsa()
        for data in [[self.router_id_1, self.router_lsa_1_v3], [self.router_id_2, self.router_lsa_2_v3],
                     [self.router_id_3, self.router_lsa_3_v3], [self.router_id_4, self.router_lsa_4_v3]]:
            data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_ROUTER, 0, data[0],
                                  conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
            data[1].create_router_lsa_body(False, False, False, conf.OPTIONS, conf.VERSION_IPV6)
        self.network_lsa_1_v3 = lsa.Lsa()
        self.network_lsa_3_v3 = lsa.Lsa()
        self.network_lsa_5_v3 = lsa.Lsa()
        for data in [[self.router_id_4, self.network_lsa_1_v3, self.r4_e0_id],
                     [self.router_id_2, self.network_lsa_3_v3, self.r2_f0_1_id],
                     [self.router_id_3, self.network_lsa_5_v3, self.r3_f0_0_id]]:
            data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_NETWORK, data[2], data[0],
                                  conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
            data[1].create_network_lsa_body('', conf.OPTIONS, [], conf.VERSION_IPV6)
        self.intra_area_prefix_lsa_r1 = lsa.Lsa()
        self.intra_area_prefix_lsa_r2 = lsa.Lsa()
        self.intra_area_prefix_lsa_r3 = lsa.Lsa()
        self.intra_area_prefix_lsa_r4 = lsa.Lsa()
        self.intra_area_prefix_lsa_n1 = lsa.Lsa()
        self.intra_area_prefix_lsa_n3 = lsa.Lsa()
        self.intra_area_prefix_lsa_n5 = lsa.Lsa()
        for data in [[self.router_id_1, self.intra_area_prefix_lsa_r1, self.router_lsa_1_v3, 0],
                     [self.router_id_2, self.intra_area_prefix_lsa_r2, self.router_lsa_2_v3, 0],
                     [self.router_id_3, self.intra_area_prefix_lsa_r3, self.router_lsa_3_v3, 0],
                     [self.router_id_4, self.intra_area_prefix_lsa_r4, self.router_lsa_4_v3, 0],
                     [self.router_id_4, self.intra_area_prefix_lsa_n1, self.network_lsa_1_v3, self.r4_e0_id],
                     [self.router_id_2, self.intra_area_prefix_lsa_n3, self.network_lsa_3_v3, self.r2_f0_1_id],
                     [self.router_id_3, self.intra_area_prefix_lsa_n5, self.network_lsa_5_v3, self.r3_f0_0_id]]:
            data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_INTRA_AREA_PREFIX, data[3], data[0],
                                  conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
            data[1].create_intra_area_prefix_lsa_body(
                data[2].header.ls_type, data[2].header.link_state_id, data[2].header.advertising_router)
        self.link_lsa_r1_1 = lsa.Lsa()
        self.link_lsa_r1_2 = lsa.Lsa()
        self.link_lsa_r1_3 = lsa.Lsa()
        self.link_lsa_r1_6 = lsa.Lsa()
        self.link_lsa_r2_3 = lsa.Lsa()
        self.link_lsa_r2_4 = lsa.Lsa()
        self.link_lsa_r2_5 = lsa.Lsa()
        self.link_lsa_r3_5 = lsa.Lsa()
        self.link_lsa_r3_6 = lsa.Lsa()
        self.link_lsa_r4_1 = lsa.Lsa()
        for data in [[self.router_id_1, self.link_lsa_r1_1, self.r1_f1_0_id, self.prefix_1_v3, self.r1_f1_0_local,
                      self.cost_broadcast_link],
                     [self.router_id_1, self.link_lsa_r1_2, self.r1_f0_1_id, self.prefix_2_v3, self.r1_f0_1_local,
                      self.cost_broadcast_link],
                     [self.router_id_1, self.link_lsa_r1_6, self.r1_s2_0_id, self.prefix_6_v3, self.r1_s2_0_local,
                      self.cost_point_point_link],
                     [self.router_id_1, self.link_lsa_r1_3, self.r1_f0_0_id, self.prefix_3_v3, self.r1_f0_0_local,
                      self.cost_broadcast_link],
                     [self.router_id_2, self.link_lsa_r2_3, self.r2_f0_1_id, self.prefix_3_v3, self.r2_f0_1_local,
                      self.cost_broadcast_link],
                     [self.router_id_2, self.link_lsa_r2_4, self.r2_f0_0_id, self.prefix_4_v3, self.r2_f0_0_local,
                      self.cost_broadcast_link],
                     [self.router_id_2, self.link_lsa_r2_5, self.r2_f1_0_id, self.prefix_5_v3, self.r2_f1_0_local,
                      self.cost_broadcast_link],
                     [self.router_id_3, self.link_lsa_r3_5, self.r3_f0_0_id, self.prefix_5_v3, self.r3_f0_0_local,
                      self.cost_broadcast_link],
                     [self.router_id_3, self.link_lsa_r3_6, self.r3_s1_0_id, self.prefix_6_v3, self.r3_s1_0_local,
                      self.cost_point_point_link],
                     [self.router_id_4, self.link_lsa_r4_1, self.r4_e0_id, self.prefix_1_v3, self.r4_e0_local,
                      self.cost_broadcast_link]]:
            data[1].create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_LINK, data[2], data[0],
                                  conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
            data[1].create_link_lsa_body(self.router_priority, conf.OPTIONS, data[4])
            data[1].add_prefix_info(self.prefix_length, 0, data[5], data[3], conf.LSA_TYPE_LINK)

    #  Full successful run - Instant
    def test_routing_table(self):
        table = routing_table.RoutingTable()
        self.assertEqual(0, len(table.entries))
        self.assertIsNone(table.get_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA))
        table.delete_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA)
        self.assertEqual(0, len(table.entries))

        table.add_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', 24, 0, conf.BACKBONE_AREA)
        self.assertEqual(1, len(table.entries))
        self.assertEqual('222.222.1.0', table.entries[0].destination_id)
        self.assertIsNotNone(table.get_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA))
        self.assertEqual(24, table.get_entry(
            conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA).prefix_length)
        table.add_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', 24, 0, conf.BACKBONE_AREA)
        self.assertEqual(1, len(table.entries))
        self.assertEqual(24, table.get_entry(
            conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA).prefix_length)
        table.add_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.2.0', 24, 0, conf.BACKBONE_AREA)
        self.assertEqual(2, len(table.entries))
        self.assertEqual('222.222.1.0', table.get_entry(
            conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA).destination_id)
        self.assertEqual('222.222.2.0', table.get_entry(
            conf.DESTINATION_TYPE_NETWORK, '222.222.2.0', conf.BACKBONE_AREA).destination_id)

        table.delete_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA)
        self.assertEqual(1, len(table.entries))
        self.assertIsNone(table.get_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA))
        self.assertEqual('222.222.2.0', table.get_entry(
            conf.DESTINATION_TYPE_NETWORK, '222.222.2.0', conf.BACKBONE_AREA).destination_id)
        table.delete_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.2.0', conf.BACKBONE_AREA)
        self.assertEqual(0, len(table.entries))
        self.assertIsNone(table.get_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', conf.BACKBONE_AREA))

        table.add_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.1.0', 24, 0, conf.BACKBONE_AREA)
        table.add_entry(conf.DESTINATION_TYPE_NETWORK, '222.222.2.0', 24, 0, conf.BACKBONE_AREA)
        table.delete_all_entries()
        self.assertEqual(0, len(table.entries))

    #  Full successful run - Instant
    def test_routing_table_entry(self):
        destination_type = conf.DESTINATION_TYPE_NETWORK
        destination_id = '222.222.1.0'
        prefix_length = 24
        options = 0
        area = conf.BACKBONE_AREA
        entry = routing_table.RoutingTableEntry(destination_type, destination_id, prefix_length, options, area)
        self.assertEqual(destination_type, entry.destination_type)
        self.assertEqual(destination_id, entry.destination_id)
        self.assertEqual(prefix_length, entry.prefix_length)
        self.assertEqual(options, entry.options)
        self.assertEqual(area, entry.area)
        self.assertEqual(0, len(entry.paths))
        self.assertIsNone(entry.get_path('ens33', '222.222.1.1', ''))
        entry.delete_path('ens33', '222.222.1.1', '')
        self.assertEqual(0, len(entry.paths))

        entry.add_path(conf.INTRA_AREA_PATH, 10, 0, 'ens33', '222.222.1.1', '')
        self.assertEqual(1, len(entry.paths))
        self.assertEqual('ens33', entry.paths[0].outgoing_interface)
        self.assertIsNotNone(entry.get_path('ens33', '222.222.1.1', ''))
        self.assertEqual(10, entry.get_path('ens33', '222.222.1.1', '').cost)
        entry.add_path(conf.INTER_AREA_PATH, 20, 10, 'ens33', '222.222.1.1', '')
        self.assertEqual(1, len(entry.paths))
        self.assertEqual(0, entry.get_path('ens33', '222.222.1.1', '').type_2_cost)
        entry.add_path(conf.INTER_AREA_PATH, 20, 10, 'ens38', '222.222.2.1', '1.1.1.1')  # Creates a warning
        self.assertEqual(1, len(entry.paths))
        self.assertEqual(0, entry.get_path('ens33', '222.222.1.1', '').type_2_cost)
        entry.add_path(conf.INTRA_AREA_PATH, 10, 30, 'ens38', '222.222.2.1', '1.1.1.1')
        self.assertEqual(2, len(entry.paths))
        self.assertEqual('ens33', entry.get_path('ens33', '222.222.1.1', '').outgoing_interface)
        self.assertEqual('ens38', entry.get_path('ens38', '222.222.2.1', '1.1.1.1').outgoing_interface)

        entry.delete_path('ens33', '222.222.1.1', '')
        self.assertEqual(1, len(entry.paths))
        self.assertEqual('ens38', entry.paths[0].outgoing_interface)
        entry.delete_path('ens33', '222.222.1.1', '')
        self.assertEqual(1, len(entry.paths))
        entry.delete_path('ens38', '222.222.2.1', '1.1.1.1')
        self.assertEqual(0, len(entry.paths))

        entry.add_path(conf.INTRA_AREA_PATH, 10, 0, 'ens33', '222.222.1.1', '')
        entry.add_path(conf.INTRA_AREA_PATH, 10, 30, 'ens38', '222.222.2.1', '1.1.1.1')
        entry.delete_all_paths()
        self.assertEqual(0, len(entry.paths))

    #  Full successful run - Instant
    def test_routing_table_path(self):
        path_type = conf.INTRA_AREA_PATH
        cost = 10
        type_2_cost = 0
        outgoing_interface = 'ens33'
        next_hop_address = '222.222.1.1'
        advertising_router = ''
        path = routing_table.RoutingTablePath(
            path_type, cost, type_2_cost, outgoing_interface, next_hop_address, advertising_router)
        self.assertEqual(path_type, path.path_type)
        self.assertEqual(cost, path.cost)
        self.assertEqual(type_2_cost, path.type_2_cost)
        self.assertEqual(outgoing_interface, path.outgoing_interface)
        self.assertEqual(next_hop_address, path.next_hop_address)
        self.assertEqual(advertising_router, path.advertising_router)

    #  The following tests test the methods related to the creation of the routing table, regardless of their class

    #  Successful run - Instant
    def test_get_directed_graph(self):
        #  No LSAs

        self.assertEqual([{}, {}], self.lsdb_v2.get_directed_graph(self.interfaces_r1_v2))
        self.assertEqual([{}, {}], self.lsdb_v3.get_directed_graph(self.interfaces_r1_v3))

        #  LSAs for single router (1.1.1.1)

        self.set_lsdb_router_1_1_1_1(self.interfaces_r1_v2, self.interfaces_r1_v3)

        directed_graph = {self.router_id_1: {}}
        prefixes = {self.router_id_1: [self.prefix_1_v2, self.prefix_2_v2, self.prefix_3_v2, self.prefix_6_v2]}
        self.assertEqual([directed_graph, prefixes], self.lsdb_v2.get_directed_graph(self.interfaces_r1_v2))

        directed_graph = {self.router_id_1: {}}
        prefixes = {self.router_id_1: [self.prefix_1_v3, self.prefix_2_v3, self.prefix_3_v3, self.prefix_6_v3]}
        self.assertEqual([directed_graph, prefixes], self.lsdb_v3.get_directed_graph(self.interfaces_r1_v3))

        self.lsdb_v2.clean_lsdb(self.interfaces_r1_v2)
        self.lsdb_v3.clean_lsdb(self.interfaces_r1_v3)

        #  LSAs for 2 connected routers (1.1.1.1 and 2.2.2.2)

        self.router_lsa_1_v2.body.links = []
        for data in [[self.prefix_1_v2, self.network_mask, self.cost_broadcast_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_1_v2],
                     [self.prefix_2_v2, self.network_mask, self.cost_broadcast_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_1_v2],
                     [self.r2_f0_1_v2, self.r1_f0_0_v2, self.cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK,
                      self.router_lsa_1_v2],
                     [self.prefix_6_v2, self.network_mask, self.cost_point_point_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_1_v2],
                     [self.r2_f0_1_v2, self.r2_f0_1_v2, self.cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK,
                      self.router_lsa_2_v2],
                     [self.prefix_4_v2, self.network_mask, self.cost_broadcast_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_2_v2],
                     [self.prefix_5_v2, self.network_mask, self.cost_broadcast_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_2_v2]]:
            router_lsa = data[4]
            router_lsa.add_link_info_v2(data[0], data[1], data[3], conf.DEFAULT_TOS, data[2])
        for router_lsa in [self.router_lsa_1_v2, self.router_lsa_2_v2]:
            self.lsdb_v2.router_lsa_list.append(router_lsa)
        self.network_lsa_3_v2.body.attached_routers = [self.router_id_1, self.router_id_2]
        self.lsdb_v2.network_lsa_list.append(self.network_lsa_3_v2)
        directed_graph = {self.router_id_1: {self.r2_f0_1_v2: self.cost_broadcast_link}, self.r2_f0_1_v2: {
            self.router_id_1: 0, self.router_id_2: 0}, self.router_id_2: {self.r2_f0_1_v2: self.cost_broadcast_link}}
        prefixes = {self.router_id_1: [self.prefix_1_v2, self.prefix_2_v2, self.prefix_6_v2],
                    self.r2_f0_1_v2: [self.prefix_3_v2], self.router_id_2: [self.prefix_4_v2, self.prefix_5_v2]}
        self.assertEqual([directed_graph, prefixes], self.lsdb_v2.get_directed_graph(self.interfaces_r1_v2))

        for data in [[self.r1_f0_0_id, self.router_lsa_1_v3], [self.r2_f0_1_id, self.router_lsa_2_v3]]:
            data[1].add_link_info_v3(
                conf.LINK_TO_TRANSIT_NETWORK, self.cost_broadcast_link, data[0], self.r2_f0_1_id, self.router_id_2)
            self.lsdb_v3.router_lsa_list.append(data[1])
        self.network_lsa_3_v3.body.attached_routers = [self.router_id_1, self.router_id_2]
        self.lsdb_v3.network_lsa_list.append(self.network_lsa_3_v3)
        self.intra_area_prefix_lsa_r1.body.prefixes = []
        for data in [[self.prefix_1_v3, self.cost_broadcast_link, self.intra_area_prefix_lsa_r1],
                     [self.prefix_2_v3, self.cost_broadcast_link, self.intra_area_prefix_lsa_r1],
                     [self.prefix_6_v3, self.cost_point_point_link, self.intra_area_prefix_lsa_r1],
                     [self.prefix_4_v3, self.cost_broadcast_link, self.intra_area_prefix_lsa_r2],
                     [self.prefix_5_v3, self.cost_broadcast_link, self.intra_area_prefix_lsa_r2],
                     [self.prefix_3_v3, self.cost_broadcast_link, self.intra_area_prefix_lsa_n3]]:
            data[2].add_prefix_info(
                self.prefix_length, self.prefix_options, data[1], data[0], conf.LSA_TYPE_INTRA_AREA_PREFIX)
        self.lsdb_v3.intra_area_prefix_lsa_list.append(self.intra_area_prefix_lsa_r1)
        self.lsdb_v3.intra_area_prefix_lsa_list.append(self.intra_area_prefix_lsa_r2)
        self.lsdb_v3.intra_area_prefix_lsa_list.append(self.intra_area_prefix_lsa_n3)
        for data in [[self.prefix_1_v3, self.cost_broadcast_link, self.link_lsa_r1_1, self.interface_r1_f1_0_v3],
                     [self.prefix_2_v3, self.cost_broadcast_link, self.link_lsa_r1_2, self.interface_r1_f0_1_v3],
                     [self.prefix_3_v3, self.cost_broadcast_link, self.link_lsa_r1_3, self.interface_r1_f0_0_v3],
                     [self.prefix_6_v3, self.cost_point_point_link, self.link_lsa_r1_6, self.interface_r1_s2_0_v3],
                     [self.prefix_3_v3, self.cost_broadcast_link, self.link_lsa_r2_3, self.interface_r2_f0_1_v3],
                     [self.prefix_4_v3, self.cost_broadcast_link, self.link_lsa_r2_4, self.interface_r2_f0_0_v3],
                     [self.prefix_5_v3, self.cost_broadcast_link, self.link_lsa_r2_5, self.interface_r2_f1_0_v3]]:
            data[2].add_prefix_info(self.prefix_length, self.prefix_options, data[1], data[0], conf.LSA_TYPE_LINK)
            data[3].link_local_lsa_list.append(data[2])
        directed_graph = {self.router_id_1: {self.network_3_id_v3: self.cost_broadcast_link},
                          self.router_id_2: {self.network_3_id_v3: self.cost_broadcast_link},
                          self.network_3_id_v3: {self.router_id_1: 0, self.router_id_2: 0}}
        prefixes = {self.router_id_1: [self.prefix_1_v3, self.prefix_2_v3, self.prefix_6_v3],
                    self.router_id_2: [self.prefix_4_v3, self.prefix_5_v3],
                    self.network_3_id_v3: [self.prefix_3_v3]}
        self.assertEqual([directed_graph, prefixes], self.lsdb_v3.get_directed_graph(self.interfaces_r1_v3))

        self.lsdb_v2.clean_lsdb(self.interfaces_r1_v2)
        self.lsdb_v3.clean_lsdb(self.interfaces_r1_v3)

        #  LSAs for full network

        self.set_lsdb_full_network(self.interfaces_r1_v2, self.interfaces_r1_v3)

        directed_graph, prefixes = self.get_directed_graph_prefixes_full_network(conf.VERSION_IPV4)
        self.assertEqual([directed_graph, prefixes], self.lsdb_v2.get_directed_graph(self.interfaces_r1_v2))

        directed_graph, prefixes = self.get_directed_graph_prefixes_full_network(conf.VERSION_IPV6)
        self.assertEqual([directed_graph, prefixes], self.lsdb_v3.get_directed_graph(self.interfaces_r1_v3))

        self.lsdb_v2.clean_lsdb(self.interfaces_r1_v2)
        self.lsdb_v3.clean_lsdb(self.interfaces_r1_v3)

    #  Successful run - Instant
    def test_get_shortest_path_tree(self):
        router_id_1 = '1.1.1.1'
        router_id_2 = '2.2.2.2'
        router_id_3 = '3.3.3.3'
        router_id_4 = '4.4.4.4'
        network_id_1 = 'network_1'
        network_id_2 = 'network_2'
        cost = 10

        #  Single router

        directed_graph = {router_id_1: {}}
        self.assertEqual({router_id_1: [0, router_id_1]}, lsdb.Lsdb.get_shortest_path_tree(
            directed_graph, router_id_1))

        #  2 routers directly connected

        directed_graph = {router_id_1: {router_id_2: cost}, router_id_2: {
            router_id_1: cost}}
        self.assertEqual({router_id_1: [0, router_id_1], router_id_2: [cost, router_id_1]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual({router_id_2: [0, router_id_2], router_id_1: [cost, router_id_2]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))

        #  2 routers connected through transit link

        directed_graph = {router_id_1: {network_id_1: cost}, router_id_2: {
            network_id_1: cost}, network_id_1: {router_id_1: 0, router_id_2: 0}}
        self.assertEqual(
            {router_id_1: [0, router_id_1], router_id_2: [cost, network_id_1], network_id_1: [cost, router_id_1]},
            lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual(
            {router_id_2: [0, router_id_2], router_id_1: [cost, network_id_1], network_id_1: [cost, router_id_2]},
            lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))
        #  Routers are disconnected
        directed_graph = {router_id_1: {}, router_id_2: {}}
        self.assertEqual({router_id_1: [0, router_id_1]}, lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual({router_id_2: [0, router_id_2]}, lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))

        #  3 routers connected through transit link

        directed_graph = {router_id_1: {network_id_1: cost},
                          router_id_2: {network_id_1: cost},
                          router_id_3: {network_id_1: cost},
                          network_id_1: {router_id_1: 0, router_id_2: 0, router_id_3: 0}}
        self.assertEqual(
            {router_id_1: [0, router_id_1], router_id_2: [cost, network_id_1], router_id_3: [cost, network_id_1],
             network_id_1: [cost, router_id_1]},
            lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual(
            {router_id_1: [cost, network_id_1], router_id_2: [0, router_id_2], router_id_3: [cost, network_id_1],
             network_id_1: [cost, router_id_2]},
            lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))
        self.assertEqual(
            {router_id_1: [cost, network_id_1], router_id_2: [cost, network_id_1], router_id_3: [0, router_id_3],
             network_id_1: [cost, router_id_3]},
            lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_3))

        #  2 networks respectively with 3 and 2 routers

        directed_graph = {router_id_1: {network_id_1: cost, network_id_2: cost},
                          router_id_2: {network_id_1: cost},
                          router_id_3: {network_id_1: cost},
                          router_id_4: {network_id_2: cost},
                          network_id_1: {router_id_1: 0, router_id_2: 0, router_id_3: 0},
                          network_id_2: {router_id_1: 0, router_id_4: 0}}
        self.assertEqual(
            {router_id_1: [0, router_id_1], router_id_2: [cost, network_id_1], router_id_3: [cost, network_id_1],
             router_id_4: [cost, network_id_2], network_id_1: [cost, router_id_1],
             network_id_2: [cost, router_id_1]}, lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual(
            {router_id_1: [cost, network_id_1], router_id_2: [0, router_id_2], router_id_3: [cost, network_id_1],
             router_id_4: [2 * cost, network_id_2], network_id_1: [cost, router_id_2],
             network_id_2: [2 * cost, router_id_1]}, lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))
        self.assertEqual(
            {router_id_1: [cost, network_id_1], router_id_2: [cost, network_id_1], router_id_3: [0, router_id_3],
             router_id_4: [2 * cost, network_id_2], network_id_1: [cost, router_id_3],
             network_id_2: [2 * cost, router_id_1]}, lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_3))
        self.assertEqual(
            {router_id_1: [cost, network_id_2], router_id_2: [2 * cost, network_id_1],
             router_id_3: [2 * cost, network_id_1], router_id_4: [0, router_id_4],
             network_id_1: [2 * cost, router_id_1], network_id_2: [cost, router_id_4]},
            lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_4))

        #  Triangular network - 2 point-to-point links and 1 transit link

        #  2 equal-cost paths from Router 1 to Network 1 - One is placed on the tree
        directed_graph = {router_id_1: {router_id_2: cost, router_id_3: cost},
                          router_id_2: {router_id_1: cost, network_id_1: cost},
                          router_id_3: {router_id_1: cost, network_id_1: cost},
                          network_id_1: {router_id_2: 0, router_id_3: 0}}  # All costs equal
        self.assertEqual({router_id_1: [0, router_id_1], router_id_2: [cost, router_id_1],
                          router_id_3: [cost, router_id_1], network_id_1: [2 * cost, router_id_2]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual({router_id_1: [cost, router_id_2], router_id_2: [0, router_id_2],
                          router_id_3: [cost, network_id_1], network_id_1: [cost, router_id_2]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))
        self.assertEqual({router_id_1: [cost, router_id_3], router_id_2: [cost, network_id_1],
                          router_id_3: [0, router_id_3], network_id_1: [cost, router_id_3]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_3))
        #  Shortest path from Router 1 to Network 1 is through Router 3
        directed_graph = {router_id_1: {router_id_2: cost, router_id_3: cost},
                          router_id_2: {router_id_1: cost, network_id_1: 2 * cost},
                          router_id_3: {router_id_1: cost, network_id_1: cost},
                          network_id_1: {router_id_2: 0, router_id_3: 0}}
        self.assertEqual({router_id_1: [0, router_id_1], router_id_2: [cost, router_id_1],
                          router_id_3: [cost, router_id_1], network_id_1: [2 * cost, router_id_3]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual({router_id_1: [cost, router_id_2], router_id_2: [0, router_id_2],
                          router_id_3: [2 * cost, router_id_1],
                          network_id_1: [2 * cost, router_id_2]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))
        self.assertEqual({router_id_1: [cost, router_id_3], router_id_2: [cost, network_id_1],
                          router_id_3: [0, router_id_3], network_id_1: [cost, router_id_3]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_3))
        #  Shortest path from Router 2 to Network 1 and Router 3 is no longer the direct route
        directed_graph = {router_id_1: {router_id_2: cost, router_id_3: cost},
                          router_id_2: {router_id_1: cost, network_id_1: 4 * cost},
                          router_id_3: {router_id_1: cost, network_id_1: cost},
                          network_id_1: {router_id_2: 0, router_id_3: 0}}
        self.assertEqual({router_id_1: [0, router_id_1], router_id_2: [cost, router_id_1],
                          router_id_3: [cost, router_id_1], network_id_1: [2 * cost, router_id_3]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual({router_id_1: [cost, router_id_2], router_id_2: [0, router_id_2],
                          router_id_3: [2 * cost, router_id_1], network_id_1: [3 * cost, router_id_3]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))
        self.assertEqual({router_id_1: [cost, router_id_3], router_id_2: [cost, network_id_1],
                          router_id_3: [0, router_id_3], network_id_1: [cost, router_id_3]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_3))
        #  Router 2 becomes isolated in the network
        directed_graph = {router_id_1: {router_id_3: cost}, router_id_2: {}, router_id_3: {router_id_1: cost}}
        self.assertEqual({router_id_1: [0, router_id_1], router_id_3: [cost, router_id_1]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual({router_id_2: [0, router_id_2]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))
        self.assertEqual({router_id_1: [cost, router_id_3], router_id_3: [0, router_id_3]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_3))
        #  Network 1 becomes isolated in the network
        directed_graph = {router_id_1: {router_id_2: cost, router_id_3: cost},
                          router_id_2: {router_id_1: cost},
                          router_id_3: {router_id_1: cost},
                          network_id_1: {}}
        self.assertEqual({router_id_1: [0, router_id_1], router_id_2: [cost, router_id_1],
                          router_id_3: [cost, router_id_1]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_1))
        self.assertEqual({router_id_1: [cost, router_id_2], router_id_2: [0, router_id_2],
                          router_id_3: [2 * cost, router_id_1]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_2))
        self.assertEqual({router_id_1: [cost, router_id_3], router_id_2: [2 * cost, router_id_1],
                          router_id_3: [0, router_id_3]},
                         lsdb.Lsdb.get_shortest_path_tree(directed_graph, router_id_3))

    #  Successful run - 0-1 s
    def test_get_intra_area_routing_table(self):
        #  Startup

        router_v2 = router.Router(self.router_id_4, conf.VERSION_IPV4, None, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS,
                                  False)
        router_v3 = router.Router(self.router_id_4, conf.VERSION_IPV6, None, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS,
                                  False)
        router_v2.shutdown_router()  # Router threads are not necessary for this test, only its data objects
        router_v3.shutdown_router()
        router_v2.areas[conf.BACKBONE_AREA].database = self.lsdb_v2  # Overwriting the router LSDB
        router_v3.areas[conf.BACKBONE_AREA].database = self.lsdb_v3

        #  1 router (4.4.4.4)

        #  Overwriting the router interface and its physical identifier
        self.interface_r4_e0_v2.physical_identifier = 'e0'
        self.interface_r4_e0_v3.physical_identifier = 'e0'
        router_v2.areas[conf.BACKBONE_AREA].interfaces = {'e0': [self.interface_r4_e0_v2, None, None, None]}
        router_v3.areas[conf.BACKBONE_AREA].interfaces = {'e0': [self.interface_r4_e0_v3, None, None, None]}

        self.router_lsa_4_v2.add_link_info_v2(
            self.prefix_1_v2, self.network_mask, conf.LINK_TO_STUB_NETWORK, conf.DEFAULT_TOS, self.cost_broadcast_link)
        self.lsdb_v2.router_lsa_list.append(self.router_lsa_4_v2)
        directed_graph = {self.router_id_4: {}}
        prefixes_dictionary = {conf.BACKBONE_AREA: {self.router_id_4: [self.prefix_1_v2]}}
        shortest_path_tree_dictionary = {conf.BACKBONE_AREA: self.lsdb_v2.get_shortest_path_tree(
            directed_graph, self.router_id_4)}
        table = router_v2.get_intra_area_routing_table(shortest_path_tree_dictionary, prefixes_dictionary)
        self.assertEqual(1, len(table.entries))
        entry_1 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_1_v2, conf.BACKBONE_AREA)
        self.assertIsNotNone(entry_1)
        self.assertEqual(conf.DESTINATION_TYPE_NETWORK, entry_1.destination_type)
        self.assertEqual(self.prefix_1_v2, entry_1.destination_id)
        self.assertEqual(utils.Utils.get_prefix_length_from_prefix(self.network_mask), entry_1.prefix_length)
        self.assertEqual(conf.OPTIONS, entry_1.options)
        self.assertEqual(conf.BACKBONE_AREA, entry_1.area)
        self.assertEqual(1, len(entry_1.paths))
        path = entry_1.get_path('e0', '', '')
        self.assertIsNotNone(path)
        self.assertEqual(conf.INTRA_AREA_PATH, path.path_type)
        self.assertEqual(self.cost_broadcast_link, path.cost)
        self.assertEqual(0, path.type_2_cost)
        self.assertEqual('e0', path.outgoing_interface)
        self.assertEqual('', path.next_hop_address)
        self.assertEqual('', path.advertising_router)

        self.lsdb_v3.router_lsa_list.append(self.router_lsa_4_v3)
        self.intra_area_prefix_lsa_r4.add_prefix_info(self.prefix_length, self.prefix_options, self.cost_broadcast_link,
                                                      self.prefix_1_v3, conf.LSA_TYPE_INTRA_AREA_PREFIX)
        self.lsdb_v3.intra_area_prefix_lsa_list.append(self.intra_area_prefix_lsa_r4)
        self.link_lsa_r4_1.add_prefix_info(
            self.prefix_length, self.prefix_options, self.cost_broadcast_link, self.prefix_1_v3, conf.LSA_TYPE_LINK)
        self.interface_r4_e0_v3.link_local_lsa_list.append(self.link_lsa_r4_1)
        directed_graph = {self.router_id_4: {}}
        prefixes_dictionary = {conf.BACKBONE_AREA: {self.router_id_4: [self.prefix_1_v3]}}
        shortest_path_tree_dictionary = {conf.BACKBONE_AREA: self.lsdb_v3.get_shortest_path_tree(
            directed_graph, self.router_id_4)}
        table = router_v3.get_intra_area_routing_table(shortest_path_tree_dictionary, prefixes_dictionary)
        self.assertEqual(1, len(table.entries))
        entry_1 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_1_v3, conf.BACKBONE_AREA)
        self.assertIsNotNone(entry_1)
        self.assertEqual(conf.DESTINATION_TYPE_NETWORK, entry_1.destination_type)
        self.assertEqual(self.prefix_1_v3, entry_1.destination_id)
        self.assertEqual(self.prefix_length, entry_1.prefix_length)
        self.assertEqual(conf.OPTIONS, entry_1.options)
        self.assertEqual(conf.BACKBONE_AREA, entry_1.area)
        self.assertEqual(1, len(entry_1.paths))
        path = entry_1.get_path('e0', '', '')
        self.assertIsNotNone(path)
        self.assertEqual(conf.INTRA_AREA_PATH, path.path_type)
        self.assertEqual(self.cost_broadcast_link, path.cost)
        self.assertEqual(0, path.type_2_cost)
        self.assertEqual('e0', path.outgoing_interface)
        self.assertEqual('', path.next_hop_address)
        self.assertEqual('', path.advertising_router)

        self.lsdb_v2.clean_lsdb(self.interfaces_r4_v2)
        self.lsdb_v3.clean_lsdb(self.interfaces_r4_v3)

        #  1 router (1.1.1.1)

        self.set_lsdb_router_1_1_1_1(self.interfaces_r1_v2, self.interfaces_r1_v3)
        self.interface_r1_f1_0_v2.physical_identifier = 'f1/0'
        self.interface_r1_f0_1_v2.physical_identifier = 'f0/1'
        self.interface_r1_f0_0_v2.physical_identifier = 'f0/0'
        self.interface_r1_s2_0_v2.physical_identifier = 's2/0'
        router_v2.areas[conf.BACKBONE_AREA].interfaces = {
            'f1/0': [self.interface_r1_f1_0_v2, None, None, None],
            'f0/1': [self.interface_r1_f0_1_v2, None, None, None],
            'f0/0': [self.interface_r1_f0_0_v2, None, None, None],
            's2/0': [self.interface_r1_s2_0_v2, None, None, None]}
        self.interface_r1_f1_0_v3.physical_identifier = 'f1/0'
        self.interface_r1_f0_1_v3.physical_identifier = 'f0/1'
        self.interface_r1_f0_0_v3.physical_identifier = 'f0/0'
        self.interface_r1_s2_0_v3.physical_identifier = 's2/0'
        router_v3.areas[conf.BACKBONE_AREA].interfaces = {
            'f1/0': [self.interface_r1_f1_0_v3, None, None, None],
            'f0/1': [self.interface_r1_f0_1_v3, None, None, None],
            'f0/0': [self.interface_r1_f0_0_v3, None, None, None],
            's2/0': [self.interface_r1_s2_0_v3, None, None, None]}

        directed_graph = {self.router_id_1: {}}
        prefixes_dictionary = {conf.BACKBONE_AREA: {self.router_id_1: [
            self.prefix_1_v2, self.prefix_2_v2, self.prefix_3_v2, self.prefix_6_v2]}}
        shortest_path_tree_dictionary = {conf.BACKBONE_AREA: self.lsdb_v2.get_shortest_path_tree(
            directed_graph, self.router_id_1)}
        table = router_v2.get_intra_area_routing_table(shortest_path_tree_dictionary, prefixes_dictionary)
        self.assertEqual(4, len(table.entries))
        entry_1 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_1_v2, conf.BACKBONE_AREA)
        entry_2 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_2_v2, conf.BACKBONE_AREA)
        entry_3 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_3_v2, conf.BACKBONE_AREA)
        entry_6 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_6_v2, conf.BACKBONE_AREA)
        for data in [[entry_1, self.prefix_1_v2, 'f1/0', self.cost_broadcast_link],
                     [entry_2, self.prefix_2_v2, 'f0/1', self.cost_broadcast_link],
                     [entry_3, self.prefix_3_v2, 'f0/0', self.cost_broadcast_link],
                     [entry_6, self.prefix_6_v2, 's2/0', self.cost_point_point_link]]:
            self.assertIsNotNone(data[0])
            self.assertEqual(conf.DESTINATION_TYPE_NETWORK, data[0].destination_type)
            self.assertEqual(data[1], data[0].destination_id)
            self.assertEqual(utils.Utils.get_prefix_length_from_prefix(self.network_mask), data[0].prefix_length)
            self.assertEqual(conf.OPTIONS, data[0].options)
            self.assertEqual(conf.BACKBONE_AREA, data[0].area)
            self.assertEqual(1, len(data[0].paths))
            path = data[0].get_path(data[2], '', '')
            self.assertIsNotNone(path)
            self.assertEqual(conf.INTRA_AREA_PATH, path.path_type)
            self.assertEqual(data[3], path.cost)
            self.assertEqual(0, path.type_2_cost)
            self.assertEqual(data[2], path.outgoing_interface)
            self.assertEqual('', path.next_hop_address)
            self.assertEqual('', path.advertising_router)

        directed_graph = {self.router_id_1: {}}
        prefixes_dictionary = {conf.BACKBONE_AREA: {self.router_id_1: [
            self.prefix_1_v3, self.prefix_2_v3, self.prefix_3_v3, self.prefix_6_v3]}}
        shortest_path_tree_dictionary = {conf.BACKBONE_AREA: self.lsdb_v3.get_shortest_path_tree(
            directed_graph, self.router_id_1)}
        table = router_v3.get_intra_area_routing_table(shortest_path_tree_dictionary, prefixes_dictionary)
        self.assertEqual(4, len(table.entries))
        entry_1 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_1_v3, conf.BACKBONE_AREA)
        entry_2 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_2_v3, conf.BACKBONE_AREA)
        entry_3 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_3_v3, conf.BACKBONE_AREA)
        entry_6 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_6_v3, conf.BACKBONE_AREA)
        for data in [[entry_1, self.prefix_1_v3, 'f1/0', self.cost_broadcast_link],
                     [entry_2, self.prefix_2_v3, 'f0/1', self.cost_broadcast_link],
                     [entry_3, self.prefix_3_v3, 'f0/0', self.cost_broadcast_link],
                     [entry_6, self.prefix_6_v3, 's2/0', self.cost_point_point_link]]:
            self.assertIsNotNone(data[0])
            self.assertEqual(conf.DESTINATION_TYPE_NETWORK, data[0].destination_type)
            self.assertEqual(data[1], data[0].destination_id)
            self.assertEqual(self.prefix_length, data[0].prefix_length)
            self.assertEqual(conf.OPTIONS, data[0].options)
            self.assertEqual(conf.BACKBONE_AREA, data[0].area)
            self.assertEqual(1, len(data[0].paths))
            path = data[0].get_path(data[2], '', '')
            self.assertIsNotNone(path)
            self.assertEqual(conf.INTRA_AREA_PATH, path.path_type)
            self.assertEqual(data[3], path.cost)
            self.assertEqual(0, path.type_2_cost)
            self.assertEqual(data[2], path.outgoing_interface)
            self.assertEqual('', path.next_hop_address)
            self.assertEqual('', path.advertising_router)

        self.lsdb_v2.clean_lsdb(self.interfaces_r1_v2)
        self.lsdb_v3.clean_lsdb(self.interfaces_r1_v3)

        #  Full network (point of view of 1.1.1.1)

        self.set_lsdb_full_network(self.interfaces_r1_v2, self.interfaces_r1_v3)

        directed_graph, prefixes = self.get_directed_graph_prefixes_full_network(conf.VERSION_IPV4)
        shortest_path_tree_dictionary = {conf.BACKBONE_AREA: self.lsdb_v2.get_shortest_path_tree(
            directed_graph, self.router_id_1)}
        prefixes_dictionary = {conf.BACKBONE_AREA: prefixes}
        table = router_v2.get_intra_area_routing_table(shortest_path_tree_dictionary, prefixes_dictionary)
        self.assertEqual(6, len(table.entries))
        entry_1 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_1_v2, conf.BACKBONE_AREA)
        entry_2 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_2_v2, conf.BACKBONE_AREA)
        entry_3 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_3_v2, conf.BACKBONE_AREA)
        entry_4 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_4_v2, conf.BACKBONE_AREA)
        entry_5 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_5_v2, conf.BACKBONE_AREA)
        entry_6 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_6_v2, conf.BACKBONE_AREA)
        for data in [[entry_1, self.prefix_1_v2, 'f1/0', self.cost_broadcast_link, ''],
                     [entry_2, self.prefix_2_v2, 'f0/1', self.cost_broadcast_link, ''],
                     [entry_3, self.prefix_3_v2, 'f0/0', self.cost_broadcast_link, ''],
                     [entry_4, self.prefix_4_v2, 'f0/0', 2 * self.cost_broadcast_link, self.r2_f0_1_v2],
                     [entry_5, self.prefix_5_v2, 'f0/0', 2 * self.cost_broadcast_link, self.r2_f0_1_v2],
                     [entry_6, self.prefix_6_v2, 's2/0', self.cost_point_point_link, '']]:
            self.assertIsNotNone(data[0])
            self.assertEqual(conf.DESTINATION_TYPE_NETWORK, data[0].destination_type)
            self.assertEqual(data[1], data[0].destination_id)
            self.assertEqual(utils.Utils.get_prefix_length_from_prefix(self.network_mask), data[0].prefix_length)
            self.assertEqual(conf.OPTIONS, data[0].options)
            self.assertEqual(conf.BACKBONE_AREA, data[0].area)
            self.assertEqual(1, len(data[0].paths))
            path = data[0].get_path(data[2], data[4], '')
            self.assertIsNotNone(path)
            self.assertEqual(conf.INTRA_AREA_PATH, path.path_type)
            self.assertEqual(data[3], path.cost)
            self.assertEqual(0, path.type_2_cost)
            self.assertEqual(data[2], path.outgoing_interface)
            self.assertEqual(data[4], path.next_hop_address)
            self.assertEqual('', path.advertising_router)

        directed_graph, prefixes = self.get_directed_graph_prefixes_full_network(conf.VERSION_IPV6)
        shortest_path_tree_dictionary = {conf.BACKBONE_AREA: self.lsdb_v3.get_shortest_path_tree(
            directed_graph, self.router_id_1)}
        prefixes_dictionary = {conf.BACKBONE_AREA: prefixes}
        table = router_v3.get_intra_area_routing_table(shortest_path_tree_dictionary, prefixes_dictionary)
        self.assertEqual(6, len(table.entries))
        entry_1 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_1_v3, conf.BACKBONE_AREA)
        entry_2 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_2_v3, conf.BACKBONE_AREA)
        entry_3 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_3_v3, conf.BACKBONE_AREA)
        entry_4 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_4_v3, conf.BACKBONE_AREA)
        entry_5 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_5_v3, conf.BACKBONE_AREA)
        entry_6 = table.get_entry(conf.DESTINATION_TYPE_NETWORK, self.prefix_6_v3, conf.BACKBONE_AREA)
        for data in [[entry_1, self.prefix_1_v3, 'f1/0', self.cost_broadcast_link, ''],
                     [entry_2, self.prefix_2_v3, 'f0/1', self.cost_broadcast_link, ''],
                     [entry_3, self.prefix_3_v3, 'f0/0', self.cost_broadcast_link, ''],
                     [entry_4, self.prefix_4_v3, 'f0/0', 2 * self.cost_broadcast_link, self.r2_f0_1_local],
                     [entry_5, self.prefix_5_v3, 'f0/0', 2 * self.cost_broadcast_link, self.r2_f0_1_local],
                     [entry_6, self.prefix_6_v3, 's2/0', self.cost_point_point_link, '']]:
            self.assertIsNotNone(data[0])
            self.assertEqual(conf.DESTINATION_TYPE_NETWORK, data[0].destination_type)
            self.assertEqual(data[1], data[0].destination_id)
            self.assertEqual(self.prefix_length, data[0].prefix_length)
            self.assertEqual(conf.OPTIONS, data[0].options)
            self.assertEqual(conf.BACKBONE_AREA, data[0].area)
            self.assertEqual(1, len(data[0].paths))
            path = data[0].get_path(data[2], data[4], '')
            self.assertIsNotNone(path)
            self.assertEqual(conf.INTRA_AREA_PATH, path.path_type)
            self.assertEqual(data[3], path.cost)
            self.assertEqual(0, path.type_2_cost)
            self.assertEqual(data[2], path.outgoing_interface)
            self.assertEqual(data[4], path.next_hop_address)
            self.assertEqual('', path.advertising_router)

        self.lsdb_v2.clean_lsdb(self.interfaces_r1_v2)
        self.lsdb_v3.clean_lsdb(self.interfaces_r1_v3)

    #  Successful run - 42 s
    def test_update_kernel_routing_table(self):
        # Setup
        kernel_table.KernelTable.delete_all_ospf_routes(0)
        shutdown_event_v2 = threading.Event()
        shutdown_event_v3 = threading.Event()
        router_v2 = router.Router(conf.ROUTER_ID, conf.VERSION_IPV4, shutdown_event_v2, conf.INTERFACE_NAMES,
                                       conf.INTERFACE_AREAS, False)
        router_v3 = router.Router(conf.ROUTER_ID, conf.VERSION_IPV6, shutdown_event_v3, conf.INTERFACE_NAMES,
                                       conf.INTERFACE_AREAS, False)
        thread_v2 = threading.Thread(target=router_v2.main_loop)
        thread_v3 = threading.Thread(target=router_v3.main_loop)
        thread_v2.start()
        thread_v3.start()
        existing_routes = len(kernel_table.KernelTable.get_all_routes())  # Includes 222.222.1.0 and 2001:db8:cafe:1::

        time.sleep(40)
        network_prefixes = 10  # 222.222.2.0 to 222.222.6.0 and 2001:db8:cafe:2:: to 2001:db8:cafe:6::
        self.assertEqual(network_prefixes, len(kernel_table.KernelTable.get_all_ospf_routes()))
        self.assertEqual(existing_routes + network_prefixes, len(kernel_table.KernelTable.get_all_routes()))

        # Tear down
        shutdown_event_v2.set()
        shutdown_event_v3.set()
        thread_v2.join()
        thread_v3.join()
        self.assertEqual(0, len(kernel_table.KernelTable.get_all_ospf_routes()))
        self.assertEqual(existing_routes, len(kernel_table.KernelTable.get_all_routes()))

    def tearDown(self):
        interface.Interface.ospf_identifier = 1

    #  #  #  #  #  #  #  #
    #  Auxiliary methods  #
    #  #  #  #  #  #  #  #

    #  Returns directed graph and prefixes for full Network 1 considering point of view of router 1.1.1.1
    def get_directed_graph_prefixes_full_network(self, version):
        directed_graph_v2 = {
            self.router_id_1: {self.router_id_3: self.cost_point_point_link, self.r4_e0_v2: self.cost_broadcast_link,
                               self.r2_f0_1_v2: self.cost_broadcast_link},
            self.router_id_2: {self.r2_f0_1_v2: self.cost_broadcast_link, self.r3_f0_0_v2: self.cost_broadcast_link},
            self.router_id_3: {self.router_id_1: self.cost_point_point_link, self.r3_f0_0_v2: self.cost_broadcast_link},
            self.router_id_4: {self.r4_e0_v2: self.cost_broadcast_link},
            self.r4_e0_v2: {self.router_id_1: 0, self.router_id_4: 0},
            self.r2_f0_1_v2: {self.router_id_1: 0, self.router_id_2: 0},
            self.r3_f0_0_v2: {self.router_id_2: 0, self.router_id_3: 0}}
        prefixes_v2 = {self.router_id_1: [self.prefix_2_v2, self.prefix_6_v2], self.router_id_2: [self.prefix_4_v2],
                       self.router_id_3: [self.prefix_6_v2], self.router_id_4: [], self.r4_e0_v2: [self.prefix_1_v2],
                       self.r2_f0_1_v2: [self.prefix_3_v2], self.r3_f0_0_v2: [self.prefix_5_v2]}
        directed_graph_v3 = {self.router_id_1: {self.router_id_3: self.cost_point_point_link,
                                                self.network_1_id_v3: self.cost_broadcast_link,
                                                self.network_3_id_v3: self.cost_broadcast_link},
                             self.router_id_2: {self.network_3_id_v3: self.cost_broadcast_link,
                                                self.network_5_id_v3: self.cost_broadcast_link},
                             self.router_id_3: {self.router_id_1: self.cost_point_point_link,
                                                self.network_5_id_v3: self.cost_broadcast_link},
                             self.router_id_4: {self.network_1_id_v3: self.cost_broadcast_link},
                             self.network_1_id_v3: {self.router_id_1: 0, self.router_id_4: 0},
                             self.network_3_id_v3: {self.router_id_1: 0, self.router_id_2: 0},
                             self.network_5_id_v3: {self.router_id_2: 0, self.router_id_3: 0}}
        prefixes_v3 = {self.router_id_1: [self.prefix_2_v3, self.prefix_6_v3], self.router_id_2: [self.prefix_4_v3],
                       self.router_id_3: [self.prefix_6_v3], self.router_id_4: [],
                       self.network_1_id_v3: [self.prefix_1_v3], self.network_3_id_v3: [self.prefix_3_v3],
                       self.network_5_id_v3: [self.prefix_5_v3]}
        if version == conf.VERSION_IPV4:
            return directed_graph_v2, prefixes_v2
        elif version == conf.VERSION_IPV6:
            return directed_graph_v3, prefixes_v3
        else:
            raise ValueError("Invalid OSPF version")

    #  Sets LSDB for both OSPF versions considering router 1.1.1.1 as sole router in network
    def set_lsdb_router_1_1_1_1(self, interfaces_v2, interfaces_v3):
        self.lsdb_v2.clean_lsdb(interfaces_v2)
        self.lsdb_v3.clean_lsdb(interfaces_v3)
        self.delete_lsa_content()

        for data in [[self.prefix_1_v2, self.cost_broadcast_link], [self.prefix_2_v2, self.cost_broadcast_link],
                     [self.prefix_3_v2, self.cost_broadcast_link], [self.prefix_6_v2, self.cost_point_point_link]]:
            self.router_lsa_1_v2.add_link_info_v2(
                data[0], self.network_mask, conf.LINK_TO_STUB_NETWORK, conf.DEFAULT_TOS, data[1])
        self.lsdb_v2.router_lsa_list.append(self.router_lsa_1_v2)

        self.lsdb_v3.router_lsa_list.append(self.router_lsa_1_v3)
        for data in [[self.prefix_1_v3, self.cost_broadcast_link], [self.prefix_2_v3, self.cost_broadcast_link],
                     [self.prefix_3_v3, self.cost_broadcast_link], [self.prefix_6_v3, self.cost_point_point_link]]:
            self.intra_area_prefix_lsa_r1.add_prefix_info(
                self.prefix_length, self.prefix_options, data[1], data[0], conf.LSA_TYPE_INTRA_AREA_PREFIX)
        self.lsdb_v3.intra_area_prefix_lsa_list.append(self.intra_area_prefix_lsa_r1)
        for data in [[self.prefix_1_v3, self.cost_broadcast_link, self.link_lsa_r1_1, self.interface_r1_f1_0_v3],
                     [self.prefix_2_v3, self.cost_broadcast_link, self.link_lsa_r1_2, self.interface_r1_f0_1_v3],
                     [self.prefix_3_v3, self.cost_broadcast_link, self.link_lsa_r1_3, self.interface_r1_f0_0_v3],
                     [self.prefix_6_v3, self.cost_point_point_link, self.link_lsa_r1_6, self.interface_r1_s2_0_v3]]:
            data[2].add_prefix_info(self.prefix_length, self.prefix_options, data[1], data[0], conf.LSA_TYPE_LINK)
            data[3].link_local_lsa_list.append(data[2])

    #  Sets LSDB for both OSPF versions considering entire Network 1 and point of view of router 1.1.1.1
    def set_lsdb_full_network(self, interfaces_v2, interfaces_v3):
        self.lsdb_v2.clean_lsdb(interfaces_v2)
        self.lsdb_v3.clean_lsdb(interfaces_v3)
        self.delete_lsa_content()

        for data in [[self.r4_e0_v2, self.r1_f1_0_v2, self.cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK,
                      self.router_lsa_1_v2],
                     [self.prefix_2_v2, self.network_mask, self.cost_broadcast_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_1_v2],
                     [self.r2_f0_1_v2, self.r1_f0_0_v2, self.cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK,
                      self.router_lsa_1_v2],
                     [self.prefix_6_v2, self.network_mask, self.cost_point_point_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_1_v2],
                     [self.router_id_3, self.r1_s2_0_v2, self.cost_point_point_link, conf.POINT_TO_POINT_LINK,
                      self.router_lsa_1_v2],
                     [self.r2_f0_1_v2, self.r2_f0_1_v2, self.cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK,
                      self.router_lsa_2_v2],
                     [self.prefix_4_v2, self.network_mask, self.cost_broadcast_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_2_v2],
                     [self.r3_f0_0_v2, self.r2_f1_0_v2, self.cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK,
                      self.router_lsa_2_v2],
                     [self.r3_f0_0_v2, self.r3_f0_0_v2, self.cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK,
                      self.router_lsa_3_v2],
                     [self.prefix_6_v2, self.network_mask, self.cost_point_point_link, conf.LINK_TO_STUB_NETWORK,
                      self.router_lsa_3_v2],
                     [self.router_id_1, self.r3_s1_0_v2, self.cost_point_point_link, conf.POINT_TO_POINT_LINK,
                      self.router_lsa_3_v2],
                     [self.r4_e0_v2, self.r4_e0_v2, self.cost_broadcast_link, conf.LINK_TO_TRANSIT_NETWORK,
                      self.router_lsa_4_v2]]:
            router_lsa = data[4]
            router_lsa.add_link_info_v2(data[0], data[1], data[3], conf.DEFAULT_TOS, data[2])
        for router_lsa in [self.router_lsa_1_v2, self.router_lsa_2_v2, self.router_lsa_3_v2, self.router_lsa_4_v2]:
            self.lsdb_v2.router_lsa_list.append(router_lsa)
        for data in [[self.network_lsa_1_v2, [self.router_id_1, self.router_id_4]],
                     [self.network_lsa_3_v2, [self.router_id_1, self.router_id_2]],
                     [self.network_lsa_5_v2, [self.router_id_2, self.router_id_3]]]:
            network_lsa = data[0]
            network_lsa.body.attached_routers = data[1]
            self.lsdb_v2.network_lsa_list.append(network_lsa)

        for data in [[self.router_lsa_1_v3, conf.LINK_TO_TRANSIT_NETWORK, self.cost_broadcast_link, self.r1_f1_0_id,
                      self.r4_e0_id, self.router_id_4],
                     [self.router_lsa_1_v3, conf.POINT_TO_POINT_LINK, self.cost_point_point_link, self.r1_s2_0_id,
                      self.r3_s1_0_id, self.router_id_3],
                     [self.router_lsa_1_v3, conf.LINK_TO_TRANSIT_NETWORK, self.cost_broadcast_link, self.r1_f0_0_id,
                      self.r2_f0_1_id, self.router_id_2],
                     [self.router_lsa_2_v3, conf.LINK_TO_TRANSIT_NETWORK, self.cost_broadcast_link, self.r2_f0_1_id,
                      self.r2_f0_1_id, self.router_id_2],
                     [self.router_lsa_2_v3, conf.LINK_TO_TRANSIT_NETWORK, self.cost_broadcast_link, self.r2_f1_0_id,
                      self.r3_f0_0_id, self.router_id_3],
                     [self.router_lsa_3_v3, conf.POINT_TO_POINT_LINK, self.cost_point_point_link, self.r3_s1_0_id,
                      self.r1_s2_0_id, self.router_id_1],
                     [self.router_lsa_3_v3, conf.LINK_TO_TRANSIT_NETWORK, self.cost_broadcast_link, self.r3_f0_0_id,
                      self.r3_f0_0_id, self.router_id_3],
                     [self.router_lsa_4_v3, conf.LINK_TO_TRANSIT_NETWORK, self.cost_broadcast_link, self.r4_e0_id,
                      self.r4_e0_id, self.router_id_4]]:
            data[0].add_link_info_v3(data[1], data[2], data[3], data[4], data[5])
        for router_lsa in [self.router_lsa_1_v3, self.router_lsa_2_v3, self.router_lsa_3_v3, self.router_lsa_4_v3]:
            self.lsdb_v3.router_lsa_list.append(router_lsa)
        for data in [[self.network_lsa_1_v3, [self.router_id_1, self.router_id_4]],
                     [self.network_lsa_3_v3, [self.router_id_1, self.router_id_2]],
                     [self.network_lsa_5_v3, [self.router_id_2, self.router_id_3]]]:
            data[0].body.attached_routers = data[1]
        for network_lsa in [self.network_lsa_1_v3, self.network_lsa_3_v3, self.network_lsa_5_v3]:
            self.lsdb_v3.network_lsa_list.append(network_lsa)
        for intra_area_prefix_lsa in [
                self.intra_area_prefix_lsa_r1, self.intra_area_prefix_lsa_r2, self.intra_area_prefix_lsa_r3,
                self.intra_area_prefix_lsa_r4, self.intra_area_prefix_lsa_n1, self.intra_area_prefix_lsa_n3,
                self.intra_area_prefix_lsa_n5]:
            intra_area_prefix_lsa.body.prefixes = []
        for data in [[self.intra_area_prefix_lsa_r1, self.prefix_2_v3, self.cost_broadcast_link],
                     [self.intra_area_prefix_lsa_r1, self.prefix_6_v3, self.cost_point_point_link],
                     [self.intra_area_prefix_lsa_r2, self.prefix_4_v3, self.cost_broadcast_link],
                     [self.intra_area_prefix_lsa_r3, self.prefix_6_v3, self.cost_point_point_link],
                     [self.intra_area_prefix_lsa_n1, self.prefix_1_v3, self.cost_broadcast_link],
                     [self.intra_area_prefix_lsa_n3, self.prefix_3_v3, self.cost_broadcast_link],
                     [self.intra_area_prefix_lsa_n5, self.prefix_5_v3, self.cost_broadcast_link]]:
            data[0].add_prefix_info(self.prefix_length, 0, data[2], data[1], conf.LSA_TYPE_INTRA_AREA_PREFIX)
        #  No Intra-Area-Prefix-LSA is added for Router 4 as it has no point-to-point or stub links
        for intra_area_prefix_lsa in [
                self.intra_area_prefix_lsa_r1, self.intra_area_prefix_lsa_r2, self.intra_area_prefix_lsa_r3,
                self.intra_area_prefix_lsa_n1, self.intra_area_prefix_lsa_n3, self.intra_area_prefix_lsa_n5]:
            self.lsdb_v3.intra_area_prefix_lsa_list.append(intra_area_prefix_lsa)
        for link_lsa in [self.link_lsa_r1_1, self.link_lsa_r1_2, self.link_lsa_r1_3, self.link_lsa_r1_6,
                         self.link_lsa_r2_3, self.link_lsa_r3_6, self.link_lsa_r4_1]:
            link_lsa.body.prefixes = []
        for data in [[self.link_lsa_r1_1, self.prefix_1_v3],
                     [self.link_lsa_r1_2, self.prefix_2_v3],
                     [self.link_lsa_r1_3, self.prefix_3_v3],
                     [self.link_lsa_r1_6, self.prefix_6_v3],
                     [self.link_lsa_r2_3, self.prefix_3_v3],
                     [self.link_lsa_r3_6, self.prefix_6_v3],
                     [self.link_lsa_r4_1, self.prefix_1_v3]]:
            data[0].add_prefix_info(self.prefix_length, 0, 0, data[1], conf.LSA_TYPE_LINK)
        for link_lsa in [[self.link_lsa_r1_1, self.interface_r1_f1_0_v3],
                         [self.link_lsa_r1_2, self.interface_r1_f0_1_v3],
                         [self.link_lsa_r1_3, self.interface_r1_f0_0_v3],
                         [self.link_lsa_r1_6, self.interface_r1_s2_0_v3],
                         [self.link_lsa_r2_3, self.interface_r1_f0_0_v3],
                         [self.link_lsa_r3_6, self.interface_r1_s2_0_v3],
                         [self.link_lsa_r4_1, self.interface_r1_f1_0_v3]]:  # Point of view of Router 1
            link_lsa[1].link_local_lsa_list.append(link_lsa[0])

    #  Deletes link, attached router and prefix information respectively from all LSAs in the LSDB
    def delete_lsa_content(self):
        for router_lsa in [self.router_lsa_1_v2, self.router_lsa_2_v2, self.router_lsa_3_v2, self.router_lsa_4_v2,
                           self.router_lsa_1_v3, self.router_lsa_2_v3, self.router_lsa_3_v3, self.router_lsa_4_v3]:
            router_lsa.body.link_number = 0
            router_lsa.body.links = []
        for network_lsa in [self.network_lsa_1_v2, self.network_lsa_3_v2, self.network_lsa_5_v2, self.network_lsa_1_v3,
                            self.network_lsa_3_v3, self.network_lsa_5_v3]:
            network_lsa.body.attached_routers = []
        for intra_area_prefix_lsa in [
                self.intra_area_prefix_lsa_r1, self.intra_area_prefix_lsa_r2, self.intra_area_prefix_lsa_r3,
                self.intra_area_prefix_lsa_r4, self.intra_area_prefix_lsa_n1, self.intra_area_prefix_lsa_n3,
                self.intra_area_prefix_lsa_n5]:
            intra_area_prefix_lsa.body.prefix_number = 0
            intra_area_prefix_lsa.body.prefixes = []
        for link_lsa in [self.link_lsa_r1_1, self.link_lsa_r1_2, self.link_lsa_r1_3, self.link_lsa_r1_6,
                         self.link_lsa_r2_3, self.link_lsa_r3_6, self.link_lsa_r4_1]:
            link_lsa.body.prefix_number = 0
            link_lsa.body.prefixes = []
