import threading
import queue

import interface.interface as interface
import conf.conf as conf
import general.utils as utils

'''
This class represents the OSPF area and contains its data and operations, from the point of view of a router
'''

#  Elements of the list stored in the interfaces dictionary - The key is the interface identifier (Ex: ens33)
INTERFACE_OBJECT = 0
INTERFACE_THREAD = 1
PIPELINE = 2
SHUTDOWN_EVENT = 3


class Area:
    #  TODO: Allow router to operate with both OSPF versions at the same time
    version = 0

    area_id = '0.0.0.0'  # 0.0.0.0 - Backbone area
    interfaces = {}  # Contains as key their identifier, and as value the list above mentioned
    external_routing_capable = False

    utils = utils.Utils()

    def __init__(self, area_id, external_routing_capable):
        self.version = conf.VERSION_IPV4
        if not self.utils.is_ipv4_address(area_id):
            raise ValueError("Invalid Area ID")
        self.area_id = area_id
        self.external_routing_capable = external_routing_capable

        #  Creates the interfaces that belong to this area
        interface_list = conf.INTERFACE_NAMES
        interface_areas = conf.INTERFACE_AREAS
        for i in range(len(interface_list)):
            if interface_areas[i] == self.area_id:  # If an interface belonging to this area is found in configurations
                self.create_interface(interface_list[i])

    #  Creates and starts an interface associated with this area
    def create_interface(self, interface_id):
        if interface_id in self.interfaces:
            print("Interface", interface_id, "is already created")
            return

        pipeline = queue.Queue()
        shutdown = threading.Event()
        if self.version == conf.VERSION_IPV4:
            ip_address = self.utils.get_ipv4_address_from_interface_name(interface_id)
            network_mask = self.utils.get_ipv4_network_mask_from_interface_name(interface_id)
            new_interface = interface.Interface(conf.VERSION_IPV4, interface_id, ip_address, network_mask, self.area_id,
                                                pipeline, shutdown)
        else:
            pass
            #  TODO

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
            print("Interface", interface_id, "started")
        else:
            print("Interface", interface_id, "is already operating")

    #  Shutdowns a specified interface
    def shutdown_interface(self, interface_id):
        interface_data = self.interfaces[interface_id]
        if self.is_interface_operating(interface_id):  # If operating
            interface_data[SHUTDOWN_EVENT].set()  # Signals interface thread to shutdown
            interface_data[INTERFACE_THREAD].join()
            interface_data[PIPELINE].queue.clear()
            print("Interface", interface_id, "successfully shutdown")
        else:
            print("Interface", interface_id, "is already down")

    #  Shutdown event is set when interface should stop operating
    def is_interface_operating(self, interface_id):
        return not self.interfaces[interface_id][SHUTDOWN_EVENT].is_set()

    #  Ensures area is down, and with it all of its interfaces
    def shutdown_area(self):
        for i in self.interfaces:
            self.shutdown_interface(i)
