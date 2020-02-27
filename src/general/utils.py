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

    #  Converts IPv6 addresses to numbers between 0 and 340282366920938463463374607431768211455
    '''@staticmethod
    def ipv6_to_decimal(ip_address):
        if not Utils.is_ipv6_address(ip_address):
            raise ValueError("Invalid IPv6 address")'''

    #  Converts numbers between 0 and 4294967295 to IPv4 addresses
    @staticmethod
    def decimal_to_ipv4(decimal):
        if not (0 <= decimal <= conf.MAX_VALUE_32_BITS):
            raise ValueError("Invalid IPv4 decimal")
        first_octet = decimal >> 3 * conf.BYTE_SIZE
        second_octet = (decimal >> 2 * conf.BYTE_SIZE) % (conf.MAX_VALUE_8_BITS + 1)
        third_octet = (decimal >> conf.BYTE_SIZE) % (conf.MAX_VALUE_8_BITS + 1)
        fourth_octet = decimal % (conf.MAX_VALUE_8_BITS + 1)
        ip_address = str(first_octet) + "." + str(second_octet) + "." + str(third_octet) + "." + str(fourth_octet)
        return ip_address

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

    #  Returns the IPv6 prefix of an interface given its name (ex: ens33)
    @staticmethod
    def get_ipv6_prefix_from_interface_name(interface_name):
        global_ipv6_address = Utils.get_ipv6_global_address_from_interface_name(interface_name)
        network_mask = Utils.get_ipv6_network_mask_from_interface_name(interface_name)
        network_mask = network_mask.split("::")[0]
        hextets = network_mask.split(":")

    #  Returns True if argument is a valid IPv4 address
    @staticmethod
    def is_ipv4_address(ip_address):
        if ' ' in ip_address:
            return False
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

    #  Returns True if argument is a valid IPv6 address
    @staticmethod
    def is_ipv6_address(ip_address):
        if ' ' in ip_address:
            return False
        try:
            if ip_address == '::':
                return True
            if ':' not in ip_address:
                return False
            parts = ip_address.split('::')
            if len(parts) > 2:  # 2001::db8::1 -> Invalid IPv6 address
                return False
            number_hextets = 0
            for part in parts:
                if part != '':  # '0::'.split('::') -> ['0', '']
                    hextets = part.split(':')
                    if '' in hextets:
                        hextets.remove('')
                    for hextet in hextets:
                        number_hextets += 1
                        if number_hextets > 8:
                            return False
                        hextet = int(hextet, conf.BASE_16)
                        if (hextet < 0) | (hextet > conf.MAX_VALUE_16_BITS):
                            return False
            if (len(parts) == 2) & (number_hextets == 8):  # 2001:1:1:1::1:1:1:1 -> Invalid address
                return False
            elif (len(parts) == 1) & (number_hextets < 8):  # 2001:1:1:1 -> Invalid address
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
