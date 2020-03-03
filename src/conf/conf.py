"""
This file contains the program constants
"""

#  OSPF-related constants

ROUTER_ID = '4.4.4.4'
ROUTER_PRIORITY = 1
OPTIONS = 2  # External Routing enabled - For compatibility with Cisco routers used
DEFAULT_DESIGNATED_ROUTER = '0.0.0.0'
DEFAULT_AUTH = 0
INTERFACE_COST = 10
MTU = 1500  # Maximum transmission unit - In bytes
OSPF_PROTOCOL_NUMBER = 89

VERSION_IPV4 = 2
VERSION_IPV6 = 3

PACKET_TYPE_HELLO = 1
PACKET_TYPE_DB_DESCRIPTION = 2
PACKET_TYPE_LS_REQUEST = 3
PACKET_TYPE_LS_UPDATE = 4
PACKET_TYPE_LS_ACKNOWLEDGMENT = 5

#  1st element in interface names tuple must match 1st element in interface areas tuple, and so on
#  Ex: Interface "ens33" belongs to area '0.0.0.0'
INTERFACE_NAMES = ("ens33",)  # Must match interface names in the machine
INTERFACE_AREAS = ('0.0.0.0',)

HELLO_INTERVAL = 10
ROUTER_DEAD_INTERVAL = 40

ALL_OSPF_ROUTERS_IPV4 = '224.0.0.5'
ALL_DR_IPV4 = '224.0.0.6'
ALL_OSPF_ROUTERS_IPV6 = 'ff02::5'
ALL_DR_IPV6 = 'ff02::6'

BACKBONE_AREA = '0.0.0.0'

OSPFV2_HEADER_LENGTH = 24
OSPFV3_HEADER_LENGTH = 16

OSPFV2_BASE_HELLO_LENGTH = 44
HELLO_NEIGHBOR_LENGTH = 4

NEIGHBOR_STATE_DOWN = "DOWN"
NEIGHBOR_STATE_INIT = "INIT"
NEIGHBOR_STATE_2_WAY = "2-WAY"
NEIGHBOR_STATE_EXSTART = "EXSTART"
NEIGHBOR_STATE_EXCHANGE = "EXCHANGE"
NEIGHBOR_STATE_LOADING = "LOADING"
NEIGHBOR_STATE_FULL = "FULL"

NULL_AUTHENTICATION = 0
SIMPLE_PASSWORD = 1
CRYPTOGRAPHIC_AUTHENTICATION = 2

BROADCAST_INTERFACE = 1
POINT_TO_POINT_INTERFACE = 2

#  General constants

IP_HEADER_BASE_LENGTH = 20
SOURCE_IP_ADDRESS_1ST_BYTE = 12  # 1st byte of the source IP address is the 13th of the IP header
DESTINATION_IP_ADDRESS_1ST_BYTE = 16

BYTE_SIZE = 8
BASE_16 = 16
HEX_DIGIT_BIT_SIZE = 4
IP_ADDRESS_BYTE_LENGTH = 4

MAX_VALUE_8_BITS = 255
MAX_VALUE_16_BITS = 65535
MAX_VALUE_24_BITS = 16777215
MAX_VALUE_32_BITS = 4294967295
MAX_VALUE_64_BITS = 18446744073709551615
MAX_VALUE_128_BITS = 340282366920938463463374607431768211455
