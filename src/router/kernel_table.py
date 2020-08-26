from pyroute2 import NDB

import conf.conf as conf
import general.utils as utils

'''
This class serves as an interface to OSPF route management in the Linux kernel default routing table
'''

PROTOCOL = 'proto'
DESTINATION = 'dst'
DESTINATION_LENGTH = 'dst_len'
GATEWAY = 'gateway'


class KernelTable:

    ndb = NDB()

    #  Returns the prefixes associated with the router interfaces
    @staticmethod
    def get_directly_connected_prefixes():
        prefixes = []
        for interface in conf.INTERFACE_NAMES:
            prefixes.append(utils.Utils.get_ipv4_prefix_from_interface_name(interface))
            prefixes.append(utils.Utils.get_ipv6_prefix_from_interface_name(interface))
        return prefixes

    #  Returns True if there is route created by OSPF in default routing table with provided parameters
    @staticmethod
    def has_ospf_route(prefix, prefix_length, next_hop):
        for route in KernelTable.ndb.routes.dump():
            if (route[DESTINATION] == prefix) & (route[DESTINATION_LENGTH] == prefix_length) & (
                    route[GATEWAY] == next_hop) & (route[PROTOCOL] == conf.OSPF_PROTOCOL_NUMBER):
                return True
        return False

    @staticmethod
    def get_ospf_route(prefix, prefix_length, next_hop):
        for route in KernelTable.ndb.routes.dump():
            if (route[DESTINATION] == prefix) & (route[DESTINATION_LENGTH] == prefix_length) & (
                    route[GATEWAY] == next_hop) & (route[PROTOCOL] == conf.OSPF_PROTOCOL_NUMBER):
                return route
        return None

    @staticmethod
    def get_all_ospf_routes():
        routes = []
        for route in KernelTable.ndb.routes.dump():
            if route[PROTOCOL] == conf.OSPF_PROTOCOL_NUMBER:
                routes.append(route)
        return routes

    #  Returns all routes in default routing table regardless of protocol that created them
    @staticmethod
    def get_all_routes():
        return list(KernelTable.ndb.routes.dump())

    #  Adds route to default routing table with provided parameters and OSPF as protocol
    @staticmethod
    def add_ospf_route(prefix, prefix_length, next_hop):
        #  Direct routes are always preferred over OSPF routes
        if (not KernelTable.has_ospf_route(prefix, prefix_length, next_hop)) & \
               ([prefix, prefix_length] not in KernelTable.get_directly_connected_prefixes()):
            KernelTable.ndb.routes.create(dst=prefix, dst_len=prefix_length, gateway=next_hop, proto=89).commit()

    #  Cleans the default routing table of all routes created by OSPF
    @staticmethod
    def delete_all_ospf_routes():
        for route in KernelTable.ndb.routes.dump():
            prefix = route[DESTINATION]
            prefix_length = route[DESTINATION_LENGTH]

            #  Searching for routes for these prefixes and prefix lengths will return error
            if prefix_length == 0:
                continue
            elif utils.Utils.is_ipv4_address(prefix):
                if prefix_length == 4 * conf.BYTE_SIZE:
                    continue
                elif utils.Utils.ipv4_to_decimal('127.0.0.0') <= utils.Utils.ipv4_to_decimal(prefix) <= \
                        utils.Utils.ipv4_to_decimal('127.255.255.255'):
                    continue
            else:  # IPv6
                if prefix_length == 16 * conf.BYTE_SIZE:
                    continue
                elif utils.Utils.ipv6_to_decimal('ff00::') <= utils.Utils.ipv6_to_decimal(prefix) <= \
                        utils.Utils.ipv6_to_decimal('ff00:ffff:ffff:ffff:ffff:ffff:ffff:ffff'):
                    continue

            prefix_string = prefix + '/' + str(prefix_length)
            if KernelTable.ndb.routes[{DESTINATION: prefix_string}][PROTOCOL] == conf.OSPF_PROTOCOL_NUMBER:
                KernelTable.ndb.routes[{DESTINATION: prefix_string}].remove().commit()
