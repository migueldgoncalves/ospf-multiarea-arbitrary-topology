import unittest

import lsa.summary as summary

'''
This class tests the OSPFv2 Summary-LSAs body class and its operations
'''


#  Full successful run - Instant
class TestSummary(unittest.TestCase):

    body_bytes = b'\xff\xff\xff\x00\x00\x00\x00\n'
    network_mask = '255.255.255.0'
    metric = 10

    #  Successful run - Instant
    def test_pack_body(self):
        self.assertEqual(TestSummary.body_bytes, summary.Summary(
            TestSummary.network_mask, TestSummary.metric).pack_lsa_body())

    #  Successful run - Instant
    def test_unpack_body(self):
        unpacked_body = summary.Summary.unpack_lsa_body(TestSummary.body_bytes, 0)
        self.assertEqual(TestSummary.network_mask, unpacked_body.network_mask)
        self.assertEqual(TestSummary.metric, unpacked_body.metric)
