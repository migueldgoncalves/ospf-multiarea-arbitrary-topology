import threading
import queue
from datetime import datetime

import interface.interface as interface
import conf.conf as conf
import general.utils as utils
import area.lsdb as lsdb
import lsa.lsa as lsa

'''
This class represents the OSPF area and contains its data and operations, from the point of view of a router
'''

#  Elements of the list stored in the interfaces dictionary - The key is the interface identifier (Ex: ens33)
INTERFACE_OBJECT = 0
INTERFACE_THREAD = 1
PIPELINE = 2
SHUTDOWN_EVENT = 3


class Area:

    def __init__(self, router_id, ospf_version, area_id, external_routing_capable, interfaces, localhost, is_abr):
        if ospf_version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
            raise ValueError("Invalid OSPF version")
        if not utils.Utils.is_ipv4_address(area_id):
            raise ValueError("Invalid Area ID")
        self.router_id = router_id
        self.ospf_version = ospf_version
        self.area_id = area_id  # 0.0.0.0 - Backbone area
        self.interfaces = {}  # Contains as key their identifier, and as value the list above mentioned
        self.external_routing_capable = external_routing_capable
        self.is_abr = is_abr  # True if router is ABR

        #  LSDB initialization
        self.database = Area.lsdb_startup(self.router_id, self.ospf_version, self.area_id, self.is_abr, interfaces)

        #  Creates the interfaces that belong to this area
        self.localhost = localhost
        for i in range(len(interfaces)):
            self.create_interface(interfaces[i])

    #  Creates and populates LSDB with LSAs that should be in it on startup
    @staticmethod
    def lsdb_startup(router_id, version, area_id, is_abr, physical_ids):
        database = lsdb.Lsdb(version, area_id)
        router_lsa = lsa.Lsa()
        if version == conf.VERSION_IPV4:
            link_state_id = router_id
            options = 0
        else:
            link_state_id = '0.0.0.0'
            options = conf.OPTIONS
        router_lsa.create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_ROUTER, link_state_id, router_id,
                                 conf.INITIAL_SEQUENCE_NUMBER, version)
        router_lsa.create_router_lsa_body(False, False, is_abr, options, version)
        if version == conf.VERSION_IPV4:
            for identifier in physical_ids:
                prefix = utils.Utils.interface_name_to_ipv4_prefix_and_length(identifier)[0]
                netmask = utils.Utils.interface_name_to_ipv4_network_mask(identifier)
                cost = conf.INTERFACE_COST
                router_lsa.add_link_info_v2(prefix, netmask, conf.LINK_TO_STUB_NETWORK, conf.DEFAULT_TOS, cost)
        database.add_lsa(router_lsa, None)

        if version == conf.VERSION_IPV6:
            intra_area_prefix_lsa = lsa.Lsa()
            referenced_ls_type = router_lsa.header.ls_type
            referenced_link_state_id = router_lsa.header.link_state_id
            referenced_advertising_router = router_lsa.header.advertising_router
            intra_area_prefix_lsa.create_header(
                conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_INTRA_AREA_PREFIX, link_state_id, router_id,
                conf.INITIAL_SEQUENCE_NUMBER, version)
            intra_area_prefix_lsa.create_intra_area_prefix_lsa_body(referenced_ls_type, referenced_link_state_id,
                                                                    referenced_advertising_router)
            for identifier in physical_ids:
                prefix_data = utils.Utils.interface_name_to_ipv6_prefix_and_length(identifier)
                prefix_length = prefix_data[1]
                prefix_options = conf.PREFIX_OPTIONS
                metric = conf.INTERFACE_COST
                prefix = prefix_data[0]
                intra_area_prefix_lsa.add_prefix_info(
                    prefix_length, prefix_options, metric, prefix, conf.LSA_TYPE_INTRA_AREA_PREFIX)
            database.add_lsa(intra_area_prefix_lsa, None)
        return database

    #  Creates and starts an interface associated with this area
    def create_interface(self, interface_id):
        if interface_id in self.interfaces:
            print(datetime.now().time(), self.router_id + ": OSPFv" + str(self.ospf_version), "interface", interface_id,
                  "is already created")
            return

        pipeline = queue.Queue()
        shutdown = threading.Event()
        if self.ospf_version == conf.VERSION_IPV4:
            ip_address = utils.Utils.interface_name_to_ipv4_address(interface_id)
            network_mask = utils.Utils.interface_name_to_ipv4_network_mask(interface_id)
            new_interface = interface.Interface(
                self.router_id, interface_id, ip_address, '', network_mask, [], self.area_id, pipeline, shutdown,
                self.ospf_version, self.database, self.localhost, self.is_abr)
        else:
            ip_address = utils.Utils.interface_name_to_ipv6_link_local_address(interface_id)
            link_prefix = utils.Utils.interface_name_to_ipv6_prefix_and_length(interface_id)
            new_interface = interface.Interface(
                self.router_id, interface_id, '', ip_address, '', [link_prefix], self.area_id, pipeline, shutdown,
                self.ospf_version, self.database, self.localhost, self.is_abr)

        interface_thread = threading.Thread(target=new_interface.interface_loop)

        #  Adds data and objects to the interfaces dictionary
        self.interfaces[interface_id] = [new_interface, interface_thread, pipeline, shutdown]

        shutdown.set()  # Interface is down when created
        self.start_interface(interface_id)

    #  Starts a specified interface, whether for the first time or after being shutdown
    def start_interface(self, interface_id):
        interface_data = self.interfaces[interface_id]
        starting_interface = interface_data[INTERFACE_OBJECT]
        if not self.is_interface_operating(interface_id):  # If not operating
            interface_data[INTERFACE_THREAD] = threading.Thread(target=starting_interface.interface_loop)
            interface_data[PIPELINE].queue.clear()  # Clears interface thread pipeline
            interface_data[SHUTDOWN_EVENT].clear()  # Resets shutdown event of interface thread
            interface_data[INTERFACE_THREAD].start()
            print(datetime.now().time(), self.router_id + ": OSPFv" + str(self.ospf_version), "interface", interface_id,
                  "started")
        else:
            print(datetime.now().time(), self.router_id + ": OSPFv" + str(self.ospf_version), "interface", interface_id,
                  "is already operating")

    #  Performs shutdown of a specified interface
    def shutdown_interface(self, interface_id):
        interface_data = self.interfaces[interface_id]
        if self.is_interface_operating(interface_id):  # If operating
            interface_data[SHUTDOWN_EVENT].set()  # Signals interface thread to shutdown
            interface_data[INTERFACE_THREAD].join()
            interface_data[PIPELINE].queue.clear()
            print(datetime.now().time(), self.router_id + ": OSPFv" + str(self.ospf_version), "interface", interface_id,
                  "successfully shutdown")
        else:
            print(datetime.now().time(), self.router_id + ": OSPFv" + str(self.ospf_version), "interface", interface_id,
                  "is already down")

    #  Shutdown event is set when interface should stop operating
    def is_interface_operating(self, interface_id):
        return not self.interfaces[interface_id][SHUTDOWN_EVENT].is_set()

    #  Returns area interfaces in a list
    def get_interfaces(self):
        interface_list = []
        for i in self.interfaces:
            interface_list.append(self.interfaces[i][INTERFACE_OBJECT])
        return interface_list

    #  Ensures area is down, and with it all of its interfaces
    def shutdown_area(self):
        for i in self.interfaces:
            self.shutdown_interface(i)
