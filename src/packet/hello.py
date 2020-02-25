import struct

import general.utils as utils
import conf.conf as conf

'''
This class represents the body of an OSPF Hello packet and contains its operations
'''

#  > - Big-endian
#  B - Unsigned char (1 byte) - struct.pack("> B", 1) -> b'\x01
#  H - Unsigned short (2 bytes) - struct.pack("> H", 1) -> b'\x00\x01
#  L - Unsigned long (4 bytes) - struct.pack("> L", 1) -> b'\x00\x00\x00\x01
OSPFV2_BASE_FORMAT_STRING = "> L H B B L L L"  # Determines the format of the byte object to be created
OSPFV3_BASE_FORMAT_STRING = "> L L H H L L"
EXTRA_FORMAT_STRING = " L"  # Must be added to the base format string for every neighbor, for every OSPF version


class Hello:

    utils = utils.Utils()

    interface_id = 0  # 4 bytes - Only for OSPFv3
    network_mask = ''  # 4 bytes - Only for OSPFv2
    hello_interval = 0  # 2 bytes
    options = 0  # 1 byte in OSPFv2, 3 bytes in OSPFv3
    router_priority = 0  # 1 byte
    router_dead_interval = 0  # 4 bytes in OSPFv2, 2 bytes in OSPFv3
    designated_router = ''  # 4 bytes
    backup_designated_router = ''  # 4 bytes
    neighbors = ()  # 4 bytes / neighbor

    def __init__(self, network_mask, hello_interval, options, router_priority, router_dead_interval,
                 designated_router, backup_designated_router, neighbors):
        is_valid, message = self.parameter_validation(
            network_mask, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)

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

        base_packed_data = struct.pack(OSPFV2_BASE_FORMAT_STRING, decimal_network_mask, self.hello_interval, self.options,
                                       self.router_priority, self.router_dead_interval, decimal_designated_router,
                                       decimal_backup_designated_router)

        packed_data = base_packed_data
        #  Adds neighbors one by one to the Hello packet
        for n in self.neighbors:
            decimal_neighbor = self.utils.ipv4_to_decimal(n)
            extra_packed_data = struct.pack(">" + EXTRA_FORMAT_STRING, decimal_neighbor)
            packed_data += extra_packed_data
        return packed_data

    @staticmethod
    def get_format_string(neighbor_number):
        format_string = OSPFV2_BASE_FORMAT_STRING
        #  Format string must receive 1 parameter for every new neighbor in the packet
        for _ in range(neighbor_number):
            format_string += EXTRA_FORMAT_STRING
        return format_string[2:]

    #  Validates constructor parameters - Returns error message in case of failed validation
    def parameter_validation(self, network_mask, hello_interval, options, router_priority, router_dead_interval,
                             designated_router, backup_designated_router, neighbors):
        try:
            if not self.utils.is_ipv4_network_mask(network_mask):
                return False, "Invalid network mask"
            if not (0 <= hello_interval <= conf.MAX_VALUE_16_BITS):
                return False, "Invalid Hello interval"
            if not (0 <= options <= conf.MAX_VALUE_8_BITS):
                return False, "Invalid packet options"
            if not (0 <= router_priority <= conf.MAX_VALUE_8_BITS):
                return False, "Invalid router priority"
            if not (0 <= router_dead_interval <= conf.MAX_VALUE_32_BITS):
                return False, "Invalid router dead interval"
            if not self.utils.is_ipv4_address(designated_router):
                return False, "Invalid Designated Router"
            if not self.utils.is_ipv4_address(backup_designated_router):
                return False, "Invalid Backup Designated Router"
            if len(neighbors) > 0:
                for neighbor_id in neighbors:
                    if not self.utils.is_ipv4_address(neighbor_id):
                        return False, "Invalid Neighbor(s)"
            return True, ''  # No error message to return
        except (ValueError, TypeError):
            return False, "Invalid parameter type"
