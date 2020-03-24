import unittest

import lsa.header as header
import conf.conf as conf

'''
This class tests the OSPF LSA header class and its operations
'''


#  Full successful run - Instant
class TestHeader(unittest.TestCase):
    ls_age = 0
    options = 0
    ls_type = 0
    link_state_id = 0
    advertising_router = '0.0.0.0'
    ls_sequence_number = 0

    header_ospfv2 = None
    header_ospfv3 = None

    def setUp(self):
        self.ls_age = 1
        self.options = 2
        self.ls_type = conf.LSA_TYPE_ROUTER
        self.link_state_id = 3
        self.advertising_router = '1.1.1.1'
        self.ls_sequence_number = 4
        self.header_ospfv2 = header.Header(self.ls_age, self.options, self.ls_type, self.link_state_id,
                                           self.advertising_router, self.ls_sequence_number, conf.VERSION_IPV4)
        self.header_ospfv3 = header.Header(self.ls_age, 0, self.ls_type, self.link_state_id, self.advertising_router,
                                           self.ls_sequence_number, conf.VERSION_IPV6)

    #  Successful run - Instant
    def test_constructor_v2_successful(self):
        self.assertEqual(self.ls_age, self.header_ospfv2.ls_age)
        self.assertEqual(self.options, self.header_ospfv2.options)
        self.assertEqual(self.ls_type, self.header_ospfv2.ls_type)
        self.assertEqual(self.link_state_id, self.header_ospfv2.link_state_id)
        self.assertEqual(self.advertising_router, self.header_ospfv2.advertising_router)
        self.assertEqual(self.ls_sequence_number, self.header_ospfv2.ls_sequence_number)
        self.assertEqual(0, self.header_ospfv2.ls_checksum)
        self.assertEqual(0, self.header_ospfv2.length)

    #  Successful run - Instant
    def test_constructor_v3_successful(self):
        self.assertEqual(self.ls_age, self.header_ospfv3.ls_age)
        self.assertEqual(self.ls_type, self.header_ospfv3.ls_type)
        self.assertEqual(self.link_state_id, self.header_ospfv3.link_state_id)
        self.assertEqual(self.advertising_router, self.header_ospfv3.advertising_router)
        self.assertEqual(self.ls_sequence_number, self.header_ospfv3.ls_sequence_number)
        self.assertEqual(0, self.header_ospfv3.ls_checksum)
        self.assertEqual(0, self.header_ospfv3.length)

    #  Successful run - Instant
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            header.Header(-1, self.options, self.ls_type, self.link_state_id, self.advertising_router,
                          self.ls_sequence_number, conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            header.Header(self.ls_age, -1, self.ls_type, self.link_state_id, self.advertising_router,
                          self.ls_sequence_number, conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            header.Header(self.ls_age, self.options, -1, self.link_state_id, self.advertising_router,
                          self.ls_sequence_number, conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            header.Header(self.ls_age, self.options, self.ls_type, -1, self.advertising_router, self.ls_sequence_number,
                          conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            header.Header(self.ls_age, self.options, self.ls_type, self.link_state_id, '', self.ls_sequence_number,
                          conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            header.Header(self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router, -1,
                          conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            header.Header(self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router,
                          self.ls_sequence_number, -1)

    #  Successful run - Instant
    def test_pack_header(self):
        header_bytes = b'\x00\x01\x02\x01\x00\x00\x00\x03\x01\x01\x01\x01\x00\x00\x00\x04\x00\x00\x00\x00'
        self.assertEqual(header_bytes, self.header_ospfv2.pack_header())
        self.header_ospfv2.ls_checksum = 10
        self.header_ospfv2.length = 20
        header_bytes = b'\x00\x01\x02\x01\x00\x00\x00\x03\x01\x01\x01\x01\x00\x00\x00\x04\x00\n\x00\x14'
        self.assertEqual(header_bytes, self.header_ospfv2.pack_header())

        header_bytes = b'\x00\x01\x00\x01\x00\x00\x00\x03\x01\x01\x01\x01\x00\x00\x00\x04\x00\x00\x00\x00'
        self.assertEqual(header_bytes, self.header_ospfv3.pack_header())
        self.header_ospfv3.ls_checksum = 30
        self.header_ospfv3.length = 40
        header_bytes = b'\x00\x01\x00\x01\x00\x00\x00\x03\x01\x01\x01\x01\x00\x00\x00\x04\x00\x1e\x00('
        self.assertEqual(header_bytes, self.header_ospfv3.pack_header())

    #  Successful run - Instant
    def test_unpack_header(self):
        header_bytes = b'\x00\x01\x02\x01\x00\x00\x00\x03\x01\x01\x01\x01\x00\x00\x00\x04\x00\n\x00\x14'
        unpacked_header = header.Header.unpack_header(header_bytes, conf.VERSION_IPV4)
        self.assertEqual(conf.VERSION_IPV4, unpacked_header.ospf_version)
        self.assertEqual(self.ls_age, unpacked_header.ls_age)
        self.assertEqual(self.options, unpacked_header.options)
        self.assertEqual(self.ls_type, unpacked_header.ls_type)
        self.assertEqual(self.link_state_id, unpacked_header.link_state_id)
        self.assertEqual(self.advertising_router, unpacked_header.advertising_router)
        self.assertEqual(self.ls_sequence_number, unpacked_header.ls_sequence_number)
        self.assertEqual(10, unpacked_header.ls_checksum)
        self.assertEqual(20, unpacked_header.length)

        header_bytes = b'\x00\x01\x00\x01\x00\x00\x00\x03\x01\x01\x01\x01\x00\x00\x00\x04\x00\x1e\x00('
        unpacked_header = header.Header.unpack_header(header_bytes, conf.VERSION_IPV6)
        self.assertEqual(conf.VERSION_IPV6, unpacked_header.ospf_version)
        self.assertEqual(self.ls_age, unpacked_header.ls_age)
        self.assertEqual(self.ls_type, unpacked_header.ls_type)
        self.assertEqual(self.link_state_id, unpacked_header.link_state_id)
        self.assertEqual(self.advertising_router, unpacked_header.advertising_router)
        self.assertEqual(self.ls_sequence_number, unpacked_header.ls_sequence_number)
        self.assertEqual(30, unpacked_header.ls_checksum)
        self.assertEqual(40, unpacked_header.length)

    #  Successful run - Instant
    def test_parameter_validation_successful(self):
        #  Correct LS Age
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            0, self.options, self.ls_type, self.link_state_id, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            conf.MAX_AGE, self.options, self.ls_type, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))

        #  Correct options
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, 0, self.ls_type, self.link_state_id, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, conf.MAX_VALUE_8_BITS, self.ls_type, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))

        #  Correct LS Type
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, conf.LSA_TYPE_ROUTER, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, conf.LSA_TYPE_NETWORK, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, conf.LSA_TYPE_SUMMARY_TYPE_3, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, conf.LSA_TYPE_SUMMARY_TYPE_4, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, conf.LSA_TYPE_AS_EXTERNAL, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv3.parameter_validation(
            self.ls_age, self.options, 1, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV6))
        self.assertEqual((True, ''), self.header_ospfv3.parameter_validation(
            self.ls_age, self.options, 24575, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV6))

        #  Correct Link State ID
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, 1, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, conf.MAX_VALUE_32_BITS, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))

        #  Correct Advertising Router
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, '0.0.0.1', self.ls_sequence_number,
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, '255.255.255.255', self.ls_sequence_number,
            conf.VERSION_IPV4))

        #  Correct LS Sequence Number
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router, 0x00000000,
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router, 0x80000001,
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router, 0xFFFFFFFF,
            conf.VERSION_IPV4))

        #  Correct OSPF version
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4))
        self.assertEqual((True, ''), self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV6))

    #  Successful run - Instant
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid LS Age
        self.assertEqual((False, "Invalid LS Age"), (self.header_ospfv2.parameter_validation(
            -1, self.options, self.ls_type, self.link_state_id, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid LS Age"), (self.header_ospfv2.parameter_validation(
            conf.MAX_AGE + 1, self.options, self.ls_type, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4)))

        #  Invalid options
        self.assertEqual((False, "Invalid options"), (self.header_ospfv2.parameter_validation(
            self.ls_age, -1, self.ls_type, self.link_state_id, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid options"), (self.header_ospfv2.parameter_validation(
            self.ls_age, conf.MAX_VALUE_8_BITS + 1, self.ls_type, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4)))

        #  Invalid LS Type
        self.assertEqual((False, "Invalid LS Type"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, 0, self.link_state_id, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid LS Type"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, 6, self.link_state_id, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid LS Type"), (self.header_ospfv3.parameter_validation(
            self.ls_age, self.options, 0, self.link_state_id, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV6)))
        self.assertEqual((False, "Invalid values for S1 and S2 bits"), (self.header_ospfv3.parameter_validation(
            self.ls_age, self.options, 24576, self.link_state_id, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV6)))

        #  Invalid Link State ID
        self.assertEqual((False, "Invalid Link State ID"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, 0, self.advertising_router, self.ls_sequence_number,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid Link State ID"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, conf.MAX_VALUE_32_BITS + 1, self.advertising_router,
            self.ls_sequence_number, conf.VERSION_IPV4)))

        #  Invalid Advertising Router
        self.assertEqual((False, "Invalid Advertising Router"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, '0.0.0.0', self.ls_sequence_number,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid Advertising Router"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, '255.255.255.256', self.ls_sequence_number,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid Advertising Router"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, '', self.ls_sequence_number,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid Advertising Router"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, 'Invalid address', self.ls_sequence_number,
            conf.VERSION_IPV4)))

        #  Invalid LS Sequence Number
        self.assertEqual((False, "Invalid LS Sequence Number"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router, -1,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid LS Sequence Number"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router, 0x80000000,
            conf.VERSION_IPV4)))
        self.assertEqual((False, "Invalid LS Sequence Number"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router, 0x100000000,
            conf.VERSION_IPV4)))

        #  Invalid OSPF version
        self.assertEqual((False, "Invalid OSPF version"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, 1)))
        self.assertEqual((False, "Invalid OSPF version"), (self.header_ospfv2.parameter_validation(
            self.ls_age, self.options, self.ls_type, self.link_state_id, self.advertising_router,
            self.ls_sequence_number, 4)))

    #  Successful run - Instant
    def test_get_u_bit(self):
        self.assertEqual(0, header.Header.get_u_bit(0))
        self.assertEqual(0, header.Header.get_u_bit(32767))
        self.assertEqual(1, header.Header.get_u_bit(32768))
        self.assertEqual(1, header.Header.get_u_bit(65535))

    #  Successful run - Instant
    def test_get_s1_s2_bits(self):
        self.assertEqual(0, header.Header.get_s1_s2_bits(0))
        self.assertEqual(0, header.Header.get_s1_s2_bits(8191))
        self.assertEqual(1, header.Header.get_s1_s2_bits(8192))
        self.assertEqual(1, header.Header.get_s1_s2_bits(16383))
        self.assertEqual(2, header.Header.get_s1_s2_bits(16384))
        self.assertEqual(2, header.Header.get_s1_s2_bits(24575))
        self.assertEqual(3, header.Header.get_s1_s2_bits(24576))
        self.assertEqual(3, header.Header.get_s1_s2_bits(32767))

    #  Successful run - Instant
    def test_format_string(self):
        self.assertEqual(header.OSPFV2_FORMAT_STRING, header.Header.get_format_string(conf.VERSION_IPV4))
        self.assertEqual(header.OSPFV3_FORMAT_STRING, header.Header.get_format_string(conf.VERSION_IPV6))
        with self.assertRaises(ValueError):
            header.Header.get_format_string(1)

    def tearDown(self):
        self.ls_age = 0
        self.options = 0
        self.ls_type = 0
        self.link_state_id = 0
        self.advertising_router = '0.0.0.0'
        self.ls_sequence_number = 0
        self.header_ospfv2 = None
        self.header_ospfv3 = None