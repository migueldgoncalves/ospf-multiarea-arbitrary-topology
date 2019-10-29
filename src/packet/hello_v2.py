import struct

import general.utils as utils

'''
This class represents the body of an OSPFv2 Hello packet and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
BASE_FORMAT_STRING = "> L H B B L L L"  # Determines the format of the byte object to be created
EXTRA_FORMAT_STRING = " L"  # Must be added to the base format string for every neighbor


class HelloV2:

    utils = utils.Utils()

    network_mask = ''  # 4 bytes
    hello_interval = 0  # 2 bytes
    options = 0  # 1 byte
    router_priority = 0  # 1 byte
    router_dead_interval = 0  # 4 bytes
    designated_router = ''  # 4 bytes
    backup_designated_router = ''  # 4 bytes
    neighbors = ()  # 4 bytes / neighbor

    def __init__(self, network_mask, hello_interval, options, router_priority, router_dead_interval,
                 designated_router, backup_designated_router, neighbors):
        self.network_mask = network_mask
        self.hello_interval = hello_interval
        self.options = options
        self.router_priority = router_priority
        self.router_dead_interval = router_dead_interval
        self.designated_router = designated_router
        self.backup_designated_router = backup_designated_router
        self.neighbors = neighbors

    #  Converts set of parameters to byte object suitable to be sent and recognized as the body of an OSPF Hello packet
    def pack_packet(self):
        decimal_network_mask = self.utils.ipv4_to_decimal(self.network_mask)
        decimal_designated_router = self.utils.ipv4_to_decimal(self.designated_router)
        decimal_backup_designated_router = self.utils.ipv4_to_decimal(self.backup_designated_router)

        base_packed_data = struct.pack(BASE_FORMAT_STRING, decimal_network_mask, self.hello_interval, self.options,
                                       self.router_priority, self.router_dead_interval, decimal_designated_router,
                                       decimal_backup_designated_router)

        packed_data = base_packed_data
        #  Adds neighbors one by one to the Hello packet
        for n in self.neighbors:
            decimal_neighbor = self.utils.ipv4_to_decimal(n)
            extra_packed_data = struct.pack(">" + EXTRA_FORMAT_STRING, decimal_neighbor)
            packed_data += extra_packed_data
        return packed_data

    def get_format_string(self):
        format_string = BASE_FORMAT_STRING
        #  Format string must receive 1 parameter for every new neighbor in the packet
        for n in self.neighbors:
            format_string += EXTRA_FORMAT_STRING
        return format_string[1:]  # Removes the first char -> ">"
