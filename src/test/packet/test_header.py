import unittest

import packet.header as header
import conf.conf as conf

'''
This class tests the OSPF packet header class and its operations
'''


#  Full successful run - Instant
class TestHeader(unittest.TestCase):

    def setUp(self):
        self.packet_type = conf.PACKET_TYPE_HELLO
        self.router_id = '1.1.1.1'
        self.area_id = '2.2.2.2'
        self.auth_type = 1
        self.authentication = 2
        self.instance_id = 3
        self.header_ospfv2 = header.Header(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication, 0)
        self.header_ospfv3 = header.Header(
            conf.VERSION_IPV6, self.packet_type, self.router_id, self.area_id, 0, 0, self.instance_id)

    #  Successful run - Instant
    def test_header_constructor_v2_successful(self):
        self.assertEqual(conf.VERSION_IPV4, self.header_ospfv2.version)
        self.assertEqual(self.packet_type, self.header_ospfv2.packet_type)
        self.assertEqual(0, self.header_ospfv2.length)
        self.assertEqual(self.router_id, self.header_ospfv2.router_id)
        self.assertEqual(self.area_id, self.header_ospfv2.area_id)
        self.assertEqual(0, self.header_ospfv2.checksum)
        self.assertEqual(self.auth_type, self.header_ospfv2.auth_type)
        self.assertEqual(self.authentication, self.header_ospfv2.authentication)

    #  Successful run - Instant
    def test_header_constructor_v3_successful(self):
        self.assertEqual(conf.VERSION_IPV6, self.header_ospfv3.version)
        self.assertEqual(self.packet_type, self.header_ospfv3.packet_type)
        self.assertEqual(0, self.header_ospfv3.length)
        self.assertEqual(self.router_id, self.header_ospfv3.router_id)
        self.assertEqual(self.area_id, self.header_ospfv3.area_id)
        self.assertEqual(0, self.header_ospfv3.checksum)
        self.assertEqual(self.instance_id, self.header_ospfv3.instance_id)

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
            header.Header(conf.VERSION_IPV6, self.packet_type, self.router_id, self.area_id, self.auth_type,
                          self.authentication, instance_id)

    #  Successful run - Instant
    def test_pack_header(self):
        header_bytes = b'\x02\x01\x00\x00\x01\x01\x01\x01\x02\x02\x02\x02\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00' \
                       b'\x02'
        self.assertEqual(header_bytes, self.header_ospfv2.pack_header())
        self.header_ospfv2.length = 10
        self.header_ospfv2.checksum = 20
        header_bytes = b'\x02\x01\x00\n\x01\x01\x01\x01\x02\x02\x02\x02\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02'
        self.assertEqual(header_bytes, self.header_ospfv2.pack_header())

        header_bytes = b'\x03\x01\x00\x00\x01\x01\x01\x01\x02\x02\x02\x02\x00\x00\x03\x00'
        self.assertEqual(header_bytes, self.header_ospfv3.pack_header())
        self.header_ospfv3.length = 30
        self.header_ospfv3.checksum = 40
        header_bytes = b'\x03\x01\x00\x1e\x01\x01\x01\x01\x02\x02\x02\x02\x00\x28\x03\x00'
        self.assertEqual(header_bytes, self.header_ospfv3.pack_header())

    #  Successful run - Instant
    def test_unpack_header(self):
        header_bytes = b'\x02\x01\x00\x18\x01\x01\x01\x01\x02\x02\x02\x02\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00' \
                       b'\x02'
        unpacked_header = header.Header.unpack_header(header_bytes, conf.VERSION_IPV4)
        self.assertEqual(conf.VERSION_IPV4, unpacked_header.version)
        self.assertEqual(self.packet_type, unpacked_header.packet_type)
        self.assertEqual(24, unpacked_header.length)
        self.assertEqual(self.router_id, unpacked_header.router_id)
        self.assertEqual(self.area_id, unpacked_header.area_id)
        self.assertEqual(20, unpacked_header.checksum)
        self.assertEqual(self.auth_type, unpacked_header.auth_type)
        self.assertEqual(self.authentication, unpacked_header.authentication)

        header_bytes = b'\x03\x01\x00\x1e\x01\x01\x01\x01\x02\x02\x02\x02\x00\x28\x03\x00'
        unpacked_header = header.Header.unpack_header(header_bytes, conf.VERSION_IPV6)
        self.assertEqual(conf.VERSION_IPV6, unpacked_header.version)
        self.assertEqual(self.packet_type, unpacked_header.packet_type)
        self.assertEqual(30, unpacked_header.length)
        self.assertEqual(self.router_id, unpacked_header.router_id)
        self.assertEqual(self.area_id, unpacked_header.area_id)
        self.assertEqual(40, unpacked_header.checksum)
        self.assertEqual(self.instance_id, unpacked_header.instance_id)

    #  Successful run - Instant
    def test_prepare_packet_checksum(self):
        new_checksum = 10
        new_auth_type = 10
        new_authentication = 10

        self.header_ospfv2.checksum = new_checksum
        self.header_ospfv2.auth_type = new_auth_type
        self.header_ospfv2.authentication = new_authentication
        self.assertEqual(new_checksum, self.header_ospfv2.checksum)
        self.assertEqual(new_auth_type, self.header_ospfv2.auth_type)
        self.assertEqual(new_authentication, self.header_ospfv2.authentication)
        cleaned_parameters = self.header_ospfv2.prepare_packet_checksum()
        self.assertEqual(0, self.header_ospfv2.checksum)
        self.assertEqual(0, self.header_ospfv2.auth_type)
        self.assertEqual(0, self.header_ospfv2.authentication)
        self.assertEqual([new_auth_type, new_authentication], cleaned_parameters)

        self.header_ospfv3.checksum = new_checksum
        self.header_ospfv3.auth_type = new_auth_type
        self.header_ospfv3.authentication = new_authentication
        self.assertEqual(new_checksum, self.header_ospfv3.checksum)
        self.assertEqual(new_auth_type, self.header_ospfv3.auth_type)
        self.assertEqual(new_authentication, self.header_ospfv3.authentication)
        cleaned_parameters = self.header_ospfv3.prepare_packet_checksum()
        self.assertEqual(0, self.header_ospfv3.checksum)
        self.assertEqual(0, self.header_ospfv3.auth_type)
        self.assertEqual(0, self.header_ospfv3.authentication)
        self.assertEqual([new_auth_type, new_authentication], cleaned_parameters)

    #  Successful run - Instant
    def test_finish_packet_checksum(self):
        new_checksum = 10
        new_auth_type = 10
        new_authentication = 10

        self.header_ospfv2.checksum = new_checksum
        self.header_ospfv2.auth_type = new_auth_type
        self.header_ospfv2.authentication = new_authentication
        cleaned_parameters = self.header_ospfv2.prepare_packet_checksum()
        self.header_ospfv2.finish_packet_checksum(cleaned_parameters)
        self.assertEqual(0, self.header_ospfv2.checksum)
        self.assertEqual(new_auth_type, self.header_ospfv2.auth_type)
        self.assertEqual(new_authentication, self.header_ospfv2.authentication)

        self.header_ospfv3.checksum = new_checksum
        self.header_ospfv3.auth_type = new_auth_type
        self.header_ospfv3.authentication = new_authentication
        cleaned_parameters = self.header_ospfv3.prepare_packet_checksum()
        self.header_ospfv3.finish_packet_checksum(cleaned_parameters)
        self.assertEqual(0, self.header_ospfv3.checksum)
        self.assertEqual(new_auth_type, self.header_ospfv3.auth_type)
        self.assertEqual(new_authentication, self.header_ospfv3.authentication)

    #  Successful run - Instant
    def test_parameter_validation_successful(self):
        #  Correct OSPF version
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV6, conf.PACKET_TYPE_HELLO, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))

        #  Correct packet type
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_DB_DESCRIPTION, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_LS_REQUEST, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_LS_UPDATE, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_LS_ACKNOWLEDGMENT, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))

        #  Correct router ID
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, '0.0.0.0', self.area_id, self.auth_type, self.authentication,
            self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, '255.255.255.255', self.area_id, self.auth_type, self.authentication,
            self.instance_id))

        #  Correct area ID
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, '0.0.0.0', self.auth_type, self.authentication,
            self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, '255.255.255.255', self.auth_type, self.authentication,
            self.instance_id))

        #  Correct authentication type
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.NULL_AUTHENTICATION,
            self.authentication, self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.SIMPLE_PASSWORD,
            self.authentication, self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.CRYPTOGRAPHIC_AUTHENTICATION,
            self.authentication, self.instance_id))

        #  Correct authentication field
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, 0, self.instance_id))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, conf.MAX_VALUE_64_BITS,
            self.instance_id))

        #  Correct instance ID
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV6, self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication, 0))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV6, self.packet_type, self.router_id, self.area_id, self.auth_type, self.authentication,
            conf.MAX_VALUE_8_BITS))

    #  Successful run - Instant
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid OSPF version
        self.assertEqual((False, "Invalid OSPF version"), self.header_ospfv2.parameter_validation(
            1, conf.PACKET_TYPE_HELLO - 1, self.router_id, self.area_id, self.auth_type, self.authentication,
            self.instance_id))
        self.assertEqual((False, "Invalid OSPF version"), self.header_ospfv2.parameter_validation(
            4, conf.PACKET_TYPE_HELLO - 1, self.router_id, self.area_id, self.auth_type, self.authentication,
            self.instance_id))

        #  Invalid packet type
        self.assertEqual((False, "Invalid packet type"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO - 1, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertEqual((False, "Invalid packet type"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, conf.PACKET_TYPE_LS_ACKNOWLEDGMENT + 1, self.router_id, self.area_id, self.auth_type,
            self.authentication, self.instance_id))
        self.assertEqual((False, "Invalid packet type"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, 'Invalid parameter', self.router_id, self.area_id, self.auth_type, self.authentication,
            self.instance_id))

        #  Incorrect router ID
        self.assertEqual((False, "Invalid router ID"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, '', self.area_id, self.auth_type, self.authentication,
            self.instance_id))

        #  Incorrect area ID
        self.assertEqual((False, "Invalid area ID"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, '', self.auth_type, self.authentication,
            self.instance_id))

        #  Incorrect authentication type
        self.assertEqual((False, "Invalid authentication type"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.NULL_AUTHENTICATION - 1,
            self.authentication, self.instance_id))
        self.assertEqual((False, "Invalid authentication type"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, conf.CRYPTOGRAPHIC_AUTHENTICATION + 1,
            self.authentication, self.instance_id))
        self.assertEqual((False, "Invalid authentication type"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, 'Invalid parameter', self.authentication,
            self.instance_id))

        #  Incorrect authentication field
        self.assertEqual((False, "Invalid authentication field"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, -1, self.instance_id))
        self.assertEqual((False, "Invalid authentication field"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type,
            conf.MAX_VALUE_64_BITS + 1, self.instance_id))
        self.assertEqual((False, "Invalid parameter type"), self.header_ospfv2.parameter_validation(
            conf.VERSION_IPV4, self.packet_type, self.router_id, self.area_id, self.auth_type, 'Invalid parameter',
            self.instance_id))

        #  Incorrect instance ID
        self.assertEqual((False, "Invalid instance ID"), self.header_ospfv3.parameter_validation(
            conf.VERSION_IPV6, self.packet_type, self.router_id, self.area_id, 0, 0, -1))
        self.assertEqual((False, "Invalid instance ID"), self.header_ospfv3.parameter_validation(
            conf.VERSION_IPV6, self.packet_type, self.router_id, self.area_id, 0, 0, conf.MAX_VALUE_8_BITS + 1))

    #  Successful run - Instant
    def test_set_checksum(self):
        self.header_ospfv2.set_checksum(1)
        self.header_ospfv3.set_checksum(1)
        self.assertEqual(1, self.header_ospfv2.checksum)
        self.assertEqual(1, self.header_ospfv3.checksum)

        with self.assertRaises(ValueError):
            self.header_ospfv2.set_checksum(-1)
            with self.assertRaises(ValueError):
                self.header_ospfv3.set_checksum(-1)
        with self.assertRaises(ValueError):
            self.header_ospfv2.set_checksum(conf.MAX_VALUE_16_BITS + 1)
        with self.assertRaises(ValueError):
            self.header_ospfv3.set_checksum(conf.MAX_VALUE_16_BITS + 1)

        self.assertEqual(1, self.header_ospfv2.checksum)
        self.assertEqual(1, self.header_ospfv3.checksum)

    #  Successful run - Instant
    def test_set_length(self):
        self.header_ospfv2.set_length(conf.OSPFV2_PACKET_HEADER_LENGTH)
        self.header_ospfv3.set_length(conf.OSPFV3_PACKET_HEADER_LENGTH)
        self.assertEqual(conf.OSPFV2_PACKET_HEADER_LENGTH, self.header_ospfv2.length)
        self.assertEqual(conf.OSPFV3_PACKET_HEADER_LENGTH, self.header_ospfv3.length)

        with self.assertRaises(ValueError):
            self.header_ospfv2.set_length(conf.OSPFV2_PACKET_HEADER_LENGTH - 1)
        with self.assertRaises(ValueError):
            self.header_ospfv3.set_length(conf.OSPFV3_PACKET_HEADER_LENGTH - 1)
        with self.assertRaises(ValueError):
            self.header_ospfv2.set_length(conf.MAX_VALUE_16_BITS + 1)
        with self.assertRaises(ValueError):
            self.header_ospfv3.set_length(conf.MAX_VALUE_16_BITS + 1)

        self.assertEqual(conf.OSPFV2_PACKET_HEADER_LENGTH, self.header_ospfv2.length)
        self.assertEqual(conf.OSPFV3_PACKET_HEADER_LENGTH, self.header_ospfv3.length)

    #  Successful run - Instant
    def test_format_string(self):
        self.assertEqual(header.OSPFV2_FORMAT_STRING, header.Header.get_format_string(conf.VERSION_IPV4))
        self.assertEqual(header.OSPFV3_FORMAT_STRING, header.Header.get_format_string(conf.VERSION_IPV6))
        with self.assertRaises(ValueError):
            header.Header.get_format_string(1)
