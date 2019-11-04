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

#  Constant names for the interfaces below are according to the GNS3 network
ETHERNET_0_NAME = "ens33"  # Must match an interface name in the machine
ETHERNET_0_AREA = '0.0.0.0'

AUTH_TYPE = 0
AUTHENTICATION = 0

HELLO_INTERVAL = 10
ROUTER_DEAD_INTERVAL = 40

OPTIONS = 2
ROUTER_PRIORITY = 0

ALL_OSPF_ROUTERS_IPV4 = '224.0.0.5'
ALL_DR_ROUTERS_IPV4 = '224.0.0.6'
ALL_OSPF_ROUTERS_IPV6 = 'ff02::5'
ALL_DR_ROUTERS_IPV6 = 'ff02::6'
