import struct

import lsa.body as body
import conf.conf as conf
import general.utils as utils

'''
This class represents the body of an OSPF Router-LSA and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
BASE_FORMAT_STRING = "> L"  # Determines the format of the byte object to be created
OSPFV2_LINK_FORMAT_STRING = "> L L B B H"
OSPFV3_LINK_FORMAT_STRING = "> L L L L"


class Router(body.Body):  # OSPFv2 - 4 bytes + 12 bytes / link; OSPFv3 - 4 bytes + 16 bytes / link

    def __init__(self, bit_v, bit_e, bit_b, options, version):
        self.bit_v = bit_v  # Virtual link endpoint bit
        self.bit_e = bit_e  # AS boundary router bit
        self.bit_b = bit_b  # Area border router bit
        self.link_number = 0  # 2 bytes - Just for OSPFv2
        self.options = options  # 3 bytes - Just for OSPFv3
        self.links = []  # 12 bytes/link in OSPFv2; 16 bytes / link in OSPFv3
        self.version = version

    #  Adds data for one link (interface) to the OSPFv2 LSA body
    def add_link_info_v2(self, link_id, link_data, link_type, tos_number, metric):
        new_link = [link_id, link_data, link_type, tos_number, metric]
        if (self.version == conf.VERSION_IPV4) & (new_link not in self.links):
            self.links.append(new_link)
            self.link_number += 1

    #  Adds data for one link (interface) to the OSPFv3 LSA body
    def add_link_info_v3(self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id):
        new_link = [link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id]
        if (self.version == conf.VERSION_IPV6) & (new_link not in self.links):
            self.links.append(new_link)

    def has_link_info_v2(self, link_id, link_data, link_type, tos_number, metric):
        return [link_id, link_data, link_type, tos_number, metric] in self.links

    def has_link_info_v3(self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id):
        return [link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id] in self.links

    #  Deletes all link information produced by provided interface
    def delete_interface_link_info(self, interface_ip, subnet_ip, interface_id):
        remaining_links = []
        for info in self.links:
            if (interface_ip in [info[0], info[1]]) | (subnet_ip in [info[0], info[1]]) | (interface_id == info[2]):
                pass  # Link information produced by current interface matching desired type(s)
            else:
                remaining_links.append(info)
        self.links = remaining_links
        self.link_number = len(self.links)

    #  Deletes data for one link from the OSPFv2 LSA body
    def delete_link_info_v2(self, link_id, link_data, link_type, tos_number, metric):
        if [link_id, link_data, link_type, tos_number, metric] in self.links:
            self.links.remove([link_id, link_data, link_type, tos_number, metric])

    #  Deletes data for one link from the OSPFv3 LSA body
    def delete_link_info_v3(self, link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id):
        if [link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id] in self.links:
            self.links.remove([link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id])

    #  Creates byte object suitable to be sent and recognized as the body of an OSPF Router-LSA
    def pack_lsa_body(self):
        flags_byte = (self.bit_v << 2) + (self.bit_e << 1) + self.bit_b
        if self.version == conf.VERSION_IPV6:
            flags_byte << 1

        if self.version == conf.VERSION_IPV4:
            body_bytes = struct.pack(BASE_FORMAT_STRING, (flags_byte << 3 * conf.BYTE_SIZE) + self.link_number)
            for link in self.links:
                decimal_link_id = utils.Utils.ipv4_to_decimal(link[0])
                decimal_link_data = utils.Utils.ipv4_to_decimal(link[1])
                link_type = link[2]
                tos_number = link[3]
                metric = link[4]
                body_bytes += struct.pack(
                    OSPFV2_LINK_FORMAT_STRING, decimal_link_id, decimal_link_data, link_type, tos_number, metric)
        else:
            body_bytes = struct.pack(BASE_FORMAT_STRING, (flags_byte << 3 * conf.BYTE_SIZE) + self.options)
            for link in self.links:
                link_type = link[0]
                metric = link[1]
                interface_id = link[2]
                neighbor_interface_id = link[3]
                decimal_neighbor_router_id = utils.Utils.ipv4_to_decimal(link[4])
                body_bytes += struct.pack(OSPFV3_LINK_FORMAT_STRING, (link_type << 3 * conf.BYTE_SIZE) + metric,
                                          interface_id, neighbor_interface_id, decimal_neighbor_router_id)
        return body_bytes

    #  Converts byte stream to body of an OSPF Router-LSA
    @staticmethod
    def unpack_lsa_body(body_bytes, version):
        body_tuple = struct.unpack(BASE_FORMAT_STRING, body_bytes[:4])
        flags_byte = body_tuple[0] >> 3 * conf.BYTE_SIZE
        bit_v = (flags_byte >> 2) & 1
        bit_e = (flags_byte >> 1) & 1
        bit_b = flags_byte & 1
        if version == conf.VERSION_IPV4:
            unpacked_body = Router(bit_v, bit_e, bit_b, 0, conf.VERSION_IPV4)
            for i in range(len(body_bytes[4:]) // 12):
                body_tuple = struct.unpack(OSPFV2_LINK_FORMAT_STRING, body_bytes[12*i+4:12*(i+1)+4])
                link_id = utils.Utils.decimal_to_ipv4(body_tuple[0])
                link_data = utils.Utils.decimal_to_ipv4(body_tuple[1])
                link_type = body_tuple[2]
                tos_number = body_tuple[3]
                metric = body_tuple[4]
                unpacked_body.add_link_info_v2(link_id, link_data, link_type, tos_number, metric)
        else:
            options = body_tuple[0] & conf.MAX_VALUE_24_BITS
            unpacked_body = Router(bit_v, bit_e, bit_b, options, conf.VERSION_IPV6)
            for i in range(len(body_bytes[4:]) // 16):
                body_tuple = struct.unpack(OSPFV3_LINK_FORMAT_STRING, body_bytes[16*i+4:16*(i+1)+4])
                link_type = body_tuple[0] >> 3 * conf.BYTE_SIZE
                metric = body_tuple[0] & conf.MAX_VALUE_16_BITS
                interface_id = body_tuple[1]
                neighbor_interface_id = body_tuple[2]
                neighbor_router_id = utils.Utils.decimal_to_ipv4(body_tuple[3])
                unpacked_body.add_link_info_v3(
                    link_type, metric, interface_id, neighbor_interface_id, neighbor_router_id)
        return unpacked_body

    #  Validates constructor parameters - Returns error message in case of failed validation
    @staticmethod
    def parameter_validation(version):
        try:
            if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
                return False, "Invalid OSPF version"
            return True, ''  # No error message to return
        except (ValueError, TypeError, AttributeError):
            return False, "Invalid parameter type"

    def __str__(self):
        return str({'V-bit': self.bit_v, 'E-bit': self.bit_e, 'B-bit': self.bit_b, 'Link Number': self.link_number,
                    'Options': self.options, 'Links': self.links, 'Version': self.version})
