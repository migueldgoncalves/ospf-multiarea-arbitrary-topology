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
INITIAL_LS_AGE = 0
INITIAL_SEQUENCE_NUMBER = 0x80000001
DEFAULT_TOS = 0

#  Seconds
MAX_AGE = 60 * 60
LS_REFRESH_TIME = 30 * 60
MAX_AGE_DIFF = 15 * 60
TRANSMISSION_DELAY = 1
RETRANSMISSION_INTERVAL = 5
MIN_LS_ARRIVAL = 1
LS_ACK_TRANSMISSION_DELAY = 3  # Time acknowledgements to LS Update packets will be delayed to be grouped

VERSION_IPV4 = 2
VERSION_IPV6 = 3

PACKET_TYPE_HELLO = 1
PACKET_TYPE_DB_DESCRIPTION = 2
PACKET_TYPE_LS_REQUEST = 3
PACKET_TYPE_LS_UPDATE = 4
PACKET_TYPE_LS_ACKNOWLEDGMENT = 5

LSA_TYPE_ROUTER = 1
LSA_TYPE_NETWORK = 2
LSA_TYPE_SUMMARY_TYPE_3 = 3  # Just for OSPFv2
LSA_TYPE_INTER_AREA_PREFIX = 3  # Just for OSPFv3
LSA_TYPE_SUMMARY_TYPE_4 = 4  # Just for OSPFv2
LSA_TYPE_INTER_AREA_ROUTER = 4  # Just for OSPFv3
LSA_TYPE_AS_EXTERNAL = 5
LSA_TYPE_LINK = 8  # Just for OSPFv3
LSA_TYPE_INTRA_AREA_PREFIX = 9  # Just for OSPFv3
LSA_TYPE_OPAQUE_LINK_LOCAL = 9  # Just for OSPFv2
LSA_TYPE_OPAQUE_AREA = 10  # Just for OSPFv2
LSA_TYPE_OPAQUE_AS = 11  # Just for OSPFv2

#  1st element in interface names tuple must match 1st element in interface areas tuple, and so on
#  Ex: Interface "ens33" belongs to area '0.0.0.0'
INTERFACE_NAMES = ["ens33"]  # Must match interface names in the machine
INTERFACE_AREAS = ['0.0.0.0']

HELLO_INTERVAL = 10
ROUTER_DEAD_INTERVAL = 40

ALL_OSPF_ROUTERS_IPV4 = '224.0.0.5'
ALL_DR_IPV4 = '224.0.0.6'
ALL_OSPF_ROUTERS_IPV6 = 'ff02::5'
ALL_DR_IPV6 = 'ff02::6'

BACKBONE_AREA = '0.0.0.0'

OSPFV2_PACKET_HEADER_LENGTH = 24
OSPFV3_PACKET_HEADER_LENGTH = 16
OSPFV2_BASE_HELLO_LENGTH = 44
OSPFV3_BASE_HELLO_LENGTH = 36
HELLO_NEIGHBOR_LENGTH = 4
OSPFV2_BASE_DB_DESCRIPTION_LENGTH = 8
OSPFV3_BASE_DB_DESCRIPTION_LENGTH = 12  # 10 content bytes + 2 empty bytes

LSA_HEADER_LENGTH = 20

INTERFACE_STATE_DOWN = "DOWN"
INTERFACE_STATE_WAITING = "WAITING"
INTERFACE_STATE_POINT_POINT = "POINT-TO-POINT"
INTERFACE_STATE_DR = "DR"
INTERFACE_STATE_BACKUP = "BACKUP"
INTERFACE_STATE_DROTHER = "DROTHER"

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

LINK_LOCAL_SCOPING = 0
AREA_SCOPING = 1
AS_SCOPING = 2

BROADCAST_INTERFACE = 1
POINT_TO_POINT_INTERFACE = 2

POINT_TO_POINT_LINK = 1
LINK_TO_TRANSIT_NETWORK = 2
LINK_TO_STUB_NETWORK = 3
VIRTUAL_LINK = 4

#  General constants

IPV4_HEADER_BASE_LENGTH = 20
SOURCE_IPV4_ADDRESS_1ST_BYTE = 12  # 1st byte of the source IPv4 address is the 13th of the IPv4 header

BYTE_SIZE = 8
BASE_16 = 16
HEX_DIGIT_BIT_SIZE = 4
IPV4_ADDRESS_BYTE_LENGTH = 4
IPV6_ADDRESS_BYTE_LENGTH = 16

MAX_VALUE_8_BITS = 255
MAX_VALUE_16_BITS = 65535
MAX_VALUE_24_BITS = 16777215
MAX_VALUE_32_BITS = 4294967295
MAX_VALUE_64_BITS = 18446744073709551615
MAX_VALUE_128_BITS = 340282366920938463463374607431768211455
