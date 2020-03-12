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
        return str(ipaddress.IPv4Address(decimal))

    #  Converts numbers between 0 and 340282366920938463463374607431768211455 to IPv6 addresses
    @staticmethod
    def decimal_to_ipv6(decimal):
        return str(ipaddress.IPv6Address(decimal))

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
        network_mask_length = bin(int(ipaddress.IPv6Address(network_mask)))[2:].count('1')  # '0b1111'[2:] -> '1111'
        prefix = str(ipaddress.IPv6Interface((global_ipv6_address, network_mask_length)).network).split("/")[0]
        return [prefix, network_mask_length]

    #  Returns True if argument is a valid IPv4 address
    @staticmethod
    def is_ipv4_address(ip_address):
        try:
            ipaddress.IPv4Address(ip_address)
            return True
        except ipaddress.AddressValueError:
            return False

    #  Returns True if argument is a valid IPv6 address
    @staticmethod
    def is_ipv6_address(ip_address):
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
