import struct

import packet.body as body
import conf.conf as conf
import general.utils as utils

'''
This class represents the body of an OSPF Link State Request packet and contains its operations
'''

#  > - Big-endian
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
FORMAT_STRING = "> L L L"  # Determines the format of the byte object to be created


class LSRequest(body.Body):  # OSPFv2 and OSPFv3 - 12 bytes / LSA identifier

    def __init__(self, version):
        self.lsa_identifiers = []  # 12 bytes / LSA identifier
        self.version = version

    #  Adds data for one LSA identifier to the packet
    def add_lsa_info(self, ls_type, link_state_id, advertising_router):
        #  TODO: COnsider other types of LSAs
        if (self.version == conf.VERSION_IPV6) & (ls_type != conf.LSA_TYPE_LINK) & (ls_type < 0x2000):
            ls_type += 0x2000
        self.lsa_identifiers.append([ls_type, link_state_id, advertising_router])

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Link State Request packet
    def pack_packet_body(self):
        body_bytes = b''
        for i in self.lsa_identifiers:
            ls_type = i[0]
            decimal_link_state_id = utils.Utils.ipv4_to_decimal(i[1])
            decimal_advertising_router = utils.Utils.ipv4_to_decimal(i[2])
            body_bytes += struct.pack(FORMAT_STRING, ls_type, decimal_link_state_id, decimal_advertising_router)
        return body_bytes

    #  Converts byte stream to body of an OSPF Link State Request packet
    @staticmethod
    def unpack_packet_body(body_bytes, version):
        new_packet = LSRequest(version)
        for i in range(len(body_bytes) // 12):
            body_tuple = struct.unpack(FORMAT_STRING, body_bytes[i*12:(i+1)*12])
            ls_type = body_tuple[0]
            link_state_id = utils.Utils.decimal_to_ipv4(body_tuple[1])
            advertising_router = utils.Utils.decimal_to_ipv4(body_tuple[2])
            new_packet.add_lsa_info(ls_type, link_state_id, advertising_router)
        return new_packet
