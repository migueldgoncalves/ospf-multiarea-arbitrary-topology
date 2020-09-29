import netifaces
import ipaddress
import struct

import conf.conf as conf

'''
This class contains utility functions used throughout the router code
'''


class Utils:

    #  Converts IPv4 addresses to numbers between 0 and 4294967295
    @staticmethod
    def ipv4_to_decimal(ip_address):
        return int(ipaddress.IPv4Address(ip_address))

    #  Converts IPv6 addresses to numbers between 0 and 340282366920938463463374607431768211455
    @staticmethod
    def ipv6_to_decimal(ip_address):
        return int(ipaddress.IPv6Address(ip_address))

    #  Converts numbers between 0 and 4294967295 to IPv4 addresses
    @staticmethod
    def decimal_to_ipv4(decimal):
        return str(ipaddress.IPv4Address(int(decimal)))

    #  Converts numbers between 0 and 340282366920938463463374607431768211455 to IPv6 addresses
    @staticmethod
    def decimal_to_ipv6(decimal):
        return str(ipaddress.IPv6Address(int(decimal)))

    #  Calculates the OSPFv2 packet checksum - Same as IPv4 header checksum
    #  It is assumed that checksum, authentication and authentication type fields are clear
    @staticmethod
    def create_checksum_ospfv2(message):
        #  1 - If the message has an odd number of bytes, append a empty byte at the end
        if (len(message) % 2) != 0:
            message += b'\x00'

        #  2 - Get all 16-bit blocks of the message, and sum them
        content_chunk_sum = 0
        for i in range(len(message) // 2):  # len() returns byte size - Chunks of 2 bytes are required
            value = int(message.hex()[conf.HEX_DIGIT_BIT_SIZE * i:conf.HEX_DIGIT_BIT_SIZE * i +
                        conf.HEX_DIGIT_BIT_SIZE], conf.BASE_16)
            content_chunk_sum += value

        #  3 - If sum exceeds 16 bits, carry value (the remainder) is added to the 16-bit sum
        quotient, remainder = divmod(content_chunk_sum, conf.MAX_VALUE_16_BITS + 1)
        result = quotient + remainder

        #  4 - If another carry happens, another 1 is added to the 16-bit result
        if result > conf.MAX_VALUE_16_BITS:
            result = divmod(result, conf.MAX_VALUE_16_BITS + 1)[0] + 1

        #  5 - The checksum is the 1's complement (all bits are inverted) of the previous result
        checksum = result ^ conf.MAX_VALUE_16_BITS
        return checksum

    #  Calculates the OSPFv3 packet checksum
    #  It is assumed that the checksum field is clear
    @staticmethod
    def create_checksum_ospfv3(message, source_address, destination_address):
        source_address_bytes = ipaddress.IPv6Address(source_address).packed
        destination_address_bytes = ipaddress.IPv6Address(destination_address).packed

        #  Format strings indicate the format of the byte objects to be created, or converted to other object types
        #  > - Big-endian
        #  B - Unsigned char (1 byte) - struct.unpack("> B", b'\x01) -> 1
        #  L - Unsigned long (4 bytes) - struct.unpack("> L", b'\x00\x00\x00\x01) -> 1

        upper_layer_packet_length = struct.pack("> L", len(message))
        next_header = struct.pack("> B", conf.OSPF_PROTOCOL_NUMBER)

        #  Attaching a "pseudo-header" to the OSPFv3 packet is required since IPv6 does not include a packet checksum
        pseudo_header = source_address_bytes + destination_address_bytes + upper_layer_packet_length + b'\x00\x00\x00'\
            + next_header
        return Utils.create_checksum_ospfv2(pseudo_header + message)  # Bitwise operations are the same as in OSPFv2

    #  Calculates the LSA Fletcher's checksum
    #  It is assumed that the LSA Age (first 2 bytes) is removed, and the checksum field is clear
    @staticmethod
    def create_fletcher_checksum(message):
        c0 = 0
        c1 = 0
        for i in range(len(message)):
            c0 = (message[i] + c0) % conf.MAX_VALUE_8_BITS
            c1 = (c0 + c1) % conf.MAX_VALUE_8_BITS
        x = (-c1 + (len(message) - 15) * c0) % conf.MAX_VALUE_8_BITS  # Checksum starts at 16th byte of LSA
        y = (c1 - (len(message) - 15 + 1) * c0) % conf.MAX_VALUE_8_BITS
        return (x << conf.BYTE_SIZE) + y

    #  Returns the IPv4 address of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv4_address_from_interface_name(interface_name):
        return netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']

    #  Returns the IPv6 global address of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv6_global_address_from_interface_name(interface_name):
        return netifaces.ifaddresses(interface_name)[netifaces.AF_INET6][0]['addr']

    #  Returns the IPv6 link-local address of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv6_link_local_address_from_interface_name(interface_name):
        return netifaces.ifaddresses(interface_name)[netifaces.AF_INET6][1]['addr'].split('%')[0]

    #  Returns the IPv4 network mask of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv4_network_mask_from_interface_name(interface_name):
        return netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['netmask']

    #  Returns the IPv4 prefix and respective length of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv4_prefix_from_interface_name(interface_name):
        ipv4_address = Utils.get_ipv4_address_from_interface_name(interface_name)
        network_mask = Utils.get_ipv4_network_mask_from_interface_name(interface_name)
        prefix_length = bin(int(ipaddress.IPv4Address(network_mask)))[2:].count('1')  # '0b1111'[2:] -> '1111'
        prefix = str(ipaddress.IPv4Interface((ipv4_address, prefix_length)).network).split("/")[0]
        return [prefix, prefix_length]

    #  TODO: Consider the case where more than one IPv6 prefix is configured
    #  Returns the IPv6 network mask of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv6_network_mask_from_interface_name(interface_name):
        return netifaces.ifaddresses(interface_name)[netifaces.AF_INET6][0]['netmask']

    #  Returns the IPv6 prefix and respective length of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv6_prefix_from_interface_name(interface_name):
        global_ipv6_address = Utils.get_ipv6_global_address_from_interface_name(interface_name)
        network_mask = Utils.get_ipv6_network_mask_from_interface_name(interface_name)
        prefix_length = bin(int(ipaddress.IPv6Address(network_mask)))[2:].count('1')  # '0b1111'[2:] -> '1111'
        prefix = str(ipaddress.IPv6Interface((global_ipv6_address, prefix_length)).network).split("/")[0]
        return [prefix, prefix_length]

    #  Returns True if argument is a valid IPv4 address
    @staticmethod
    def is_ipv4_address(ip_address):
        try:
            int(ip_address)
            return False
        except (ValueError, TypeError):
            try:
                ipaddress.IPv4Address(ip_address)
                return True
            except ipaddress.AddressValueError:
                return False

    #  Returns True if argument is a valid IPv6 address
    @staticmethod
    def is_ipv6_address(ip_address):
        try:
            int(ip_address)
            return False
        except (ValueError, TypeError):
            try:
                ipaddress.IPv6Address(ip_address)
                return True
            except ipaddress.AddressValueError:
                return False

    #  Returns the version of the running OSPF protocol given an IP address
    @staticmethod
    def get_ospf_version(ip_address):
        if Utils.is_ipv4_address(ip_address):
            return conf.VERSION_IPV4
        elif Utils.is_ipv6_address(ip_address):
            return conf.VERSION_IPV6
        else:
            raise ValueError("No valid IP address provided")

    #  Return True if argument is a valid IPv4 network mask
    @staticmethod
    def is_ipv4_network_mask(network_mask):
        if not Utils.is_ipv4_address(network_mask):
            return False
        if network_mask == '0.0.0.0':  # Method below will not work for address '0.0.0.0' since 2's complement of 0 is 0
            return True
        binary_mask = Utils.ipv4_to_decimal(network_mask)
        return Utils.is_network_mask(binary_mask, conf.MAX_VALUE_32_BITS)

    #  Return True if argument is a valid IPv6 network mask
    @staticmethod
    def is_ipv6_network_mask(network_mask):
        if not Utils.is_ipv6_address(network_mask):
            return False
        if network_mask == '::':  # Method below will not work for address '::' since 2's complement of 0 is 0
            return True
        binary_mask = Utils.ipv6_to_decimal(network_mask)
        return Utils.is_network_mask(binary_mask, conf.MAX_VALUE_128_BITS)

    #  Given a binary IP address (IPv4 or IPv6), returns True if it is a valid network mask
    @staticmethod
    def is_network_mask(binary_mask, max_value):
        #  Iterates over the 0's at the right of the binary network mask
        #  https://wiki.python.org/moin/BitManipulation#lowestSet.28.29
        lowest_set_bit = binary_mask & -binary_mask  # "0010" & "1110" = "0010"
        zero_bits = -1  # If LSB is 1, cycle iterates once - There are 0 bits with value 0
        while lowest_set_bit:  # Until first 1 at right is reached
            lowest_set_bit >>= 1
            zero_bits += 1

        #  Verifies that all bits to the left are 1's
        if binary_mask | ((1 << zero_bits) - 1) != max_value:  # "1100" | "0011" = "1111"
            return False  # Bits to the left include 0's
        return True

    #  Given an IP address and a network mask, return True if the address is part of the network
    @staticmethod
    def is_ip_in_network(ip_address, interface_name):
        if not (Utils.is_ipv4_address(ip_address) | Utils.is_ipv6_address(ip_address)):
            return False
        elif Utils.is_ipv4_address(ip_address):
            network_prefix = Utils.get_ipv4_prefix_from_interface_name(interface_name)
            decimal_network_prefix = Utils.ipv4_to_decimal(network_prefix[0])
            decimal_ip_address = Utils.ipv4_to_decimal(ip_address) >> (32 - network_prefix[1])
            return decimal_ip_address == (decimal_network_prefix >> (32 - network_prefix[1]))
        elif Utils.is_ipv6_address(ip_address):
            network_prefix = Utils.get_ipv6_prefix_from_interface_name(interface_name)
            decimal_network_prefix = Utils.ipv6_to_decimal(network_prefix[0])
            decimal_ip_address = Utils.ipv6_to_decimal(ip_address) >> (128 - network_prefix[1])
            return decimal_ip_address == (decimal_network_prefix >> (128 - network_prefix[1]))
        else:
            return False

    #  Given IP address and prefix length, returns network prefix
    @staticmethod
    def ip_address_to_prefix(ip_address, prefix_length):  # For OSPFv2 netmask can replace prefix length
        if Utils.is_ipv4_address(ip_address):
            return str(ipaddress.IPv4Network((ip_address, prefix_length), strict=False).network_address)
        elif Utils.is_ipv6_address(ip_address):
            return str(ipaddress.IPv6Network((ip_address, prefix_length), strict=False).network_address)
        else:
            raise ValueError("Invalid IP address")

    #  Given prefix length, returns corresponding network mask
    @staticmethod
    def prefix_length_to_network_mask(prefix_length, version):
        if version == conf.VERSION_IPV4:
            max_len = 4 * conf.BYTE_SIZE
            max_netmask = conf.MAX_VALUE_32_BITS
            return Utils.decimal_to_ipv4((max_netmask >> (max_len - prefix_length)) << (max_len - prefix_length))
        elif version == conf.VERSION_IPV6:
            max_len = 16 * conf.BYTE_SIZE
            max_netmask = conf.MAX_VALUE_128_BITS
            return Utils.decimal_to_ipv6((max_netmask >> (max_len - prefix_length)) << (max_len - prefix_length))
        else:
            raise ValueError("Invalid OSPF version")

    #  Given a prefix, returns its length
    @staticmethod
    def get_prefix_length_from_prefix(prefix):
        if Utils.is_ipv4_address(prefix):
            prefix = Utils.ipv4_to_decimal(prefix)
            prefix_length = 4 * conf.BYTE_SIZE
        elif Utils.is_ipv6_address(prefix):
            prefix = Utils.ipv6_to_decimal(prefix)
            prefix_length = 16 * conf.BYTE_SIZE
        else:
            raise ValueError("Invalid prefix")
        host_bits = 0
        while True:
            if prefix & (2 ** host_bits) != 0:
                return prefix_length - host_bits
            host_bits += 1

    #  Given a prefix length and a OSPF version, returns the prefix
    @staticmethod
    def get_prefix_from_prefix_length(prefix_length, version):
        if version == conf.VERSION_IPV4:
            bits_to_clear = 4 * conf.BYTE_SIZE - prefix_length
            decimal_prefix = (conf.MAX_VALUE_32_BITS >> bits_to_clear) << bits_to_clear
            return Utils.decimal_to_ipv4(decimal_prefix)
        elif version == conf.VERSION_IPV6:
            bits_to_clear = 16 * conf.BYTE_SIZE - prefix_length
            decimal_prefix = (conf.MAX_VALUE_128_BITS >> bits_to_clear) << bits_to_clear
            return Utils.decimal_to_ipv6(decimal_prefix)
        else:
            raise ValueError("Invalid OSPF version")
