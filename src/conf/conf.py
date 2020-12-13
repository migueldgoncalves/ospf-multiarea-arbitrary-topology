"""
This file contains the program constants
"""

#  OSPF configurable parameters - Default

ROUTER_ID = '4.4.4.4'
ROUTER_PRIORITY = 1
INTERFACE_COST = 10
#  1st element in interface names tuple must match 1st element in interface areas tuple, and so on
#  Ex: Interface "ens32" belongs to area '0.0.0.0'
INTERFACE_NAMES = ["eth0"]  # Must match interface names in the machine
INTERFACE_AREAS = ['0.0.0.0']
KERNEL_UPDATE_INTERVAL = 0  # Implementation-specific - Minimum time between updates of kernel routing table

#  Only applicable if program is running inside provided GNS3 networks - Replaces default parameters

ROUTER_IDS = ['1.1.1.1', '2.2.2.2', '3.3.3.3', '4.4.4.4', '5.5.5.5', '6.6.6.6']
INTERFACES_R1 = [['eth0', 'eth1', 'eth2', 'eth3'], [], []]  # First list for first GNS3 network, and so on
INTERFACES_R2 = [['eth0', 'eth1', 'eth2'], [], []]
INTERFACES_R3 = [['eth0', 'eth1'], ['eth0', 'eth1'], []]
INTERFACES_R4 = [['eth0'], [], []]
INTERFACES_R5 = [['eth0'], ['eth0', 'eth1'], []]
INTERFACES_R6 = [['eth0'], [], []]
AREAS_R1 = [['0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0'], [], []]
AREAS_R2 = [['0.0.0.0', '0.0.0.0', '0.0.0.0'], [], []]
AREAS_R3 = [['0.0.0.0', '0.0.0.0'], ['0.0.0.1', '0.0.0.0'], []]
AREAS_R4 = [['0.0.0.0'], [], []]
AREAS_R5 = [['0.0.0.0'], ['0.0.0.0', '0.0.0.1'], []]
AREAS_R6 = [['0.0.0.0'], [], []]

#  OSPF-related constants

OPTIONS_V2 = 0x40 + 0x02  # O-bit and E-bit
OPTIONS_V3 = 0x10 + 0x02 + 0x01  # R-bit, E-bit, and V6-bit
PREFIX_OPTIONS = 0
DEFAULT_DESIGNATED_ROUTER = '0.0.0.0'
DEFAULT_LINK_STATE_ID = '0.0.0.0'
DEFAULT_AUTH = 0
MTU = 1500  # Maximum transmission unit - In bytes
OSPF_PROTOCOL_NUMBER = 89
INITIAL_LS_AGE = 0
INITIAL_SEQUENCE_NUMBER = 0x80000001
DEFAULT_TOS = 0
INFINITE_COST = 16777215 + 1  # Undefined in OSPF RFCs - Value larger than possible to store in cost fields (3 bytes)

#  Seconds
MAX_AGE = 60 * 60
LS_REFRESH_TIME = 30 * 60
MAX_AGE_DIFF = 15 * 60
TRANSMISSION_DELAY = 1
RETRANSMISSION_INTERVAL = 5
MIN_LS_ARRIVAL = 1
LS_ACK_TRANSMISSION_DELAY = 2  # Time acknowledgements to LS Update packets will be delayed to be grouped

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
#  LS Types 1-16 are already being used (LS Type 16 use is temporary as of December 2020)
LSA_TYPE_EXTENSION_ABR_LSA = 17  # Just for OSPFv3
LSA_TYPE_EXTENSION_PREFIX_LSA = 18  # Just for OSPFv3
LSA_TYPE_EXTENSION_ASBR_LSA = 19  # Just for OSPFv3

#  Opaque Types 1-10 are already being used (Opaque Type 10 use is temporary as of December 2020)
OPAQUE_TYPE_ABR_LSA = 11
OPAQUE_TYPE_PREFIX_LSA = 12
OPAQUE_TYPE_ASBR_LSA = 13

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

DESTINATION_TYPE_ROUTER = "Router"
DESTINATION_TYPE_NETWORK = "Network"

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

INTRA_AREA_PATH = 3
INTER_AREA_PATH = 2
TYPE_1_EXTERNAL_PATH = 1
TYPE_2_EXTERNAL_PATH = 0

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
