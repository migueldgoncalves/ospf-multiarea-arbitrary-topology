import struct

import lsa.body as body
import general.utils as utils
import conf.conf as conf

'''
This class represents the body of an OSPFv2 Summary-LSA and contains its operations
LSA structure is the same for both Type 3 Summary-LSA (Network-Summary) and Type 4 Summary-LSA (ASBR-Summary)
'''

#  > - Big-endian
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
FORMAT_STRING = "> L L L"  # Determines the format of the byte object to be created


class Summary(body.Body):  # 12 bytes

    def __init__(self, network_mask, metric):
        is_valid, message = self.parameter_validation(network_mask, metric)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)

        self.network_mask = network_mask  # 4 bytes
        self.metric = metric  # 3 bytes

    #  Creates byte object suitable to be sent and recognized as the body of an OSPFv2 Summary-LSA
    def pack_lsa_body(self):
        #  Last 4 bytes in Summary-LSA are for TOS-specific information, here set to 0
        return struct.pack(FORMAT_STRING, utils.Utils.ipv4_to_decimal(self.network_mask), self.metric, 0)

    #  Converts byte stream to body of an OSPFv2 Summary-LSA
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        network_mask = utils.Utils.decimal_to_ipv4(struct.unpack(FORMAT_STRING, body_bytes)[0])
        metric = struct.unpack(FORMAT_STRING, body_bytes)[1]
        return Summary(network_mask, metric)

    #  Validates constructor parameters - Returns error message in case of failed validation
    @staticmethod
    def parameter_validation(network_mask, metric):
        try:
            if not utils.Utils.is_ipv4_address(network_mask):
                return False, "Invalid Network Mask"
            if not 0 <= metric <= conf.MAX_VALUE_24_BITS:
                return False, "Invalid Metric"
            return True, ''  # No error message to return
        except (ValueError, TypeError):
            return False, "Invalid parameter type"

    def __str__(self):
        return str({'Network Mask': self.network_mask, 'Metric': self.metric})
