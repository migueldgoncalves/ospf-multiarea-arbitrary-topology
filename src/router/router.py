import queue
import threading

import general.utils as utils
import general.sock as sock
import conf.conf as conf
import area.area as area

'''
This class contains the top-level OSPF data structures and operations
'''


class Router:
    #  TODO: Allow router to operate with both OSPF versions at the same time
    ospf_version = 0

    #  OSPF top-level parameters
    router_id = '0.0.0.0'
    areas = {}
    interfaces = {}
    max_ip_datagram = 0

    #  Implementation-specific parameters
    receiving_socket = None
    pipelines = {}
    shutdown_events = {}
    threads = {}

    utils = utils.Utils()

    def __init__(self, ospf_version):
        if ospf_version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
            raise ValueError("Invalid OSPF version")
        self.ospf_version = ospf_version

        self.router_id = conf.ROUTER_ID
        self.areas = {}
        area_ids = list(set(conf.INTERFACE_AREAS))
        external_routing_capable = False
        for area_id in area_ids:
            new_area = area.Area(self.ospf_version, area_id, external_routing_capable)
            self.areas[area_id] = new_area
        self.interfaces = {}
        for area_id in self.areas:
            for interface_id in self.areas[area_id].interfaces:
                self.interfaces[interface_id] = self.areas[area_id].interfaces[interface_id]
        self.max_ip_datagram = conf.MTU

        self.receiving_socket = sock.Socket()
        self.pipelines = {}
        for interface_id in self.interfaces:
            self.pipelines[interface_id] = queue.Queue()
        self.shutdown_events = {}
        for interface_id in self.interfaces:
            self.shutdown_events[interface_id] = threading.Event()
        self.threads = {}
        accept_self_packets = False
        is_dr = False
        for interface_id in self.interfaces:
            if self.ospf_version == conf.VERSION_IPV4:
                self.threads[interface_id] = threading.Thread(
                    target=self.receiving_socket.receive_ipv4,
                    args=(self.pipelines[interface_id], self.shutdown_events[interface_id], interface_id,
                          accept_self_packets, is_dr))
            else:
                self.threads[interface_id] = threading.Thread(
                    target=self.receiving_socket.receive_ipv6,
                    args=(self.pipelines[interface_id], self.shutdown_events[interface_id], interface_id,
                          accept_self_packets, is_dr))
            self.threads[interface_id].start()

    #  TODO: Process incoming packets and send them to the proper interfaces

    #  Ensures router is down, and with it all of its area data structures and interfaces
    def shutdown_router(self):
        for s in self.shutdown_events:
            self.shutdown_events[s].set()
        for t in self.threads:
            self.threads[t].join()
        for a in self.areas:
            self.areas[a].shutdown_area()
