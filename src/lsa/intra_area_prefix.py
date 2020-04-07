import struct

import lsa.body as body

'''
This class represents the body of an OSPF Intra-Area-Prefix-LSA and contains its operations
'''


class IntraAreaPrefix(body.Body):

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Intra-Area-Prefix-LSA
    def pack_lsa_body(self):
        pass

    #  Converts byte stream to body of an OSPF Intra-Area-Prefix-LSA
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        pass

#  If length == 0
#  no field for address prefix
#  If length > 0
#  field can have 1, 2, 3 or 4 32-bit words
#  1 bit -> 1 word
#  32 bits -> 1 word
#  33 bits -> 2 words
#  64 bits -> 2 words
#  65 bits -> 3 words
#  96 bits -> 3 words
#  97 bits -> 4 words
#  128 bits -> 4 words
#  < 32 bits - Shift left until address has 32 bits, then packed in 4 bytes
#  32 bits - Packed in 4 bytes
#  32 < length < 64 bits - Shift left until address has 64 bits, then packed in 8 bytes
#  64 bits - Packed in 8 bytes
#  64 < length < 96 bits - Shift left until address has 96 bits, split, first 64 bits packed in 8 bytes, last bit(s) packed in 4 bytes, then bytes are joined together
#  96 bits - Split, first 64 bits packed in 8 bytes, last 32 bits packed in 4 bytes, then bytes are joined together
#  96 < length < 128 bits - Shift left until address has 128 bits, split, first 64 bits packed in 8 bytes, last bit packed in 8 bytes, then bytes are joined together
#  If address has 128 bits - Split, first 64 bits packed in 8 bytes, last 64 bits packed in 8 bytes, then bytes are joined together

#  When packing LSA
#  Prefix length will be obtained from method to be created in utils
#  When unpacking LSA
#  Prefix length will be obtained from field in LSA bytes

#  Pack in 4 or 8 bytes - Direct
#  To shift - Prefix must be converted to int - Already possible using utils
#  Split the address
#  Left side - Shift right until only first 8 bytes remain
#  Right side - Shift left until prefix fills 96 or 128 bits, then XOR with 255 or 65535 respectively
#  Join bytes together - b'\x00 + b'\x01' = b'\x00\x01'
