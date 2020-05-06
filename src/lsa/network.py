import struct

import lsa.body as body
import conf.conf as conf
import general.utils as utils

'''
This class represents the body of an OSPF Network-LSA and contains its operations
'''

#  > - Big-endian
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
FORMAT_STRING = "> L"


class Network(body.Body):  # OSPFv2 and OSPFv3 - 4 bytes + 4 bytes / link

    def __init__(self, network_mask, options, attached_routers, version):
        self.network_mask = network_mask  # 4 bytes - Only for OSPFv2
        self.options = options  # 3 bytes - Only for OSPFv3
        self.attached_routers = attached_routers  # 4 bytes / router
        self.version = version

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Network-LSA
    def pack_lsa_body(self):
        if self.version == conf.VERSION_IPV4:
            decimal_network_mask = utils.Utils.ipv4_to_decimal(self.network_mask)
            body_bytes = struct.pack(FORMAT_STRING, decimal_network_mask)
        else:
            body_bytes = struct.pack(FORMAT_STRING, self.options)
        for r in self.attached_routers:
            body_bytes += struct.pack(FORMAT_STRING, utils.Utils.ipv4_to_decimal(r))
        return body_bytes

    #  Converts byte stream to body of an OSPF Network-LSA
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        first_field = struct.unpack(FORMAT_STRING, body_bytes[:4])[0]
        if version == conf.VERSION_IPV4:
            first_field = utils.Utils.decimal_to_ipv4(first_field)
        attached_routers = []
        for i in range(len(body_bytes[4:]) // 4):
            attached_router_ip = struct.unpack(FORMAT_STRING, body_bytes[4*i+4:4*(i+1)+4])[0]
            attached_routers.append(utils.Utils.decimal_to_ipv4(attached_router_ip))
        if version == conf.VERSION_IPV4:
            return Network(first_field, 0, attached_routers, conf.VERSION_IPV4)
        else:
            return Network(0, first_field, attached_routers, conf.VERSION_IPV6)
