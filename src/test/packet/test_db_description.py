import unittest

import lsa.header as header
import conf.conf as conf
import packet.db_description as db_description

'''
This class tests the OSPF Database Description packet class and its operations
'''


#  Full successful run - Instant
class TestDBDescription(unittest.TestCase):
    interface_mtu = 0
    options = 0
    i_bit = False
    m_bit = False
    ms_bit = False
    dd_sequence_number = 0
    lsa_header_1 = None
    lsa_header_2 = None
    lsa_header_3 = None
    lsa_header_4 = None
    lsa_header_5 = None

    db_description_ospfv2 = None
    db_description_ospfv3 = None

    def setUp(self):
        self.interface_mtu = 1
        self.options = 2
        self.i_bit = False
        self.m_bit = True
        self.ms_bit = True
        self.dd_sequence_number = 3
        self.lsa_header_1 = header.Header(10, 20, 1, 30, '1.1.1.1', 40, conf.VERSION_IPV4)
        self.lsa_header_2 = header.Header(50, 60, 2, 70, '2.2.2.2', 80, conf.VERSION_IPV4)
        self.lsa_header_3 = header.Header(90, 0, 3, 100, '3.3.3.3', 110, conf.VERSION_IPV6)
        self.lsa_header_4 = header.Header(120, 0, 4, 130, '4.4.4.4', 140, conf.VERSION_IPV6)
        self.lsa_header_5 = header.Header(150, 0, 5, 160, '5.5.5.5', 170, conf.VERSION_IPV6)

        self.db_description_ospfv2 = db_description.DBDescription(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4)
        self.db_description_ospfv3 = db_description.DBDescription(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_3, self.lsa_header_4), conf.VERSION_IPV6)

    #  Successful run - Instant
    def test_constructor_v2_successful(self):
        self.assertEqual(self.interface_mtu, self.db_description_ospfv2.interface_mtu)
        self.assertEqual(self.options, self.db_description_ospfv2.options)
        self.assertEqual(self.i_bit, self.db_description_ospfv2.i_bit)
        self.assertEqual(self.m_bit, self.db_description_ospfv2.m_bit)
        self.assertEqual(self.ms_bit, self.db_description_ospfv2.ms_bit)
        self.assertEqual(self.dd_sequence_number, self.db_description_ospfv2.dd_sequence_number)
        self.assertEqual(1, len(self.db_description_ospfv2.lsa_headers))
        self.assertEqual(self.lsa_header_1.ls_age, self.db_description_ospfv2.lsa_headers[0].ls_age)
        self.assertEqual(self.lsa_header_1.ls_type, self.db_description_ospfv2.lsa_headers[0].ls_type)
        self.assertEqual(
            self.lsa_header_1.advertising_router, self.db_description_ospfv2.lsa_headers[0].advertising_router)

    #  Successful run - Instant
    def test_constructor_v3_successful(self):
        self.assertEqual(self.interface_mtu, self.db_description_ospfv3.interface_mtu)
        self.assertEqual(self.options, self.db_description_ospfv3.options)
        self.assertEqual(self.i_bit, self.db_description_ospfv3.i_bit)
        self.assertEqual(self.m_bit, self.db_description_ospfv3.m_bit)
        self.assertEqual(self.ms_bit, self.db_description_ospfv3.ms_bit)
        self.assertEqual(self.dd_sequence_number, self.db_description_ospfv3.dd_sequence_number)
        self.assertEqual(2, len(self.db_description_ospfv3.lsa_headers))
        self.assertEqual(self.lsa_header_3.ls_age, self.db_description_ospfv3.lsa_headers[0].ls_age)
        self.assertEqual(self.lsa_header_4.ls_age, self.db_description_ospfv3.lsa_headers[1].ls_age)
        self.assertEqual(self.lsa_header_3.ls_type, self.db_description_ospfv3.lsa_headers[0].ls_type)
        self.assertEqual(self.lsa_header_4.ls_type, self.db_description_ospfv3.lsa_headers[1].ls_type)
        self.assertEqual(
            self.lsa_header_3.advertising_router, self.db_description_ospfv3.lsa_headers[0].advertising_router)
        self.assertEqual(
            self.lsa_header_4.advertising_router, self.db_description_ospfv3.lsa_headers[1].advertising_router)

    #  Successful run - Instant
    def test_constructor_invalid_parameters(self):
        with self.assertRaises(ValueError):
            db_description.DBDescription(0, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
                                         (), conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            db_description.DBDescription(self.interface_mtu, -1, self.i_bit, self.m_bit, self.ms_bit,
                                         self.dd_sequence_number, (), conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            db_description.DBDescription(self.interface_mtu, self.options, True, False, False, self.dd_sequence_number,
                                         (), conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            db_description.DBDescription(self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, -1, (),
                                         conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            db_description.DBDescription(self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit,
                                         self.dd_sequence_number, (None,), conf.VERSION_IPV4)
        with self.assertRaises(ValueError):
            db_description.DBDescription(self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit,
                                         self.dd_sequence_number, (), 1)

    #  Successful run - Instant
    def test_pack_packet(self):
        packet_body_bytes = b'\x00\x01\x02\x07\x00\x00\x00\x03'
        packet_body = db_description.DBDescription(self.interface_mtu, self.options, True, True, True,
                                                   self.dd_sequence_number, (), conf.VERSION_IPV4)
        self.assertEqual(packet_body_bytes, packet_body.pack_packet_body())
        packet_body_bytes = b'\x00\x01\x02\x03\x00\x00\x00\x03\x00\n\x14\x01\x00\x00\x00\x1e\x01\x01\x01\x01\x00\x00' \
                            b'\x00(\x00\x00\x00\x00'
        packet_body = db_description.DBDescription(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4)
        self.assertEqual(packet_body_bytes, packet_body.pack_packet_body())
        packet_body_bytes = b'\x00\x01\x02\x03\x00\x00\x00\x03\x00\n\x14\x01\x00\x00\x00\x1e\x01\x01\x01\x01\x00\x00' \
                            b'\x00(\x00\x00\x00\x00\x002<\x02\x00\x00\x00F\x02\x02\x02\x02\x00\x00\x00P\x00\x00\x00\x00'
        packet_body = db_description.DBDescription(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1, self.lsa_header_2), conf.VERSION_IPV4)
        self.assertEqual(packet_body_bytes, packet_body.pack_packet_body())

        packet_body_bytes = b'\x00\x00\x00\x02\x00\x01\x00\x07\x00\x00\x00\x03'
        packet_body = db_description.DBDescription(self.interface_mtu, self.options, True, True, True,
                                                   self.dd_sequence_number, (), conf.VERSION_IPV6)
        self.assertEqual(packet_body_bytes, packet_body.pack_packet_body())
        packet_body_bytes = b'\x00\x00\x00\x02\x00\x01\x00\x03\x00\x00\x00\x03\x00Z\x00\x03\x00\x00\x00d\x03\x03\x03' \
                            b'\x03\x00\x00\x00n\x00\x00\x00\x00'
        packet_body = db_description.DBDescription(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_3,), conf.VERSION_IPV6)
        self.assertEqual(packet_body_bytes, packet_body.pack_packet_body())
        packet_body_bytes = b'\x00\x00\x00\x02\x00\x01\x00\x03\x00\x00\x00\x03\x00Z\x00\x03\x00\x00\x00d\x03\x03\x03' \
                            b'\x03\x00\x00\x00n\x00\x00\x00\x00\x00x\x00\x04\x00\x00\x00\x82\x04\x04\x04\x04\x00\x00' \
                            b'\x00\x8c\x00\x00\x00\x00\x00\x96\x00\x05\x00\x00\x00\xa0\x05\x05\x05\x05\x00\x00\x00' \
                            b'\xaa\x00\x00\x00\x00'
        packet_body = db_description.DBDescription(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_3, self.lsa_header_4, self.lsa_header_5), conf.VERSION_IPV6)
        self.assertEqual(packet_body_bytes, packet_body.pack_packet_body())

    #  Successful run - Instant
    def test_unpack_packet(self):
        packet_body_bytes = b'\x00\x01\x02\x07\x00\x00\x00\x03'
        packet_body = db_description.DBDescription.unpack_packet_body(packet_body_bytes, conf.VERSION_IPV4)
        self.assertEqual(self.interface_mtu, packet_body.interface_mtu)
        self.assertEqual(self.options, packet_body.options)
        self.assertTrue(packet_body.i_bit)
        self.assertTrue(packet_body.m_bit)
        self.assertTrue(packet_body.ms_bit)
        self.assertEqual(self.dd_sequence_number, packet_body.dd_sequence_number)
        self.assertEqual(0, len(packet_body.lsa_headers))
        self.assertEqual(conf.VERSION_IPV4, packet_body.version)
        packet_body_bytes = b'\x00\x01\x02\x03\x00\x00\x00\x03\x00\n\x14\x01\x00\x00\x00\x1e\x01\x01\x01\x01\x00\x00' \
                            b'\x00(\x00\x00\x00\x00'
        packet_body = db_description.DBDescription.unpack_packet_body(packet_body_bytes, conf.VERSION_IPV4)
        self.assertEqual(self.interface_mtu, packet_body.interface_mtu)
        self.assertEqual(self.options, packet_body.options)
        self.assertEqual(self.i_bit, packet_body.i_bit)
        self.assertEqual(self.m_bit, packet_body.m_bit)
        self.assertEqual(self.ms_bit, packet_body.ms_bit)
        self.assertEqual(self.dd_sequence_number, packet_body.dd_sequence_number)
        self.assertEqual(1, len(packet_body.lsa_headers))
        self.assertEqual(self.lsa_header_1.ls_age, packet_body.lsa_headers[0].ls_age)
        self.assertEqual(self.lsa_header_1.ls_type, packet_body.lsa_headers[0].ls_type)
        self.assertEqual(self.lsa_header_1.advertising_router, packet_body.lsa_headers[0].advertising_router)
        self.assertEqual(conf.VERSION_IPV4, packet_body.version)
        packet_body_bytes = b'\x00\x01\x02\x03\x00\x00\x00\x03\x00\n\x14\x01\x00\x00\x00\x1e\x01\x01\x01\x01\x00\x00' \
                            b'\x00(\x00\x00\x00\x00\x002<\x02\x00\x00\x00F\x02\x02\x02\x02\x00\x00\x00P\x00\x00\x00\x00'
        packet_body = db_description.DBDescription.unpack_packet_body(packet_body_bytes, conf.VERSION_IPV4)
        self.assertEqual(self.interface_mtu, packet_body.interface_mtu)
        self.assertEqual(self.options, packet_body.options)
        self.assertEqual(self.i_bit, packet_body.i_bit)
        self.assertEqual(self.m_bit, packet_body.m_bit)
        self.assertEqual(self.ms_bit, packet_body.ms_bit)
        self.assertEqual(self.dd_sequence_number, packet_body.dd_sequence_number)
        self.assertEqual(2, len(packet_body.lsa_headers))
        self.assertEqual(self.lsa_header_1.ls_age, packet_body.lsa_headers[0].ls_age)
        self.assertEqual(self.lsa_header_1.ls_type, packet_body.lsa_headers[0].ls_type)
        self.assertEqual(self.lsa_header_1.advertising_router, packet_body.lsa_headers[0].advertising_router)
        self.assertEqual(self.lsa_header_2.ls_age, packet_body.lsa_headers[1].ls_age)
        self.assertEqual(self.lsa_header_2.ls_type, packet_body.lsa_headers[1].ls_type)
        self.assertEqual(self.lsa_header_2.advertising_router, packet_body.lsa_headers[1].advertising_router)
        self.assertEqual(conf.VERSION_IPV4, packet_body.version)

        packet_body_bytes = b'\x00\x00\x00\x02\x00\x01\x00\x07\x00\x00\x00\x03'
        packet_body = db_description.DBDescription.unpack_packet_body(packet_body_bytes, conf.VERSION_IPV6)
        self.assertEqual(self.interface_mtu, packet_body.interface_mtu)
        self.assertEqual(self.options, packet_body.options)
        self.assertTrue(packet_body.i_bit)
        self.assertTrue(packet_body.m_bit)
        self.assertTrue(packet_body.ms_bit)
        self.assertEqual(self.dd_sequence_number, packet_body.dd_sequence_number)
        self.assertEqual(0, len(packet_body.lsa_headers))
        self.assertEqual(conf.VERSION_IPV6, packet_body.version)
        packet_body_bytes = b'\x00\x00\x00\x02\x00\x01\x00\x03\x00\x00\x00\x03\x00Z\x00\x03\x00\x00\x00d\x03\x03\x03' \
                            b'\x03\x00\x00\x00n\x00\x00\x00\x00'
        packet_body = db_description.DBDescription.unpack_packet_body(packet_body_bytes, conf.VERSION_IPV6)
        self.assertEqual(self.interface_mtu, packet_body.interface_mtu)
        self.assertEqual(self.options, packet_body.options)
        self.assertEqual(self.i_bit, packet_body.i_bit)
        self.assertEqual(self.m_bit, packet_body.m_bit)
        self.assertEqual(self.ms_bit, packet_body.ms_bit)
        self.assertEqual(self.dd_sequence_number, packet_body.dd_sequence_number)
        self.assertEqual(1, len(packet_body.lsa_headers))
        self.assertEqual(self.lsa_header_3.ls_age, packet_body.lsa_headers[0].ls_age)
        self.assertEqual(self.lsa_header_3.ls_type, packet_body.lsa_headers[0].ls_type)
        self.assertEqual(self.lsa_header_3.advertising_router, packet_body.lsa_headers[0].advertising_router)
        self.assertEqual(conf.VERSION_IPV6, packet_body.version)
        packet_body_bytes = b'\x00\x00\x00\x02\x00\x01\x00\x03\x00\x00\x00\x03\x00Z\x00\x03\x00\x00\x00d\x03\x03\x03' \
                            b'\x03\x00\x00\x00n\x00\x00\x00\x00\x00x\x00\x04\x00\x00\x00\x82\x04\x04\x04\x04\x00\x00' \
                            b'\x00\x8c\x00\x00\x00\x00\x00\x96\x00\x05\x00\x00\x00\xa0\x05\x05\x05\x05\x00\x00\x00' \
                            b'\xaa\x00\x00\x00\x00'
        packet_body = db_description.DBDescription.unpack_packet_body(packet_body_bytes, conf.VERSION_IPV6)
        self.assertEqual(self.interface_mtu, packet_body.interface_mtu)
        self.assertEqual(self.options, packet_body.options)
        self.assertEqual(self.i_bit, packet_body.i_bit)
        self.assertEqual(self.m_bit, packet_body.m_bit)
        self.assertEqual(self.ms_bit, packet_body.ms_bit)
        self.assertEqual(self.dd_sequence_number, packet_body.dd_sequence_number)
        self.assertEqual(3, len(packet_body.lsa_headers))
        self.assertEqual(self.lsa_header_3.ls_age, packet_body.lsa_headers[0].ls_age)
        self.assertEqual(self.lsa_header_3.ls_type, packet_body.lsa_headers[0].ls_type)
        self.assertEqual(self.lsa_header_3.advertising_router, packet_body.lsa_headers[0].advertising_router)
        self.assertEqual(self.lsa_header_4.ls_age, packet_body.lsa_headers[1].ls_age)
        self.assertEqual(self.lsa_header_4.ls_type, packet_body.lsa_headers[1].ls_type)
        self.assertEqual(self.lsa_header_4.advertising_router, packet_body.lsa_headers[1].advertising_router)
        self.assertEqual(self.lsa_header_5.ls_age, packet_body.lsa_headers[2].ls_age)
        self.assertEqual(self.lsa_header_5.ls_type, packet_body.lsa_headers[2].ls_type)
        self.assertEqual(self.lsa_header_5.advertising_router, packet_body.lsa_headers[2].advertising_router)
        self.assertEqual(conf.VERSION_IPV6, packet_body.version)

    #  Successful run - Instant
    def test_get_format_string(self):
        self.assertEqual(
            db_description.OSPFV2_BASE_FORMAT_STRING, db_description.DBDescription.get_format_string(conf.VERSION_IPV4))
        self.assertEqual(
            db_description.OSPFV3_BASE_FORMAT_STRING, db_description.DBDescription.get_format_string(conf.VERSION_IPV6))
        with self.assertRaises(ValueError):
            db_description.DBDescription.get_format_string(-1)

    #  Successful run - Instant
    def test_parameter_validation_successful(self):
        #  Correct Interface MTU
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            1, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            conf.MAX_VALUE_16_BITS, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4))

        #  Correct options
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, 0, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, conf.MAX_VALUE_8_BITS, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, conf.MAX_VALUE_24_BITS, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV6))

        #  Correct values for I, M and MS bits
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, False, False, self.dd_sequence_number, (), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, False, True, self.dd_sequence_number, (), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, True, False, self.dd_sequence_number, (), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, True, True, self.dd_sequence_number, (), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, True, True, True, self.dd_sequence_number, (), conf.VERSION_IPV4))

        #  Correct DD Sequence Number
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, 0, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, conf.MAX_VALUE_32_BITS,
            (self.lsa_header_1,), conf.VERSION_IPV4))

        #  Correct LSA Headers
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, True, True, True, self.dd_sequence_number, (), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1, self.lsa_header_2), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1, self.lsa_header_2, self.lsa_header_3), conf.VERSION_IPV4))

        #  Correct OSPF version
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV6))
        
    #  Successful run - Instant
    def test_parameter_validation_invalid_parameters(self):
        #  Invalid Interface MTU
        self.assertEqual((False, "Invalid MTU"), db_description.DBDescription.parameter_validation(
            0, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((False, "Invalid MTU"), db_description.DBDescription.parameter_validation(
            conf.MAX_VALUE_16_BITS + 1, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4))

        #  Invalid options
        self.assertEqual((False, "Invalid packet options"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, -1, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((False, "Invalid packet options"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, conf.MAX_VALUE_8_BITS + 1, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4))
        self.assertEqual((False, "Invalid packet options"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, conf.MAX_VALUE_24_BITS + 1, self.i_bit, self.m_bit, self.ms_bit,
            self.dd_sequence_number, (self.lsa_header_1,), conf.VERSION_IPV4))

        #  Invalid values for I, M and MS bits
        self.assertEqual(
            (False, "Invalid values for I, M and MS bits"), db_description.DBDescription.parameter_validation(
                self.interface_mtu, self.options, True, False, False, self.dd_sequence_number, (self.lsa_header_1,),
                conf.VERSION_IPV4))
        self.assertEqual(
            (False, "Invalid values for I, M and MS bits"), db_description.DBDescription.parameter_validation(
                self.interface_mtu, self.options, True, False, True, self.dd_sequence_number, (self.lsa_header_1,),
                conf.VERSION_IPV4))
        self.assertEqual(
            (False, "Invalid values for I, M and MS bits"), db_description.DBDescription.parameter_validation(
                self.interface_mtu, self.options, True, True, False, self.dd_sequence_number, (self.lsa_header_1,),
                conf.VERSION_IPV4))

        #  Invalid DD Sequence Number
        self.assertEqual((False, "Invalid DD Sequence Number"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, -1, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((False, "Invalid DD Sequence Number"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, conf.MAX_VALUE_32_BITS + 1,
            (self.lsa_header_1,), conf.VERSION_IPV4))

        #  Invalid LSA Headers
        self.assertEqual(
            (False, "ExStart state - There must be no LSA Headers"), db_description.DBDescription.parameter_validation(
                self.interface_mtu, self.options, True, self.m_bit, self.ms_bit, self.dd_sequence_number,
                (self.lsa_header_1,), conf.VERSION_IPV4))
        self.assertEqual((False, "Invalid parameter type"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1, 0), conf.VERSION_IPV4))
        self.assertEqual((False, "Invalid parameter type"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1, 'Invalid LSA Header', self.lsa_header_3), conf.VERSION_IPV4))
        self.assertEqual((False, "Invalid parameter type"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (False,), conf.VERSION_IPV4))
        self.assertEqual((False, "Invalid parameter type"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (None,), conf.VERSION_IPV4))

        #  Invalid OSPF version
        self.assertEqual((False, "Invalid OSPF version"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), 1))
        self.assertEqual((False, "Invalid OSPF version"), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), 4))

    def tearDown(self):
        self.lsa_header_1 = None
        self.lsa_header_2 = None
        self.lsa_header_3 = None
        self.lsa_header_4 = None
        self.lsa_header_5 = None

        self.db_description_ospfv2 = None
        self.db_description_ospfv3 = None
