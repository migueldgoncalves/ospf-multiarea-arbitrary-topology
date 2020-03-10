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


class Hello:  # OSPFv2 and OSPFv3 - 20 bytes + 4 bytes / neighbor

    utils = utils.Utils()

    interface_id = 0  # 4 bytes - Only for OSPFv3
    network_mask = '0.0.0.0'  # 4 bytes - Only for OSPFv2
    hello_interval = 0  # 2 bytes
    options = 0  # 1 byte in OSPFv2, 3 bytes in OSPFv3
    router_priority = 0  # 1 byte
    router_dead_interval = 0  # 4 bytes in OSPFv2, 2 bytes in OSPFv3
    designated_router = '0.0.0.0'  # 4 bytes
    backup_designated_router = '0.0.0.0'  # 4 bytes
    neighbors = ()  # 4 bytes / neighbor

    version = 0

    def __init__(self, network_mask, hello_interval, options, router_priority, router_dead_interval,
                 designated_router, backup_designated_router, neighbors, interface_id, version):
        is_valid, message = self.parameter_validation(
            network_mask, hello_interval, options, router_priority, router_dead_interval, designated_router,
            backup_designated_router, neighbors, interface_id, version)
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
        self.interface_id = interface_id
        self.version = version

    #  Converts set of parameters to byte object suitable to be sent and recognized as the body of an OSPF Hello packet
    def pack_packet_body(self):
        decimal_designated_router = self.utils.ipv4_to_decimal(self.designated_router)
        decimal_backup_designated_router = self.utils.ipv4_to_decimal(self.backup_designated_router)

        if self.version == conf.VERSION_IPV4:
            decimal_network_mask = self.utils.ipv4_to_decimal(self.network_mask)
            base_packed_data = struct.pack(
                OSPFV2_BASE_FORMAT_STRING, decimal_network_mask, self.hello_interval, self.options,
                self.router_priority, self.router_dead_interval, decimal_designated_router,
                decimal_backup_designated_router)
        else:
            decimal_interface_id = self.utils.ipv4_to_decimal(self.interface_id)
            base_packed_data = struct.pack(
                OSPFV3_BASE_FORMAT_STRING, decimal_interface_id, (self.router_priority << 3 * conf.BYTE_SIZE) +
                self.options, self.hello_interval, self.router_dead_interval, decimal_designated_router,
                decimal_backup_designated_router)

        packed_data = base_packed_data
        #  Adds neighbors one by one to the Hello packet
        for n in self.neighbors:
            decimal_neighbor = self.utils.ipv4_to_decimal(n)
            extra_packed_data = struct.pack(">" + EXTRA_FORMAT_STRING, decimal_neighbor)
            packed_data += extra_packed_data
        return packed_data

    #  Converts byte stream to body of an OSPF Hello packet
    @staticmethod
    def unpack_packet_body(body_bytes, version):
        neighbor_number = Hello.get_hello_packet_neighbor_number(body_bytes)
        format_string = Hello.get_format_string(neighbor_number, version)
        body_tuple = struct.unpack(format_string, body_bytes)

        network_mask = ''
        interface_id = 0
        neighbors = ()
        if version == conf.VERSION_IPV4:
            network_mask = utils.Utils.decimal_to_ipv4(body_tuple[0])
            hello_interval = body_tuple[1]
            options = body_tuple[2]
            router_priority = body_tuple[3]
            router_dead_interval = body_tuple[4]
            designated_router = utils.Utils.decimal_to_ipv4(body_tuple[5])
            backup_designated_router = utils.Utils.decimal_to_ipv4(body_tuple[6])
            if neighbor_number > 0:
                neighbors = Hello.get_hello_packet_neighbors(body_tuple[7:])
        else:
            interface_id = body_tuple[0]
            router_priority = body_tuple[1] >> (3 * conf.BYTE_SIZE)  # Router priority and options in same 4-byte word
            options = body_tuple[1] % (conf.MAX_VALUE_24_BITS + 1)
            hello_interval = body_tuple[2]
            router_dead_interval = body_tuple[3]
            designated_router = utils.Utils.decimal_to_ipv4(body_tuple[4])
            backup_designated_router = utils.Utils.decimal_to_ipv4(body_tuple[5])
            if neighbor_number > 0:
                neighbors = Hello.get_hello_packet_neighbors(body_tuple[6:])

        if version == conf.VERSION_IPV4:
            return Hello(network_mask, hello_interval, options, router_priority, router_dead_interval,
                         designated_router, backup_designated_router, neighbors, 0, version)
        else:
            return Hello('', hello_interval, options, router_priority, router_dead_interval, designated_router,
                         backup_designated_router, neighbors, interface_id, version)

    @staticmethod
    def get_format_string(neighbor_number, version):
        if version == conf.VERSION_IPV4:
            format_string = OSPFV2_BASE_FORMAT_STRING
        elif version == conf.VERSION_IPV6:
            format_string = OSPFV3_BASE_FORMAT_STRING
        else:
            raise ValueError("Invalid OSPF version")
        #  Format string must receive 1 parameter for every new neighbor in the packet
        if neighbor_number < 0:
            raise ValueError("Invalid neighbor number")
        for _ in range(neighbor_number):
            format_string += EXTRA_FORMAT_STRING
        return format_string

    #  Given the body of an OSPF Hello packet as a byte stream, returns the number of its neighbors
    @staticmethod
    def get_hello_packet_neighbor_number(body_bytes):
        hello_body_base_length = conf.OSPFV2_BASE_HELLO_LENGTH - conf.OSPFV2_HEADER_LENGTH
        if len(body_bytes) < hello_body_base_length:
            raise ValueError("Invalid Hello packet body")
        neighbor_number = int((len(body_bytes) - hello_body_base_length) / conf.HELLO_NEIGHBOR_LENGTH)
        return neighbor_number

    #  Given a tuple with the neighbors of an OSPF Hello packet as integers, returns them as OSPF RIDs
    @staticmethod
    def get_hello_packet_neighbors(packet_tuple):
        neighbors = []
        for i in range(len(packet_tuple)):
            neighbor_decimal = packet_tuple[i]
            neighbor_ip = utils.Utils.decimal_to_ipv4(neighbor_decimal)
            neighbors.append(neighbor_ip)
        return tuple(neighbors)

    #  Validates constructor parameters - Returns error message in case of failed validation
    def parameter_validation(self, network_mask, hello_interval, options, router_priority, router_dead_interval,
                             designated_router, backup_designated_router, neighbors, interface_id, version):
        try:
            if (not self.utils.is_ipv4_network_mask(network_mask)) & (version == conf.VERSION_IPV4):
                return False, "Invalid network mask"
            if not (0 <= hello_interval <= conf.MAX_VALUE_16_BITS):
                return False, "Invalid Hello interval"
            if (not (0 <= options <= conf.MAX_VALUE_8_BITS)) & (version == conf.VERSION_IPV4):  # OSPFv2
                return False, "Invalid packet options"
            if (not (0 <= options <= conf.MAX_VALUE_24_BITS)) & (version == conf.VERSION_IPV6):  # OSPFv3
                return False, "Invalid packet options"
            if not (0 <= router_priority <= conf.MAX_VALUE_8_BITS):
                return False, "Invalid router priority"
            if (not (0 <= router_dead_interval <= conf.MAX_VALUE_32_BITS)) & (version == conf.VERSION_IPV4):  # OSPFv2
                return False, "Invalid router dead interval"
            if (not (0 <= router_dead_interval <= conf.MAX_VALUE_16_BITS)) & (version == conf.VERSION_IPV6):  # OSPFv3
                return False, "Invalid router dead interval"
            if not self.utils.is_ipv4_address(designated_router):
                return False, "Invalid Designated Router"
            if not self.utils.is_ipv4_address(backup_designated_router):
                return False, "Invalid Backup Designated Router"
            if len(neighbors) > 0:
                for neighbor_id in neighbors:
                    if not self.utils.is_ipv4_address(neighbor_id):
                        return False, "Invalid Neighbor(s)"
            if (not (0 <= interface_id <= conf.MAX_VALUE_32_BITS)) & (version == conf.VERSION_IPV6):
                return False, "Invalid interface ID"
            if version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
                return False, "Invalid OSPF version"
            return True, ''  # No error message to return
        except (ValueError, TypeError):
            return False, "Invalid parameter type"
