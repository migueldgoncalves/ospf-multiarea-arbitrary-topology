import struct

import packet.body as body
import lsa.lsa as lsa

'''
This class represents the body of an OSPF Link State Update packet and contains its operations
'''

#  > - Big-endian
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
FORMAT_STRING = "> L"  # Determines the format of the byte object to be created


class LSUpdate(body.Body):  # OSPFv2 and OSPFv3 - 4 bytes + 20+ bytes / LSA

    lsa_number = 0  # 4 bytes
    lsa_list = []  # 20+ bytes / LSA
    version = 0

    def __init__(self, version):
        self.lsa_number = 0
        self.lsa_list = []
        self.version = version

    #  Adds one full LSA to the packet
    def add_lsa(self, new_lsa):
        self.lsa_number += 1
        self.lsa_list.append(new_lsa)

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Link State Update packet
    def pack_packet_body(self):
        body_bytes = struct.pack(FORMAT_STRING, self.lsa_number)
        for i in self.lsa_list:
            body_bytes += i.pack_lsa()
        return body_bytes

    #  Converts byte stream to body of an OSPF Link State Update packet
    @staticmethod
    def unpack_packet_body(body_bytes, version):
        new_packet = LSUpdate(version)
        body_bytes = body_bytes[4:]  # Extracting the LSAs
        while len(body_bytes) > 0:
            ls_length = lsa.Lsa.get_ospf_lsa_length(body_bytes)
            new_lsa = lsa.Lsa.unpack_lsa(body_bytes[:ls_length], version)
            new_packet.add_lsa(new_lsa)
            body_bytes = body_bytes[ls_length:]
        return new_packet
