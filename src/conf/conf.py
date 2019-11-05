"""
This file contains the program constants
"""

VERSION_IPV4 = 2
VERSION_IPV6 = 3

PACKET_TYPE_HELLO = 1
PACKET_TYPE_DB_DESCRIPTION = 2
PACKET_TYPE_LS_REQUEST = 3
PACKET_TYPE_LS_UPDATE = 4
PACKET_TYPE_LS_ACKNOWLEDGMENT = 5

ROUTER_ID = '3.3.3.3'

# 1st element in interface names tuple must match 1st element in interface areas tuple, and so on
INTERFACE_NAMES = ("ens33",)  # Must match interface names in the machine
INTERFACE_AREAS = ('0.0.0.0',)

AUTH_TYPE = 0
AUTHENTICATION = 0

HELLO_INTERVAL = 10
ROUTER_DEAD_INTERVAL = 40

OPTIONS = 2  # External Routing enabled - For compatibility with Cisco routers used
ROUTER_PRIORITY = 0

ALL_OSPF_ROUTERS_IPV4 = '224.0.0.5'
ALL_DR_ROUTERS_IPV4 = '224.0.0.6'
ALL_OSPF_ROUTERS_IPV6 = 'ff02::5'
ALL_DR_ROUTERS_IPV6 = 'ff02::6'

BROADCAST_INTERFACE = 1

DEFAULT_DESIGNATED_ROUTER = '0.0.0.0'

INTERFACE_COST = 10

MTU = 1500
