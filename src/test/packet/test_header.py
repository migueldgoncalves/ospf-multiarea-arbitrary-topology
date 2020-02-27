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
    header = None

    def setUp(self):
        self.packet_type = conf.PACKET_TYPE_HELLO
        self.router_id = conf.ROUTER_ID
        self.area_id = conf.BACKBONE_AREA
        self.auth_type = conf.NULL_AUTHENTICATION
        self.authentication = conf.DEFAULT_AUTH
        self.header = header.Header(self.packet_type, self.router_id, self.area_id, self.auth_type,
                                    self.authentication)

    #  Successful run - Instant
    def test_header_constructor_successful(self):
        self.assertEqual(conf.VERSION_IPV4, self.header.version)
        self.assertEqual(self.packet_type, self.header.packet_type)
        self.assertEqual(0, self.header.length)
        self.assertEqual(self.router_id, self.header.router_id)
        self.assertEqual(self.area_id, self.header.area_id)
        self.assertEqual(0, self.header.checksum)
        self.assertEqual(self.auth_type, self.header.auth_type)
        self.assertEqual(self.authentication, self.header.authentication)

    #  Successful run - Instant
    def test_header_constructor_invalid_parameters(self):
        invalid_packet_type = -1
        with self.assertRaises(ValueError):
            header.Header(invalid_packet_type, self.router_id, self.area_id, self.auth_type, self.authentication)
        invalid_router_id = ''
        with self.assertRaises(ValueError):
            header.Header(self.packet_type, invalid_router_id, self.area_id, self.auth_type, self.authentication)
        invalid_area_id = ''
        with self.assertRaises(ValueError):
            header.Header(self.packet_type, self.router_id, invalid_area_id, self.auth_type, self.authentication)
        invalid_auth_type = -1
        with self.assertRaises(ValueError):
            header.Header(self.packet_type, self.router_id, self.area_id, invalid_auth_type, self.authentication)
        invalid_authentication = -1
        with self.assertRaises(ValueError):
            header.Header(self.packet_type, self.router_id, self.area_id, self.auth_type, invalid_authentication)

    #  Successful run - Instant
    def test_pack_header(self):
        new_header = b'\x02\x01\x00\x00\x04\x04\x04\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.assertEqual(new_header, self.header.pack_header())

    #  Successful run - Instant
    def test_prepare_packet_checksum(self):
        new_checksum = 1
        new_auth_type = 1
        new_authentication = 1
        self.header.checksum = new_checksum
        self.header.auth_type = new_auth_type
        self.header.authentication = new_authentication
        self.assertEqual(new_checksum, self.header.checksum)
        self.assertEqual(new_auth_type, self.header.auth_type)
        self.assertEqual(new_authentication, self.header.authentication)

        self.header.prepare_packet_checksum()
        self.assertEqual(0, self.header.checksum)
        self.assertEqual(0, self.header.auth_type)
        self.assertEqual(0, self.header.authentication)

    #  Successful run - Instant
    def test_parameter_validation_successful(self):
        #  Correct packet type
        self.assertTrue(self.header.parameter_validation(conf.PACKET_TYPE_HELLO, self.router_id, self.area_id,
                                                         self.auth_type, self.authentication))
        self.assertTrue(self.header.parameter_validation(conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id,
                                                         self.auth_type, self.authentication))
        self.assertTrue(self.header.parameter_validation(conf.PACKET_TYPE_LS_REQUEST, self.router_id, self.area_id,
                                                         self.auth_type, self.authentication))
        self.assertTrue(self.header.parameter_validation(conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id,
                                                         self.auth_type, self.authentication))
        self.assertTrue(self.header.parameter_validation(conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id,
                                                         self.area_id, self.auth_type, self.authentication))

        #  Correct router ID
        self.assertTrue(self.header.parameter_validation(self.packet_type, '0.0.0.0', self.area_id, self.auth_type,
                                                         self.authentication))
        self.assertTrue(self.header.parameter_validation(self.packet_type, '255.255.255.255', self.area_id,
                                                         self.auth_type, self.authentication))

        #  Correct area ID
        self.assertTrue(self.header.parameter_validation(self.packet_type, self.router_id, '0.0.0.0', self.auth_type,
                                                         self.authentication))
        self.assertTrue(self.header.parameter_validation(self.packet_type, self.router_id, '255.255.255.255',
                                                         self.auth_type, self.authentication))

        #  Correct authentication type
        self.assertTrue(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                         conf.NULL_AUTHENTICATION, self.authentication))
        self.assertTrue(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                         conf.SIMPLE_PASSWORD, self.authentication))
        self.assertTrue(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                         conf.CRYPTOGRAPHIC_AUTHENTICATION, self.authentication))

        #  Correct authentication field
        self.assertTrue(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id, self.auth_type,
                                                         0))
        self.assertTrue(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id, self.auth_type,
                                                         conf.MAX_VALUE_64_BITS))

    #  Successful run - Instant
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid packet type
        self.assertEqual(self.header.parameter_validation(conf.PACKET_TYPE_HELLO - 1, self.router_id, self.area_id,
                                                          self.auth_type, self.authentication),
                         (False, "Invalid packet type"))
        self.assertEqual(self.header.parameter_validation(conf.PACKET_TYPE_LS_ACKNOWLEDGMENT + 1, self.router_id,
                                                          self.area_id, self.auth_type, self.authentication),
                         (False, "Invalid packet type"))
        self.assertEqual(self.header.parameter_validation('Invalid parameter', self.router_id, self.area_id,
                                                          self.auth_type, self.authentication),
                         (False, "Invalid packet type"))

        #  Incorrect router ID
        self.assertEqual(self.header.parameter_validation(self.packet_type, '', self.area_id, self.auth_type,
                                                          self.authentication),
                         (False, "Invalid router ID"))

        #  Incorrect area ID
        self.assertEqual(self.header.parameter_validation(self.packet_type, self.router_id, '', self.auth_type,
                                                          self.authentication),
                         (False, "Invalid area ID"))

        #  Incorrect authentication type
        self.assertEqual(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                          conf.NULL_AUTHENTICATION - 1, self.authentication),
                         (False, "Invalid authentication type"))
        self.assertEqual(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                          conf.CRYPTOGRAPHIC_AUTHENTICATION + 1, self.authentication),
                         (False, "Invalid authentication type"))
        self.assertEqual(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                          'Invalid parameter', self.authentication),
                         (False, "Invalid authentication type"))

        #  Incorrect authentication field
        self.assertEqual(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                          self.auth_type, -1),
                         (False, "Invalid authentication field"))
        self.assertEqual(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                          self.auth_type, conf.MAX_VALUE_64_BITS + 1),
                         (False, "Invalid authentication field"))
        self.assertEqual(self.header.parameter_validation(self.packet_type, self.router_id, self.area_id,
                                                          self.auth_type, 'Invalid parameter'),
                         (False, "Invalid parameter type"))

    #  Successful run - Instant
    def test_set_checksum(self):
        self.header.set_checksum(1)
        self.assertEqual(1, self.header.checksum)

        with self.assertRaises(ValueError):
            self.header.set_checksum(-1)
        with self.assertRaises(ValueError):
            self.header.set_checksum(conf.MAX_VALUE_16_BITS + 1)

        self.assertEqual(1, self.header.checksum)

    #  Successful run - Instant
    def test_set_length(self):
        self.header.set_length(conf.OSPFV2_HEADER_LENGTH)
        self.assertEqual(conf.OSPFV2_HEADER_LENGTH, self.header.length)

        with self.assertRaises(ValueError):
            self.header.set_length(conf.OSPFV2_HEADER_LENGTH - 1)

        self.assertEqual(conf.OSPFV2_HEADER_LENGTH, self.header.length)

    def tearDown(self):
        self.packet_type = 0
        self.router_id = ''
        self.area_id = ''
        self.auth_type = 0
        self.authentication = 0
        self.header = None
