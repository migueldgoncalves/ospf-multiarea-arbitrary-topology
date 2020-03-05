import unittest

import packet.header as header
import conf.conf as conf

'''
This class tests the OSPF packet header class and its operations
'''


#  Full successful run - Instant
class TestHeader(unittest.TestCase):
    packet_type = 0
    router_id = '0.0.0.0'
    area_id = '0.0.0.0'
    auth_type = 0
    authentication = 0
    instance_id = 0
    header_ospfv2 = None
    header_ospfv3 = None

    def setUp(self):
        self.packet_type = conf.PACKET_TYPE_HELLO
        self.router_id = conf.ROUTER_ID
        self.area_id = conf.BACKBONE_AREA
        self.auth_type = conf.NULL_AUTHENTICATION
        self.authentication = conf.DEFAULT_AUTH
        self.header_ospfv2 = header.Header(conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id,
                                           self.auth_type, self.authentication, self.instance_id)

    #  Successful run - Instant
    def test_header_constructor_successful(self):
        self.assertEqual(conf.VERSION_IPV4, self.header_ospfv2.version)
        self.assertEqual(self.packet_type, self.header_ospfv2.packet_type)
        self.assertEqual(0, self.header_ospfv2.length)
        self.assertEqual(self.router_id, self.header_ospfv2.router_id)
        self.assertEqual(self.area_id, self.header_ospfv2.area_id)
        self.assertEqual(0, self.header_ospfv2.checksum)
        self.assertEqual(self.auth_type, self.header_ospfv2.auth_type)
        self.assertEqual(self.authentication, self.header_ospfv2.authentication)
        self.assertEqual(self.instance_id, self.header_ospfv2.instance_id)

    #  Successful run - Instant
    def test_header_constructor_invalid_parameters(self):
        version = 1
        with self.assertRaises(ValueError):
            header.Header(version, self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication,
                          self.instance_id)
        invalid_packet_type = -1
        with self.assertRaises(ValueError):
            header.Header(conf.VERSION_IPV4, invalid_packet_type, self.router_id, self.area_id, self.auth_type,
                          self.authentication, self.instance_id)
        invalid_router_id = ''
        with self.assertRaises(ValueError):
            header.Header(conf.VERSION_IPV4, self.packet_type, invalid_router_id, self.area_id, self.auth_type,
                          self.authentication, self.instance_id)
        invalid_area_id = ''
        with self.assertRaises(ValueError):
            header.Header(conf.VERSION_IPV4, self.packet_type, self.router_id, invalid_area_id, self.auth_type,
                          self.authentication, self.instance_id)
        invalid_auth_type = -1
        with self.assertRaises(ValueError):
            header.Header(conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, invalid_auth_type,
                          self.authentication, self.instance_id)
        invalid_authentication = -1
        with self.assertRaises(ValueError):
            header.Header(conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type,
                          invalid_authentication, self.instance_id)
        instance_id = -1
        with self.assertRaises(ValueError):
            header.Header(conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type,
                          self.authentication, instance_id)

    #  Successful run - Instant
    def test_pack_header(self):
        new_header = b'\x02\x01\x00\x00\x04\x04\x04\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.assertEqual(new_header, self.header_ospfv2.pack_header())

    #  Successful run - Instant
    def test_prepare_packet_checksum(self):
        new_checksum = 1
        new_auth_type = 1
        new_authentication = 1
        self.header_ospfv2.checksum = new_checksum
        self.header_ospfv2.auth_type = new_auth_type
        self.header_ospfv2.authentication = new_authentication
        self.assertEqual(new_checksum, self.header_ospfv2.checksum)
        self.assertEqual(new_auth_type, self.header_ospfv2.auth_type)
        self.assertEqual(new_authentication, self.header_ospfv2.authentication)

        self.header_ospfv2.prepare_packet_checksum()
        self.assertEqual(0, self.header_ospfv2.checksum)
        self.assertEqual(0, self.header_ospfv2.auth_type)
        self.assertEqual(0, self.header_ospfv2.authentication)

    #  Successful run - Instant
    def test_parameter_validation_successful(self):
        #  Correct OSPF version
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV6, conf.PACKET_TYPE_HELLO, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))

        #  Correct packet type
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_LS_REQUEST, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))

        #  Correct router ID
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, '0.0.0.0', self.area_id, self.auth_type, self.authentication,
            self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, '255.255.255.255', self.area_id, self.auth_type, self.authentication,
            self.instance_id))

        #  Correct area ID
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, '0.0.0.0', self.auth_type, self.authentication,
            self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, '255.255.255.255', self.auth_type, self.authentication,
            self.instance_id))

        #  Correct authentication type
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.NULL_AUTHENTICATION,
            self.authentication, self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.SIMPLE_PASSWORD,
            self.authentication, self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.CRYPTOGRAPHIC_AUTHENTICATION,
            self.authentication, self.instance_id))

        #  Correct authentication field
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, 0, self.instance_id))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, conf.MAX_VALUE_64_BITS,
            self.instance_id))

        #  Correct instance ID
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication, 0))
        self.assertTrue(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication,
            conf.MAX_VALUE_8_BITS))

    #  Successful run - Instant
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid OSPF version
        self.assertEqual(self.header_ospfv2.parameter_validation(
            1, conf.PACKET_TYPE_HELLO - 1, self.router_id, self.area_id, self.auth_type, self.authentication,
            self.instance_id), (False, "Invalid OSPF version"))
        self.assertEqual(self.header_ospfv2.parameter_validation(
            4, conf.PACKET_TYPE_HELLO - 1, self.router_id, self.area_id, self.auth_type, self.authentication,
            self.instance_id), (False, "Invalid OSPF version"))

        #  Invalid packet type
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO - 1, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id), (False, "Invalid packet type"))
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_LS_ACKNOWLEDGMENT + 1, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id), (False, "Invalid packet type"))
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, 'Invalid parameter', self.router_id, self.area_id, self.auth_type, self.authentication,
            self.instance_id), (False, "Invalid packet type"))

        #  Incorrect router ID
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, '', self.area_id, self.auth_type, self.authentication,
            self.instance_id), (False, "Invalid router ID"))

        #  Incorrect area ID
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, '', self.auth_type, self.authentication,
            self.instance_id), (False, "Invalid area ID"))

        #  Incorrect authentication type
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.NULL_AUTHENTICATION - 1,
            self.authentication, self.instance_id), (False, "Invalid authentication type"))
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.CRYPTOGRAPHIC_AUTHENTICATION + 1,
            self.authentication, self.instance_id), (False, "Invalid authentication type"))
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, 'Invalid parameter', self.authentication,
            self.instance_id), (False, "Invalid authentication type"))

        #  Incorrect authentication field
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, -1, self.instance_id),
            (False, "Invalid authentication field"))
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type,
            conf.MAX_VALUE_64_BITS + 1, self.instance_id), (False, "Invalid authentication field"))
        self.assertEqual(self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, 'Invalid parameter',
            self.instance_id), (False, "Invalid parameter type"))

    #  Successful run - Instant
    def test_set_checksum(self):
        self.header_ospfv2.set_checksum(1)
        self.assertEqual(1, self.header_ospfv2.checksum)

        with self.assertRaises(ValueError):
            self.header_ospfv2.set_checksum(-1)
        with self.assertRaises(ValueError):
            self.header_ospfv2.set_checksum(conf.MAX_VALUE_16_BITS + 1)

        self.assertEqual(1, self.header_ospfv2.checksum)

    #  Successful run - Instant
    def test_set_length(self):
        self.header_ospfv2.set_length(conf.OSPFV2_HEADER_LENGTH)
        self.assertEqual(conf.OSPFV2_HEADER_LENGTH, self.header_ospfv2.length)

        with self.assertRaises(ValueError):
            self.header_ospfv2.set_length(conf.OSPFV2_HEADER_LENGTH - 1)

        self.assertEqual(conf.OSPFV2_HEADER_LENGTH, self.header_ospfv2.length)

    def tearDown(self):
        self.packet_type = 0
        self.router_id = ''
        self.area_id = ''
        self.auth_type = 0
        self.authentication = 0
        self.header_ospfv2 = None
