BYTE_SIZE = 8
BASE_16 = 16
HEXA_DIGIT_BIT_SIZE = 4
MAX_VALUE_8_BITS = 255
MAX_VALUE_16_BITS = 65535

'''
This class contains utility functions used throughout the router code
'''


class Utils:

    #  Converts IPv4 addresses to numbers between 0 and 4294967295
    @staticmethod
    def ipv4_to_decimal(ip_address):
        parts = ip_address.split('.')
        if len(parts) != 4:
            raise ValueError("Invalid IP address format")
        for part in parts:
            if (int(part) < 0) | (int(part) > MAX_VALUE_8_BITS):
                raise ValueError("Invalid IP address value")
        return (int(parts[0]) << 3 * BYTE_SIZE) + (int(parts[1]) << 2 * BYTE_SIZE) + (int(parts[2]) << BYTE_SIZE) + \
               int(parts[3])

    #  Calculates the OSPFv2 packet checksum - Same as IPv4 header checksum
    #  It is assumed that checksum and authentication fields are clear
    @staticmethod
    def create_checksum_ipv4(message):

        #  1 - Get all 16-bit blocks of the message, and sum them
        content_chunck_sum = 0
        for i in range(len(message)//2):  # len() returns byte size - Chuncks of 2 bytes are required
            value = int(message.hex()[HEXA_DIGIT_BIT_SIZE * i:HEXA_DIGIT_BIT_SIZE * i + HEXA_DIGIT_BIT_SIZE], BASE_16)
            content_chunck_sum += value

        #  2 - If sum exceeds 16 bits, carry value (the remainder) is added to the 16-bit sum
        quotient, remainder = divmod(content_chunck_sum, MAX_VALUE_16_BITS + 1)
        result = quotient + remainder

        #  3 - If another carry happens, another 1 is added to the 16-bit result
        if result > MAX_VALUE_16_BITS:
            result = divmod(result, MAX_VALUE_16_BITS + 1)[0] + 1

        #  4 - The checksum is the 1's complement (all bits are inverted) of the previous result
        checksum = result ^ MAX_VALUE_16_BITS
        return checksum
