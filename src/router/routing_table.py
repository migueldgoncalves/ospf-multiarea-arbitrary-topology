import warnings
import copy

import conf.conf as conf
import general.utils as utils

'''
This classes represent the OSPF Routing Table and contain its data and operations
'''


class RoutingTable:

    def __init__(self):
        self.entries = []

    def get_entry(self, destination_type, destination_id, area):
        for entry in self.entries:
            if (entry.destination_type == destination_type) & (entry.destination_id == destination_id) & (
                    entry.area == area):
                return entry

    def add_entry(self, destination_type, destination_id, address_mask, options, area):
        entry = RoutingTableEntry(destination_type, destination_id, address_mask, options, area)
        if not (entry in self.entries):
            self.entries.append(entry)

    def delete_entry(self, destination_type, destination_id, area):
        for entry in copy.deepcopy(self.entries):
            if (entry.destination_type == destination_type) & (entry.destination_id == destination_id) & (
                    entry.area == area):
                self.entries.remove(entry)


class RoutingTableEntry:

    def __init__(self, destination_type, destination_id, address_mask, options, area):
        is_valid, message = self.parameter_validation(destination_type, destination_id, address_mask, options, area)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)
        self.destination_type = destination_type
        self.destination_id = destination_id
        self.address_mask = address_mask
        self.options = options
        self.area = area
        self.paths = []

    def get_path(self, next_hop, advertising_router):
        for path in self.paths:
            if (path.next_hop == next_hop) & (path.advertising_router == advertising_router):
                return path

    def add_path(self, path_type, cost, type_2_cost, next_hop, advertising_router):
        warning = False
        if len(self.paths) > 0:
            if (self.paths[0].path_type != path_type) | (self.paths[0].cost != cost):
                warnings.warn("All paths for same routing table entry must have same path type and cost")
                warning = True
        path = RoutingTablePath(path_type, cost, type_2_cost, next_hop, advertising_router)
        if (not warning) & (path not in self.paths):
            self.paths.append(path)

    def remove_path(self, next_hop, advertising_router):
        if len(self.paths) > 0:
            for path in copy.deepcopy(self.paths):
                if (path.next_hop == next_hop) & (path.advertising_router == advertising_router):
                    self.paths.remove(path)

    @staticmethod
    def parameter_validation(destination_type, destination_id, address_mask, options, area):
        if destination_type not in [conf.DESTINATION_TYPE_ROUTER, conf.DESTINATION_TYPE_NETWORK]:
            return False, "Invalid Destination Type"
        if (not utils.Utils.is_ipv4_address(destination_id)) | (destination_id == '0.0.0.0'):
            return False, "Invalid Destination ID"
        if (not utils.Utils.is_ipv4_network_mask(address_mask)) & (destination_type == conf.DESTINATION_TYPE_NETWORK):
            return False, "Invalid Network Mask"
        if not 0 <= options <= conf.MAX_VALUE_24_BITS:
            return False, "Invalid Optional Capabilities"
        if (not utils.Utils.is_ipv4_address(area)) & (area != ''):
            return False, "Invalid Area"
        return True, ''


class RoutingTablePath:

    def __init__(self, path_type, cost, type_2_cost, next_hop, advertising_router):
        is_valid, message = self.parameter_validation(path_type, cost, type_2_cost, next_hop, advertising_router)
        if not is_valid:  # At least one of the parameters failed validation
            raise ValueError(message)
        self.path_type = path_type
        self.cost = cost
        self.type_2_cost = type_2_cost
        self.next_hop = next_hop
        self.advertising_router = advertising_router

    @staticmethod
    def parameter_validation(path_type, cost, type_2_cost, next_hop, advertising_router):
        if path_type not in [conf.INTRA_AREA_PATH, conf.INTER_AREA_PATH, conf.TYPE_1_EXTERNAL_PATH,
                             conf.TYPE_2_EXTERNAL_PATH]:
            return False, "Invalid Path Type"
        if cost < 0:
            return False, "Invalid Cost"
        if type_2_cost < 0:
            return False, "Invalid Type 2 Cost"
        if (len(next_hop) != 2) | (next_hop[0] == ''):
            return False, "Invalid Next Hop"
        if (not utils.Utils.is_ipv4_address(advertising_router)) & (advertising_router != ''):
            return False, "Invalid Advertising Router"
        return True, ''
