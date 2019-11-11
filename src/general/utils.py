import netifaces

import conf.conf as conf

'''
This class contains utility functions used throughout the router code
'''


class Utils:

    #  Converts IPv4 addresses to numbers between 0 and 4294967295
    @staticmethod
    def ipv4_to_decimal(ip_address):
        if not Utils.is_ipv4_address(ip_address):
            raise ValueError("Invalid IPv4 address")
        parts = ip_address.split('.')
        return (int(parts[0]) << 3 * conf.BYTE_SIZE) + (int(parts[1]) << 2 * conf.BYTE_SIZE) + \
               (int(parts[2]) << conf.BYTE_SIZE) + int(parts[3])

    #  Calculates the OSPFv2 packet checksum - Same as IPv4 header checksum
    #  It is assumed that checksum, authentication and authentication type fields are clear
    @staticmethod
    def create_checksum_ipv4(message):

        #  1 - Get all 16-bit blocks of the message, and sum them
        content_chunk_sum = 0
        for i in range(len(message) // 2):  # len() returns byte size - Chunks of 2 bytes are required
            value = int(message.hex()[conf.HEX_DIGIT_BIT_SIZE * i:conf.HEX_DIGIT_BIT_SIZE * i +
                        conf.HEX_DIGIT_BIT_SIZE], conf.BASE_16)
            content_chunk_sum += value

        #  2 - If sum exceeds 16 bits, carry value (the remainder) is added to the 16-bit sum
        quotient, remainder = divmod(content_chunk_sum, conf.MAX_VALUE_16_BITS + 1)
        result = quotient + remainder

        #  3 - If another carry happens, another 1 is added to the 16-bit result
        if result > conf.MAX_VALUE_16_BITS:
            result = divmod(result, conf.MAX_VALUE_16_BITS + 1)[0] + 1

        #  4 - The checksum is the 1's complement (all bits are inverted) of the previous result
        checksum = result ^ conf.MAX_VALUE_16_BITS
        return checksum

    #  Returns the IP address of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv4_address_from_interface_name(interface_name):
        return netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']

    #  Returns the network mask of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv4_network_mask_from_interface_name(interface_name):
        return netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['netmask']

    #  Returns True if argument is a valid IPv4 address
    @staticmethod
    def is_ipv4_address(ip_address):
        try:
            parts = ip_address.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if (int(part) < 0) | (int(part) > conf.MAX_VALUE_8_BITS):
                    return False
            return True
        except ValueError:
            return False

    #  Return True if argument is a valid IPv4 network mask
    @staticmethod
    def is_ipv4_network_mask(network_mask):
        if not Utils.is_ipv4_address(network_mask):
            return False
        if network_mask == '0.0.0.0':  # Method below will not work for address '0.0.0.0' since 2's complement of 0 is 0
            return True

        #  Creates 32-bit number from network mask
        first, second, third, fourth = (int(octet) for octet in network_mask.split("."))
        binary_mask = first << 24 | second << 16 | third << 8 | fourth

        #  Iterates over the 0's at the right
        #  https://wiki.python.org/moin/BitManipulation#lowestSet.28.29
        lowest_set_bit = binary_mask & -binary_mask  # "0010" & "1110" = "0010"
        zero_bits = -1  # If LSB is 1, cycle iterates once - There are 0 bits with value 0
        while lowest_set_bit:  # Until first 1 at right is reached
            lowest_set_bit >>= 1
            zero_bits += 1

        #  Verifies that all bits to the left are 1's
        if binary_mask | ((1 << zero_bits) - 1) != conf.MAX_VALUE_32_BITS:  # "1100" | "0011" = "1111"
            return False  # Bits to the left include 0's
        return True
