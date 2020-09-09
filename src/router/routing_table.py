import warnings
import copy

import conf.conf as conf
import general.utils as utils

'''
This classes represent the OSPF Routing Table and contain its data and operations

The RoutingTable class is the main class, holding one or more entries

The RoutingTableEntry class represents an entry of the routing table, holding information about the destination along 
with one or more paths to reach it

The RoutingTablePath class represents a path to reach a destination in the network and contains information about the 
path
'''


class RoutingTable:

    def __init__(self):
        self.entries = []

    def get_entry(self, destination_type, destination_id, area):
        for entry in self.entries:
            if (entry.destination_type == destination_type) & (entry.destination_id == destination_id) & (
                    entry.area == area):
                return entry
        return None

    def add_entry(self, destination_type, destination_id, prefix_length, options, area):
        entry = self.get_entry(destination_type, destination_id, area)
        if entry is None:
            entry = RoutingTableEntry(destination_type, destination_id, prefix_length, options, area)
            self.entries.append(entry)

    def delete_entry(self, destination_type, destination_id, area):
        if len(self.entries) > 0:
            entry_list_copy = copy.deepcopy(self.entries)
            for i in range(len(entry_list_copy)):
                entry = entry_list_copy[i]
                if (entry.destination_type == destination_type) & (entry.destination_id == destination_id) & (
                        entry.area == area):
                    del(self.entries[i])

    def delete_all_entries(self):
        self.entries = []

    def __str__(self):
        string = 'Entries: '
        for i in range(len(self.entries)):
            string += ' ' + str(i + 1) + ': {'
            string += self.entries[i].__str__() + '}'
        return string


class RoutingTableEntry:

    def __init__(self, destination_type, destination_id, prefix_length, options, area):
        is_valid, message = self.parameter_validation(destination_type, destination_id, prefix_length, options, area)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)
        self.destination_type = destination_type
        self.destination_id = destination_id
        self.prefix_length = prefix_length
        self.options = options
        self.area = area
        self.paths = []

    def get_path(self, outgoing_interface, next_hop_address, advertising_router):
        for path in self.paths:
            if (path.outgoing_interface == outgoing_interface) & (path.next_hop_address == next_hop_address) & (
                    path.advertising_router == advertising_router):
                return path
        return None

    def add_path(self, path_type, cost, type_2_cost, outgoing_interface, next_hop_address, advertising_router):
        warning = False
        if len(self.paths) > 0:
            if (self.paths[0].path_type != path_type) | (self.paths[0].cost != cost):
                warnings.warn("All paths for same routing table entry must have same path type and cost")
                warning = True
        path = RoutingTablePath(path_type, cost, type_2_cost, outgoing_interface, next_hop_address, advertising_router)
        if (not warning) & (self.get_path(outgoing_interface, next_hop_address, advertising_router) is None):
            self.paths.append(path)

    def delete_path(self, outgoing_interface, next_hop_address, advertising_router):
        if len(self.paths) > 0:
            path_list_copy = copy.deepcopy(self.paths)
            for i in range(len(path_list_copy)):
                path = path_list_copy[i]
                if (path.outgoing_interface == outgoing_interface) & (path.next_hop_address == next_hop_address) & (
                        path.advertising_router == advertising_router):
                    del(self.paths[i])

    def delete_all_paths(self):
        self.paths = []

    def __str__(self):
        string = 'Destination Type: ' + self.destination_type.__str__() + ' Destination ID: ' + \
                 self.destination_id.__str__() + ' Prefix Length: ' + self.prefix_length.__str__() + ' Options: ' + \
                 self.options.__str__() + ' Area: ' + self.area.__str__() + ' Paths: '
        for i in range(len(self.paths)):
            string += ' ' + str(i + 1) + ': {'
            string += self.paths[i].__str__() + '}'
        return string

    @staticmethod
    def parameter_validation(destination_type, destination_id, prefix_length, options, area):
        if destination_type not in [conf.DESTINATION_TYPE_ROUTER, conf.DESTINATION_TYPE_NETWORK]:
            return False, "Invalid Destination Type"
        if (not (utils.Utils.is_ipv4_address(destination_id) | utils.Utils.is_ipv6_address(destination_id))) | (
                destination_id == '0.0.0.0') | (destination_id == '::'):
            return False, "Invalid Destination ID"
        if (not (0 <= prefix_length <= 4 * conf.BYTE_SIZE)) & (utils.Utils.is_ipv4_address(destination_id)):
            return False, "Invalid Network Mask"
        if (not (0 <= prefix_length <= 16 * conf.BYTE_SIZE)) & (utils.Utils.is_ipv6_address(destination_id)):
            return False, "Invalid Network Mask"
        if not 0 <= options <= conf.MAX_VALUE_24_BITS:
            return False, "Invalid Optional Capabilities"
        if (not utils.Utils.is_ipv4_address(area)) & (area != ''):
            return False, "Invalid Area"
        return True, ''


class RoutingTablePath:

    def __init__(self, path_type, cost, type_2_cost, outgoing_interface, next_hop_address, advertising_router):
        is_valid, message = self.parameter_validation(
            path_type, cost, type_2_cost, outgoing_interface, next_hop_address, advertising_router)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)
        self.path_type = path_type
        self.cost = cost
        self.type_2_cost = type_2_cost
        self.outgoing_interface = outgoing_interface
        self.next_hop_address = next_hop_address
        self.advertising_router = advertising_router

    @staticmethod
    def parameter_validation(path_type, cost, type_2_cost, outgoing_interface, next_hop_address, advertising_router):
        if path_type not in [conf.INTRA_AREA_PATH, conf.INTER_AREA_PATH, conf.TYPE_1_EXTERNAL_PATH,
                             conf.TYPE_2_EXTERNAL_PATH]:
            return False, "Invalid Path Type"
        if cost < 0:
            return False, "Invalid Cost"
        if type_2_cost < 0:
            return False, "Invalid Type 2 Cost"
        if outgoing_interface == '':  # It should be an interface physical identifier (Ex: ens33)
            return False, "Invalid Outgoing Interface"
        if (next_hop_address != '') & (not utils.Utils.is_ipv4_address(next_hop_address)) & (
                not utils.Utils.is_ipv6_address(next_hop_address)):
            return False, "Invalid Next Hop Address"
        if (not utils.Utils.is_ipv4_address(advertising_router)) & (advertising_router != ''):
            return False, "Invalid Advertising Router"
        return True, ''

    def __str__(self):
        return 'Path Type: ' + self.path_type.__str__() + ' Cost: ' + self.cost.__str__() + ' Type 2 Cost: ' + \
               self.type_2_cost.__str__() + ' Outgoing Interface: ' + self.outgoing_interface.__str__() + \
               ' Next Hop Address: ' + self.next_hop_address.__str__() + ' Advertising Router: ' + \
               self.advertising_router.__str__()
