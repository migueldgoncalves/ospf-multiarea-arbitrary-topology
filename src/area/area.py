import threading
import queue

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

    def __init__(self, ospf_version, area_id, external_routing_capable):
        if ospf_version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
            raise ValueError("Invalid OSPF version")
        if not utils.Utils.is_ipv4_address(area_id):
            raise ValueError("Invalid Area ID")
        self.ospf_version = ospf_version
        self.area_id = area_id  # 0.0.0.0 - Backbone area
        self.interfaces = {}  # Contains as key their identifier, and as value the list above mentioned
        self.external_routing_capable = external_routing_capable

        #  LSDB initialization
        self.database = lsdb.Lsdb()
        router_lsa = lsa.Lsa()
        if ospf_version == conf.VERSION_IPV4:
            link_state_id = conf.ROUTER_ID
        else:
            link_state_id = '0.0.0.0'
        router_lsa.create_header(conf.INITIAL_LS_AGE, conf.OPTIONS, conf.LSA_TYPE_ROUTER, link_state_id, conf.ROUTER_ID,
                                 conf.INITIAL_SEQUENCE_NUMBER, ospf_version)
        if ospf_version == conf.VERSION_IPV4:
            options = 0
        else:
            options = conf.OPTIONS
        router_lsa.create_router_lsa_body(False, False, False, options, ospf_version)
        self.database.add_lsa(router_lsa)

        #  Creates the interfaces that belong to this area
        interface_list = conf.INTERFACE_NAMES
        interface_areas = conf.INTERFACE_AREAS
        for i in range(len(interface_list)):
            if interface_areas[i] == self.area_id:  # If an interface belonging to this area is found in configurations
                self.create_interface(interface_list[i])

    #  Creates and starts an interface associated with this area
    def create_interface(self, interface_id):
        if interface_id in self.interfaces:
            print("OSPFv" + str(self.ospf_version), "interface", interface_id, "is already created")
            return

        pipeline = queue.Queue()
        shutdown = threading.Event()
        if self.ospf_version == conf.VERSION_IPV4:
            ip_address = utils.Utils.get_ipv4_address_from_interface_name(interface_id)
            network_mask = utils.Utils.get_ipv4_network_mask_from_interface_name(interface_id)
            new_interface = interface.Interface(interface_id, ip_address, '', network_mask, [], self.area_id,
                                                pipeline, shutdown, self.ospf_version, self.database)
        else:
            ip_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(interface_id)
            link_prefix = utils.Utils.get_ipv6_prefix_from_interface_name(interface_id)
            new_interface = interface.Interface(interface_id, '', ip_address, '', [link_prefix],
                                                self.area_id, pipeline, shutdown, self.ospf_version, self.database)

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
            print("OSPFv" + str(self.ospf_version), "interface", interface_id, "started")
        else:
            print("OSPFv" + str(self.ospf_version), "interface", interface_id, "is already operating")

    #  Performs shutdown of a specified interface
    def shutdown_interface(self, interface_id):
        interface_data = self.interfaces[interface_id]
        if self.is_interface_operating(interface_id):  # If operating
            interface_data[SHUTDOWN_EVENT].set()  # Signals interface thread to shutdown
            interface_data[INTERFACE_THREAD].join()
            interface_data[PIPELINE].queue.clear()
            print("OSPFv" + str(self.ospf_version), "interface", interface_id, "successfully shutdown")
        else:
            print("OSPFv" + str(self.ospf_version), "interface", interface_id, "is already down")

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
