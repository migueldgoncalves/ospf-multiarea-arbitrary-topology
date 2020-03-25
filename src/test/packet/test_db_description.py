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

    db_description_ospfv2 = None
    db_description_ospfv3 = None

    def setUp(self):
        self.interface_mtu = 1
        self.options = 2
        self.i_bit = True
        self.m_bit = True
        self.ms_bit = True
        self.dd_sequence_number = 3
        self.lsa_header_1 = header.Header(10, 20, 1, 40, '1.1.1.1', 50, conf.VERSION_IPV4)
        self.lsa_header_2 = header.Header(60, 70, 2, 90, '2.2.2.2', 100, conf.VERSION_IPV4)
        self.lsa_header_3 = header.Header(110, 0, 3, 120, '3.3.3.3', 130, conf.VERSION_IPV6)

        self.db_description_ospfv2 = db_description.DBDescription()
        self.db_description_ospfv3 = db_description.DBDescription()

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

        #  Correct values for I, M and MS bits
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, False, False, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, False, True, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, True, False, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, False, True, True, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, True, True, True, self.dd_sequence_number, (self.lsa_header_1,),
            conf.VERSION_IPV4))

        #  Correct DD Sequence Number
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, 0, (self.lsa_header_1,),
            conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, conf.MAX_VALUE_32_BITS,
            (self.lsa_header_1,), conf.VERSION_IPV4))

        #  Correct LSA Headers
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1,), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
            (self.lsa_header_1, self.lsa_header_2), conf.VERSION_IPV4))
        self.assertEqual((True, ''), db_description.DBDescription.parameter_validation(
            self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number,
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
            (False, "There must be at least 1 LSA Header"), db_description.DBDescription.parameter_validation(
                self.interface_mtu, self.options, self.i_bit, self.m_bit, self.ms_bit, self.dd_sequence_number, (),
                conf.VERSION_IPV4))
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

        self.db_description_ospfv2 = None
        self.db_description_ospfv3 = None
