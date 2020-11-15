import unittest

import router.kernel_table as kernel_table
import conf.conf as conf
import general.utils as utils

'''
This class tests the interface to OSPF route management in the Linux kernel default routing table
'''


#  Full successful run - 0-1 s
class TestKernelTable(unittest.TestCase):

    PREFIX_1_V2 = '1.1.1.0'
    PREFIX_2_V2 = '2.2.2.0'
    PREFIX_1_V3 = '1001:db8:cafe:1::'
    PREFIX_2_V3 = '3001:db8:cafe:1::'
    PREFIX_LENGTH_V2 = 24
    PREFIX_LENGTH_V3 = 64
    NEXT_HOP_1_V2 = '222.222.1.10'
    NEXT_HOP_2_V2 = '222.222.1.20'
    NEXT_HOP_1_V3 = 'fe80:db8:cafe:1::10'
    NEXT_HOP_2_V3 = 'fe80:db8:cafe:1::20'
    OUTGOING_INTERFACE = conf.INTERFACE_NAMES[0]
    PREFIX_DATA_1_V2 = [PREFIX_1_V2, PREFIX_LENGTH_V2, NEXT_HOP_1_V2, OUTGOING_INTERFACE]
    PREFIX_DATA_2_V2 = [PREFIX_2_V2, PREFIX_LENGTH_V2, NEXT_HOP_2_V2, OUTGOING_INTERFACE]
    PREFIX_DATA_1_V3 = [PREFIX_1_V3, PREFIX_LENGTH_V3, NEXT_HOP_1_V3, OUTGOING_INTERFACE]
    PREFIX_DATA_2_V3 = [PREFIX_2_V3, PREFIX_LENGTH_V3, NEXT_HOP_2_V3, OUTGOING_INTERFACE]

    def setUp(self):
        kernel_table.KernelTable.delete_all_ospf_routes(0)

    #  Successful run - Instant
    def test_get_directly_connected_prefixes(self):
        self.assertEqual([['222.222.1.0', 24], ['2001:db8:cafe:1::', 64]],
                         kernel_table.KernelTable.get_directly_connected_prefixes(conf.INTERFACE_NAMES))

    #  Successful run - 0-1 s
    def test_route_management(self):
        self.assertEqual(0, len(kernel_table.KernelTable.get_all_ospf_routes()))
        for data in [TestKernelTable.PREFIX_DATA_1_V2, TestKernelTable.PREFIX_DATA_2_V2,
                     TestKernelTable.PREFIX_DATA_1_V3, TestKernelTable.PREFIX_DATA_2_V3]:
            self.assertFalse(kernel_table.KernelTable.has_ospf_route(data[0], data[1], data[2]))
            self.assertIsNone(kernel_table.KernelTable.get_ospf_route(data[0], data[1], data[2]))
        previous_routes = len(kernel_table.KernelTable.get_all_routes())
        self.assertTrue(previous_routes > 0)

        routes_added = 0
        for data in [TestKernelTable.PREFIX_DATA_1_V2, TestKernelTable.PREFIX_DATA_2_V2,
                     TestKernelTable.PREFIX_DATA_1_V3, TestKernelTable.PREFIX_DATA_2_V3]:
            kernel_table.KernelTable.add_ospf_route(data[0], data[1], data[2], data[3], conf.INTERFACE_NAMES)
            routes_added += 1
            self.assertEqual(previous_routes + routes_added, len(kernel_table.KernelTable.get_all_routes()))
            self.assertEqual(routes_added, len(kernel_table.KernelTable.get_all_ospf_routes()))
            self.assertTrue(kernel_table.KernelTable.has_ospf_route(data[0], data[1], data[2]))
            route = kernel_table.KernelTable.get_ospf_route(data[0], data[1], data[2])
            self.assertIsNotNone(route)
            self.assertEqual(kernel_table.KernelTable.get_route_prefix(route), data[0])
            self.assertEqual(kernel_table.KernelTable.get_route_prefix_length(route), data[1])
            self.assertEqual(kernel_table.KernelTable.get_route_next_hop(route), data[2])
            self.assertEqual(kernel_table.KernelTable.get_route_outgoing_interface(route), data[3])
            self.assertEqual(kernel_table.KernelTable.get_route_protocol(route), conf.OSPF_PROTOCOL_NUMBER)

        kernel_table.KernelTable.delete_all_ospf_routes(0)
        self.assertEqual(0, len(kernel_table.KernelTable.get_all_ospf_routes()))
        for data in [TestKernelTable.PREFIX_DATA_1_V2, TestKernelTable.PREFIX_DATA_2_V2,
                     TestKernelTable.PREFIX_DATA_1_V3, TestKernelTable.PREFIX_DATA_2_V3]:
            self.assertFalse(kernel_table.KernelTable.has_ospf_route(data[0], data[1], data[2]))
            self.assertIsNone(kernel_table.KernelTable.get_ospf_route(data[0], data[1], data[2]))
        self.assertEqual(previous_routes, len(kernel_table.KernelTable.get_all_routes()))

    #  Successful run - Instant
    def test_add_connected_prefixes(self):
        prefix_data_v2 = utils.Utils.get_ipv4_prefix_from_interface_name(conf.INTERFACE_NAMES[0])
        prefix_data_v2.append(TestKernelTable.NEXT_HOP_1_V2)
        prefix_data_v2.append(TestKernelTable.OUTGOING_INTERFACE)
        prefix_data_v3 = utils.Utils.get_ipv6_prefix_from_interface_name(conf.INTERFACE_NAMES[0])
        prefix_data_v3.append(TestKernelTable.NEXT_HOP_1_V3)
        prefix_data_v3.append(TestKernelTable.OUTGOING_INTERFACE)
        previous_routes = len(kernel_table.KernelTable.get_all_routes())
        for prefix_data in [prefix_data_v2, prefix_data_v3]:
            prefix = prefix_data[0]
            prefix_length = prefix_data[1]
            next_hop = prefix_data[2]
            outgoing_interface = prefix_data[3]
            kernel_table.KernelTable.add_ospf_route(
                prefix, prefix_length, next_hop, outgoing_interface, conf.INTERFACE_NAMES)
            self.assertEqual(previous_routes, len(kernel_table.KernelTable.get_all_routes()))
            self.assertEqual(0, len(kernel_table.KernelTable.get_all_ospf_routes()))
            self.assertFalse(kernel_table.KernelTable.has_ospf_route(prefix, prefix_length, next_hop))
            self.assertIsNone(kernel_table.KernelTable.get_ospf_route(prefix, prefix_length, next_hop))

    def tearDown(self):
        kernel_table.KernelTable.delete_all_ospf_routes(0)


if __name__ == '__main__':
    unittest.main()
