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


'''
This class will be used to add and remove routes. All routes will be from OSPF (89), direct routes will already be here
and should remain intact. No previously existent route should be changed in any way.

There will be 2 main methods: to add a single OSPF route, and to delete all routes.

Adding routes should consider the direct routes. If a direct route exists (e.g. prefix if a directly connected one), no route
should be added. For that, a method should exist that collects, for a given OSPF version, the prefixes associated with the
machine interfaces. Those prefixes will be checked when adding routes.

All added routes should be associated with IP protocol 89. Deleting all routes will search for all routes with IP protocol
89 and delete them. All routes not coming from OSPF should remain intact.

More for test purposes than for any other practical purpose, methods that check if an OSPF route exists, that return that
OSPF route, or all of them, should exist as well.
'''

#print(type(ndb.routes))

#for line in ndb.routes.summary().format('csv'):
#    print(line)

#for line in ndb.routes.dump().format('csv'):
#    print(line)


'''def has_route(prefix, prefix_length, outgoing_interface, next_hop_address, version):
    if version == conf.VERSION_IPV4:
        gateway = utils.Utils.get_ipv4_address_from_interface_name(outgoing_interface)
    elif version == conf.VERSION_IPV6:
        gateway = utils.Utils.get_ipv6_link_local_address_from_interface_name(outgoing_interface)
    else:
        raise ValueError("Invalid OSPF version")

    for route in tuple(ndb.routes.summary()):
        route = tuple(route)
        if (route[DESTINATION] == prefix) & (route[DESTINATION_LENGTH] == prefix_length) & (route[GATEWAY] == gateway) \
                & (route[NEXT_HOP] == next_hop_address):
            return True
    return False'''

'''def has_route(prefix, prefix_length, outgoing_interface, next_hop_address, version):
    if version == conf.VERSION_IPV4:
        gateway = utils.Utils.get_ipv4_address_from_interface_name(outgoing_interface)
    elif version == conf.VERSION_IPV6:
        gateway = utils.Utils.get_ipv6_link_local_address_from_interface_name(outgoing_interface)
    else:
        raise ValueError("Invalid OSPF version")

    for route in ndb.routes.dump():
        print("Here is the route")
        print(route['nexthop'])
        print(route)
        if (route['dst'] == prefix) & (route['dst_len'] == prefix_length) & (route['gateway'] == gateway) \
                & (route['nexthop'] == next_hop_address):
            return True
    return False

def add_ospf_route(prefix, prefix_length, outgoing_interface, next_hop_address):
    pass

def delete_ospf_routes():
    for route in tuple(ndb.routes.summary()):
        route = tuple(route)
        subnet_address = route[DESTINATION]
        prefix_length = route[DESTINATION_LENGTH]
        if has_route(subnet_address, prefix_length, 'ens33', '', conf.VERSION_IPV4):
            print(subnet_address + '/' + str(prefix_length))
            print(ndb.routes[{'dst': subnet_address + '/' + str(prefix_length)}]['proto'])
            if ndb.routes[{'dst': subnet_address + '/' + str(prefix_length)}]['proto'] == 89:
                ndb.routes[{'dst': subnet_address + '/' + str(prefix_length)}].remove().commit()

has_route('', 0, 'ens33', '', conf.VERSION_IPV4)
#print(tuple(ndb.routes.summary()[0])[GATEWAY])

#print(ndb.routes[{'dst': '222.222.1.0/24', 'proto': 89}])'''
'''if has_route('222.222.1.0', 24):
    ndb.routes[{'dst': '222.222.1.0/24'}].remove().commit()
    print("Deleted")
else:
    print("Does not exist - Did not delete")'''
'''delete_ospf_routes()
if (not has_route('222.222.1.0', 24, 'ens33', '', conf.VERSION_IPV4)) | True:
    print("Route does not exist - Creating...")
    ndb.routes.create(dst='222.222.1.0', dst_len=24, gateway='222.222.1.2', priority=1000, proto=89).commit()'''