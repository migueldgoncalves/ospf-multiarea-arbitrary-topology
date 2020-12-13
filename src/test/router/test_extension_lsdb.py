import unittest
import time

import conf.conf as conf
import lsa.lsa as lsa
import router.extension_lsdb as extension_lsdb
import general.utils as utils

'''
This class tests the extension LSDB operations in the router
'''

ADVERTISING_ROUTER = '1.1.1.1'
BIT_U = True
BITS_S1_S2 = conf.AS_SCOPING
BITS_U_S1_S2 = (BIT_U << conf.BYTE_SIZE + 7) + (BITS_S1_S2 << conf.BYTE_SIZE + 5)


#  Full successful run - 2 s
class TestExtensionLsdb(unittest.TestCase):
    
    def setUp(self):
        self.abr_lsa_v2 = lsa.Lsa()
        self.abr_lsa_v3 = lsa.Lsa()
        self.prefix_lsa_v2 = lsa.Lsa()
        self.prefix_lsa_v3 = lsa.Lsa()
        self.abr_lsa_v2.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.OPAQUE_TYPE_ABR_LSA, 0, ADVERTISING_ROUTER,
            conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        self.abr_lsa_v3.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, conf.LSA_TYPE_EXTENSION_ABR_LSA, ADVERTISING_ROUTER,
            conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
        self.prefix_lsa_v2.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.OPAQUE_TYPE_PREFIX_LSA, 0, ADVERTISING_ROUTER,
            conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV4)
        self.prefix_lsa_v3.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, conf.LSA_TYPE_EXTENSION_PREFIX_LSA, ADVERTISING_ROUTER,
            conf.INITIAL_SEQUENCE_NUMBER, conf.VERSION_IPV6)
        self.abr_lsa_v2.create_extension_abr_lsa_body()
        self.abr_lsa_v3.create_extension_abr_lsa_body()
        self.prefix_lsa_v2.create_extension_prefix_lsa_body(conf.VERSION_IPV4)
        self.prefix_lsa_v3.create_extension_prefix_lsa_body(conf.VERSION_IPV6)
        self.abr_lsa_v2_id = [
            conf.LSA_TYPE_OPAQUE_AS, utils.Utils.decimal_to_ipv4(conf.OPAQUE_TYPE_ABR_LSA << 3 * conf.BYTE_SIZE),
            ADVERTISING_ROUTER]
        self.abr_lsa_v3_id = [BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, conf.DEFAULT_LINK_STATE_ID,
                              ADVERTISING_ROUTER]
        self.prefix_lsa_v2_id = [
            conf.LSA_TYPE_OPAQUE_AS, utils.Utils.decimal_to_ipv4(conf.OPAQUE_TYPE_PREFIX_LSA << 3 * conf.BYTE_SIZE),
            ADVERTISING_ROUTER]
        self.prefix_lsa_v3_id = [BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA, conf.DEFAULT_LINK_STATE_ID,
                                 ADVERTISING_ROUTER]

        self.extension_lsdb_v2 = extension_lsdb.ExtensionLsdb(conf.VERSION_IPV4)
        self.extension_lsdb_v3 = extension_lsdb.ExtensionLsdb(conf.VERSION_IPV6)

    #  Successful run - Instant
    def test_constructor_test(self):
        self.assertEqual(0, len(self.extension_lsdb_v2.abr_lsa_list))
        self.assertEqual(0, len(self.extension_lsdb_v2.prefix_lsa_list))
        self.assertEqual(0, len(self.extension_lsdb_v2.asbr_lsa_list))
        self.assertEqual(0, len(self.extension_lsdb_v3.abr_lsa_list))
        self.assertEqual(0, len(self.extension_lsdb_v3.prefix_lsa_list))
        self.assertEqual(0, len(self.extension_lsdb_v3.asbr_lsa_list))
        self.assertFalse(self.extension_lsdb_v2.is_modified.is_set())
        self.assertFalse(self.extension_lsdb_v3.is_modified.is_set())

    #  Successful run - Instant
    def test_get_lsa(self):
        self.populate_lsdb()

        #  Get LSDB

        retrieved_lsdb = self.extension_lsdb_v2.get_extension_lsdb(None)
        self.assertEqual(2, len(retrieved_lsdb))
        self.assertEqual(conf.OPAQUE_TYPE_ABR_LSA, retrieved_lsdb[0].get_opaque_type())
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_lsdb[0].header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_PREFIX_LSA, retrieved_lsdb[1].get_opaque_type())
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_lsdb[1].header.ls_type)
        retrieved_lsdb = self.extension_lsdb_v2.get_extension_lsdb([self.abr_lsa_v2_id])
        self.assertEqual(1, len(retrieved_lsdb))
        self.assertEqual(conf.OPAQUE_TYPE_ABR_LSA, retrieved_lsdb[0].get_opaque_type())
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_lsdb[0].header.ls_type)
        retrieved_lsdb = self.extension_lsdb_v2.get_extension_lsdb([self.abr_lsa_v2_id, self.prefix_lsa_v2_id])
        self.assertEqual(2, len(retrieved_lsdb))
        self.assertEqual(conf.OPAQUE_TYPE_ABR_LSA, retrieved_lsdb[0].get_opaque_type())
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_lsdb[0].header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_PREFIX_LSA, retrieved_lsdb[1].get_opaque_type())
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_lsdb[1].header.ls_type)
        self.assertFalse(self.extension_lsdb_v2.is_modified.is_set())

        retrieved_lsdb = self.extension_lsdb_v3.get_extension_lsdb(None)
        self.assertEqual(2, len(retrieved_lsdb))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, retrieved_lsdb[0].header.ls_type)
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA, retrieved_lsdb[1].header.ls_type)
        retrieved_lsdb = self.extension_lsdb_v3.get_extension_lsdb([self.abr_lsa_v3_id])
        self.assertEqual(1, len(retrieved_lsdb))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, retrieved_lsdb[0].header.ls_type)
        retrieved_lsdb = self.extension_lsdb_v3.get_extension_lsdb([self.abr_lsa_v3_id, self.prefix_lsa_v3_id])
        self.assertEqual(2, len(retrieved_lsdb))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, retrieved_lsdb[0].header.ls_type)
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA, retrieved_lsdb[1].header.ls_type)
        self.assertFalse(self.extension_lsdb_v3.is_modified.is_set())

        #  Get a LSA

        retrieved_lsa = self.extension_lsdb_v2.get_extension_lsa(0, 0, '0.0.0.0')
        self.assertIsNone(retrieved_lsa)
        retrieved_lsa = self.extension_lsdb_v2.get_extension_lsa(0, conf.OPAQUE_TYPE_ABR_LSA, ADVERTISING_ROUTER)
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_lsa.header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_ABR_LSA, retrieved_lsa.get_opaque_type())
        retrieved_lsa = self.extension_lsdb_v2.get_extension_lsa(0, conf.OPAQUE_TYPE_PREFIX_LSA, ADVERTISING_ROUTER)
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_lsa.header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_PREFIX_LSA, retrieved_lsa.get_opaque_type())
        self.assertFalse(self.extension_lsdb_v2.is_modified.is_set())

        retrieved_lsa = self.extension_lsdb_v3.get_extension_lsa(0, 0, '0.0.0.0')
        self.assertIsNone(retrieved_lsa)
        retrieved_lsa = self.extension_lsdb_v3.get_extension_lsa(conf.LSA_TYPE_EXTENSION_ABR_LSA, 0, ADVERTISING_ROUTER)
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, retrieved_lsa.header.ls_type)
        retrieved_lsa = self.extension_lsdb_v3.get_extension_lsa(
            conf.LSA_TYPE_EXTENSION_PREFIX_LSA, 0, ADVERTISING_ROUTER)
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA, retrieved_lsa.header.ls_type)
        self.assertFalse(self.extension_lsdb_v3.is_modified.is_set())

        #  Get LSDB headers

        retrieved_headers = self.extension_lsdb_v2.get_extension_lsa_headers(None)
        self.assertEqual(2, len(retrieved_headers))
        self.assertEqual(
            conf.OPAQUE_TYPE_ABR_LSA, retrieved_headers[0].get_opaque_type(retrieved_headers[0].link_state_id))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_headers[0].ls_type)
        self.assertEqual(
            conf.OPAQUE_TYPE_PREFIX_LSA, retrieved_headers[1].get_opaque_type(retrieved_headers[1].link_state_id))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_headers[1].ls_type)
        retrieved_headers = self.extension_lsdb_v2.get_extension_lsa_headers([self.abr_lsa_v2_id])
        self.assertEqual(1, len(retrieved_headers))
        self.assertEqual(
            conf.OPAQUE_TYPE_ABR_LSA, retrieved_headers[0].get_opaque_type(retrieved_headers[0].link_state_id))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_headers[0].ls_type)
        retrieved_headers = self.extension_lsdb_v2.get_extension_lsa_headers(
            [self.abr_lsa_v2_id, self.prefix_lsa_v2_id])
        self.assertEqual(2, len(retrieved_headers))
        self.assertEqual(
            conf.OPAQUE_TYPE_ABR_LSA, retrieved_headers[0].get_opaque_type(retrieved_headers[0].link_state_id))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_headers[0].ls_type)
        self.assertEqual(
            conf.OPAQUE_TYPE_PREFIX_LSA, retrieved_headers[1].get_opaque_type(retrieved_headers[1].link_state_id))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_headers[1].ls_type)
        self.assertFalse(self.extension_lsdb_v2.is_modified.is_set())

        retrieved_headers = self.extension_lsdb_v3.get_extension_lsdb(None)
        self.assertEqual(2, len(retrieved_headers))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, retrieved_headers[0].header.ls_type)
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA, retrieved_headers[1].header.ls_type)
        retrieved_headers = self.extension_lsdb_v3.get_extension_lsdb([self.abr_lsa_v3_id])
        self.assertEqual(1, len(retrieved_headers))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, retrieved_headers[0].header.ls_type)
        retrieved_headers = self.extension_lsdb_v3.get_extension_lsdb([self.abr_lsa_v3_id, self.prefix_lsa_v3_id])
        self.assertEqual(2, len(retrieved_headers))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, retrieved_headers[0].header.ls_type)
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA, retrieved_headers[1].header.ls_type)
        self.assertFalse(self.extension_lsdb_v3.is_modified.is_set())

        #  Get a LSA header

        retrieved_header = self.extension_lsdb_v2.get_extension_lsa_header(0, 0, '0.0.0.0')
        self.assertIsNone(retrieved_header)
        retrieved_header = self.extension_lsdb_v2.get_extension_lsa_header(
            0, conf.OPAQUE_TYPE_ABR_LSA, ADVERTISING_ROUTER)
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_ABR_LSA, retrieved_header.get_opaque_type(retrieved_header.link_state_id))
        retrieved_header = self.extension_lsdb_v2.get_extension_lsa_header(
            0, conf.OPAQUE_TYPE_PREFIX_LSA, ADVERTISING_ROUTER)
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, retrieved_header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_PREFIX_LSA, retrieved_header.get_opaque_type(retrieved_header.link_state_id))
        self.assertFalse(self.extension_lsdb_v2.is_modified.is_set())

        retrieved_header = self.extension_lsdb_v3.get_extension_lsa_header(0, 0, '0.0.0.0')
        self.assertIsNone(retrieved_header)
        retrieved_header = self.extension_lsdb_v3.get_extension_lsa_header(
            conf.LSA_TYPE_EXTENSION_ABR_LSA, 0, ADVERTISING_ROUTER)
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA, retrieved_header.ls_type)
        retrieved_header = self.extension_lsdb_v3.get_extension_lsa_header(
            conf.LSA_TYPE_EXTENSION_PREFIX_LSA, 0, ADVERTISING_ROUTER)
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA, retrieved_header.ls_type)
        self.assertFalse(self.extension_lsdb_v3.is_modified.is_set())

    #  Successful run - Instant
    def test_delete_lsa(self):
        self.populate_lsdb()

        #  Delete a LSA

        self.extension_lsdb_v2.delete_extension_lsa(0, 0, '0.0.0.0')
        self.assertEqual(2, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertFalse(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v2.delete_extension_lsa(0, conf.OPAQUE_TYPE_ABR_LSA, ADVERTISING_ROUTER)
        self.assertEqual(1, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertEqual(
            conf.OPAQUE_TYPE_PREFIX_LSA, self.extension_lsdb_v2.get_extension_lsdb(None)[0].get_opaque_type())
        self.assertTrue(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v2.is_modified.clear()
        self.extension_lsdb_v2.delete_extension_lsa(0, conf.OPAQUE_TYPE_ABR_LSA, ADVERTISING_ROUTER)
        self.assertEqual(1, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertFalse(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v2.delete_extension_lsa(0, conf.OPAQUE_TYPE_PREFIX_LSA, ADVERTISING_ROUTER)
        self.assertEqual(0, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertTrue(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v2.is_modified.clear()

        self.extension_lsdb_v3.delete_extension_lsa(0, 0, '0.0.0.0')
        self.assertEqual(2, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertFalse(self.extension_lsdb_v3.is_modified.is_set())
        self.extension_lsdb_v3.delete_extension_lsa(conf.LSA_TYPE_EXTENSION_ABR_LSA, 0, ADVERTISING_ROUTER)
        self.assertEqual(1, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[0].header.ls_type)
        self.assertTrue(self.extension_lsdb_v3.is_modified.is_set())
        self.extension_lsdb_v3.is_modified.clear()
        self.extension_lsdb_v3.delete_extension_lsa(conf.LSA_TYPE_EXTENSION_ABR_LSA, 0, ADVERTISING_ROUTER)
        self.assertEqual(1, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertFalse(self.extension_lsdb_v3.is_modified.is_set())
        self.extension_lsdb_v3.delete_extension_lsa(conf.LSA_TYPE_EXTENSION_PREFIX_LSA, 0, ADVERTISING_ROUTER)
        self.assertEqual(0, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertTrue(self.extension_lsdb_v3.is_modified.is_set())
        self.extension_lsdb_v3.is_modified.clear()

        #  Clean LSDB

        self.populate_lsdb()

        self.extension_lsdb_v2.clean_extension_lsdb()
        self.assertEqual(0, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertTrue(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v3.clean_extension_lsdb()
        self.assertEqual(0, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertTrue(self.extension_lsdb_v3.is_modified.is_set())

    #  Successful run - Instant
    def test_add_lsa(self):

        #  OSPFv2

        new_lsa_v2_1 = lsa.Lsa()
        new_lsa_v2_1.create_extension_header(conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.OPAQUE_TYPE_ABR_LSA, 0,
                                             ADVERTISING_ROUTER, conf.INITIAL_SEQUENCE_NUMBER + 1, conf.VERSION_IPV4)
        new_lsa_v2_1.create_extension_abr_lsa_body()
        new_lsa_v2_2 = lsa.Lsa()
        new_lsa_v2_2.create_extension_header(conf.INITIAL_LS_AGE, conf.OPTIONS_V2, conf.OPAQUE_TYPE_PREFIX_LSA, 0,
                                             ADVERTISING_ROUTER, conf.INITIAL_SEQUENCE_NUMBER + 1, conf.VERSION_IPV4)
        new_lsa_v2_2.create_extension_prefix_lsa_body(conf.VERSION_IPV4)

        self.extension_lsdb_v2.add_extension_lsa(self.abr_lsa_v2)
        self.assertEqual(1, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, self.extension_lsdb_v2.get_extension_lsdb(None)[0].header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_ABR_LSA, self.extension_lsdb_v2.get_extension_lsdb(None)[0].get_opaque_type())
        self.assertEqual(conf.INITIAL_SEQUENCE_NUMBER,
                         self.extension_lsdb_v2.get_extension_lsdb(None)[0].header.ls_sequence_number)
        self.assertTrue(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v2.is_modified.clear()

        self.extension_lsdb_v2.add_extension_lsa(new_lsa_v2_1)
        self.assertEqual(1, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, self.extension_lsdb_v2.get_extension_lsdb(None)[0].header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_ABR_LSA, self.extension_lsdb_v2.get_extension_lsdb(None)[0].get_opaque_type())
        self.assertEqual(conf.INITIAL_SEQUENCE_NUMBER + 1,
                         self.extension_lsdb_v2.get_extension_lsdb(None)[0].header.ls_sequence_number)
        self.assertTrue(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v2.is_modified.clear()

        self.extension_lsdb_v2.add_extension_lsa(new_lsa_v2_2)
        self.assertEqual(2, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, self.extension_lsdb_v2.get_extension_lsdb(None)[1].header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_PREFIX_LSA,
                         self.extension_lsdb_v2.get_extension_lsdb(None)[1].get_opaque_type())
        self.assertEqual(conf.INITIAL_SEQUENCE_NUMBER + 1,
                         self.extension_lsdb_v2.get_extension_lsdb(None)[1].header.ls_sequence_number)
        self.assertTrue(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v2.is_modified.clear()

        self.extension_lsdb_v2.add_extension_lsa(self.prefix_lsa_v2)
        self.assertEqual(2, len(self.extension_lsdb_v2.get_extension_lsdb(None)))
        self.assertEqual(conf.LSA_TYPE_OPAQUE_AS, self.extension_lsdb_v2.get_extension_lsdb(None)[1].header.ls_type)
        self.assertEqual(conf.OPAQUE_TYPE_PREFIX_LSA,
                         self.extension_lsdb_v2.get_extension_lsdb(None)[1].get_opaque_type())
        self.assertEqual(conf.INITIAL_SEQUENCE_NUMBER,
                         self.extension_lsdb_v2.get_extension_lsdb(None)[1].header.ls_sequence_number)
        self.assertTrue(self.extension_lsdb_v2.is_modified.is_set())
        self.extension_lsdb_v2.is_modified.clear()

        #  OSPFv3

        new_lsa_v3_1 = lsa.Lsa()
        new_lsa_v3_1.create_extension_header(conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, conf.LSA_TYPE_EXTENSION_ABR_LSA,
                                             ADVERTISING_ROUTER, conf.INITIAL_SEQUENCE_NUMBER + 1, conf.VERSION_IPV6)
        new_lsa_v3_1.create_extension_abr_lsa_body()
        new_lsa_v3_2 = lsa.Lsa()
        new_lsa_v3_2.create_extension_header(
            conf.INITIAL_LS_AGE, conf.OPTIONS_V3, 0, conf.LSA_TYPE_EXTENSION_PREFIX_LSA, ADVERTISING_ROUTER,
            conf.INITIAL_SEQUENCE_NUMBER + 1, conf.VERSION_IPV6)
        new_lsa_v3_2.create_extension_prefix_lsa_body(conf.VERSION_IPV6)

        self.extension_lsdb_v3.add_extension_lsa(self.abr_lsa_v3)
        self.assertEqual(1, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[0].header.ls_type)
        self.assertEqual(conf.INITIAL_SEQUENCE_NUMBER,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[0].header.ls_sequence_number)
        self.assertTrue(self.extension_lsdb_v3.is_modified.is_set())
        self.extension_lsdb_v3.is_modified.clear()

        self.extension_lsdb_v3.add_extension_lsa(new_lsa_v3_1)
        self.assertEqual(1, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_ABR_LSA,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[0].header.ls_type)
        self.assertEqual(conf.INITIAL_SEQUENCE_NUMBER + 1,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[0].header.ls_sequence_number)
        self.assertTrue(self.extension_lsdb_v3.is_modified.is_set())
        self.extension_lsdb_v3.is_modified.clear()

        self.extension_lsdb_v3.add_extension_lsa(new_lsa_v3_2)
        self.assertEqual(2, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[1].header.ls_type)
        self.assertEqual(conf.INITIAL_SEQUENCE_NUMBER + 1,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[1].header.ls_sequence_number)
        self.assertTrue(self.extension_lsdb_v3.is_modified.is_set())
        self.extension_lsdb_v3.is_modified.clear()

        self.extension_lsdb_v3.add_extension_lsa(self.prefix_lsa_v3)
        self.assertEqual(2, len(self.extension_lsdb_v3.get_extension_lsdb(None)))
        self.assertEqual(BITS_U_S1_S2 + conf.LSA_TYPE_EXTENSION_PREFIX_LSA,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[1].header.ls_type)
        self.assertEqual(conf.INITIAL_SEQUENCE_NUMBER,
                         self.extension_lsdb_v3.get_extension_lsdb(None)[1].header.ls_sequence_number)
        self.assertTrue(self.extension_lsdb_v3.is_modified.is_set())
        self.extension_lsdb_v3.is_modified.clear()

    #  Successful run - 2 s
    def test_increase_lsa_age(self):
        self.populate_lsdb()
        lsdb_list = [self.extension_lsdb_v2, self.extension_lsdb_v3]
        for query_lsdb in lsdb_list:
            for query_lsa in query_lsdb.get_extension_lsdb(None):
                self.assertEqual(0, query_lsa.header.ls_age)
        for query_lsdb in lsdb_list:
            query_lsdb.increase_lsa_age()
            for query_lsa in query_lsdb.get_extension_lsdb(None):
                self.assertEqual(0, query_lsa.header.ls_age)
        time.sleep(1.1)
        for query_lsdb in lsdb_list:
            query_lsdb.increase_lsa_age()
            for query_lsa in query_lsdb.get_extension_lsdb(None):
                self.assertEqual(1, query_lsa.header.ls_age)
        time.sleep(1.1)
        for query_lsdb in lsdb_list:
            query_lsdb.increase_lsa_age()
            for query_lsa in query_lsdb.get_extension_lsdb(None):
                self.assertEqual(2, query_lsa.header.ls_age)

    def populate_lsdb(self):
        self.extension_lsdb_v2.abr_lsa_list.append(self.abr_lsa_v2)
        self.extension_lsdb_v2.prefix_lsa_list.append(self.prefix_lsa_v2)
        self.extension_lsdb_v3.abr_lsa_list.append(self.abr_lsa_v3)
        self.extension_lsdb_v3.prefix_lsa_list.append(self.prefix_lsa_v3)


if __name__ == '__main__':
    unittest.main()
