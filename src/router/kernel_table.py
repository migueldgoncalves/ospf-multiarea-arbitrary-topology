import multiprocessing
import os

import conf.conf as conf
import general.utils as utils

'''
This class serves as an interface to OSPF route management in the Linux kernel default routing table
'''


class KernelTable:

    lock = multiprocessing.RLock()

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
        with KernelTable.lock:
            result = True if KernelTable.get_ospf_route(prefix, prefix_length, next_hop) is not None else False
            return result

    @staticmethod
    def get_ospf_route(prefix, prefix_length, next_hop):
        with KernelTable.lock:
            for route in KernelTable.get_all_ospf_routes():
                if (KernelTable.get_route_prefix(route) == prefix) & (
                        KernelTable.get_route_prefix_length(route) == int(prefix_length)) & (
                        KernelTable.get_route_next_hop(route) == next_hop):
                    return route
            return None

    @staticmethod
    def get_all_ospf_routes():
        with KernelTable.lock:
            routes = []
            for route in KernelTable.get_all_routes():
                if KernelTable.get_route_protocol(route) == conf.OSPF_PROTOCOL_NUMBER:
                    routes.append(route)
            return routes

    #  Returns all routes in default routing table regardless of protocol that created them
    @staticmethod
    def get_all_routes():
        with KernelTable.lock:
            routes = []
            for command in ['ip route list', 'ip -6 route list']:
                with os.popen(command) as output:
                    route_list = output.read()
                for route in route_list.split('\n'):
                    routes.append(route)
            return routes

    #  Adds route to default routing table with provided parameters and OSPF as protocol
    @staticmethod
    def add_ospf_route(prefix, prefix_length, next_hop, outgoing_interface):
        if (prefix == '') | (next_hop == '') | (outgoing_interface == ''):
            return
        with KernelTable.lock:
            #  Direct routes are always preferred over OSPF routes
            if (not KernelTable.has_ospf_route(prefix, prefix_length, next_hop)) & (
                    [prefix, prefix_length] not in KernelTable.get_directly_connected_prefixes()):
                os.system('sudo ip route add ' + prefix + '/' + str(prefix_length) + ' via ' + next_hop + ' dev ' +
                          outgoing_interface + ' proto ' + str(conf.OSPF_PROTOCOL_NUMBER))

    #  Cleans the default routing table of all routes created by specified version of OSPF
    @staticmethod
    def delete_all_ospf_routes(ospf_version):
        with KernelTable.lock:
            for route in KernelTable.get_all_ospf_routes():
                prefix = KernelTable.get_route_prefix(route)
                prefix_length = KernelTable.get_route_prefix_length(route)
                next_hop = KernelTable.get_route_next_hop(route)
                outgoing_interface = KernelTable.get_route_outgoing_interface(route)

                prefix_version = conf.VERSION_IPV4 if utils.Utils.is_ipv4_address(prefix) else conf.VERSION_IPV6
                if (prefix_version == ospf_version) | (ospf_version == 0):
                    os.system('sudo ip route del ' + prefix + '/' + str(prefix_length) + ' via ' + next_hop + ' dev ' +
                              outgoing_interface + ' proto ' + str(conf.OSPF_PROTOCOL_NUMBER))

    #  Given route information as returned by command 'ip route list', returns its prefix
    @staticmethod
    def get_route_prefix(route):
        try:
            return route.split()[0].split('/')[0]
        except IndexError:
            return ''

    #  Given route information as returned by command 'ip route list', returns its prefix length
    @staticmethod
    def get_route_prefix_length(route):
        try:
            return int(route.split()[0].split('/')[1])
        except IndexError:  # No prefix length info
            return 0

    #  Given route information as returned by command 'ip route list', returns its next hop
    @staticmethod
    def get_route_next_hop(route):
        return KernelTable.get_router_data(route, 'via')

    #  Given route information as returned by command 'ip route list', returns its outgoing interface
    @staticmethod
    def get_route_outgoing_interface(route):
        return KernelTable.get_router_data(route, 'dev')

    #  Given route information as returned by command 'ip route list', returns its protocol
    @staticmethod
    def get_route_protocol(route):
        try:
            return int(KernelTable.get_router_data(route, 'proto'))
        except ValueError:  # No protocol info
            return 0

    @staticmethod
    def get_router_data(route, keyword):
        route_list = route.split()
        for i in range(len(route_list)):
            if route_list[i] == keyword:
                return route_list[i + 1]
        return ''
