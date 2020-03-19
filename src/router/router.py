import queue
import threading

import general.utils as utils
import general.sock as sock
import conf.conf as conf
import area.area as area
import packet.packet as packet

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
    packet_socket = None
    packet_pipelines = {}
    interface_shutdown_events = {}
    interface_threads = {}
    command_pipeline = None
    data_pipeline = None
    router_shutdown_event = None

    utils = utils.Utils()

    def __init__(self, ospf_version, command_pipeline, data_pipeline, router_shutdown_event):
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

        self.packet_socket = sock.Socket()
        self.packet_pipelines = {}
        for interface_id in self.interfaces:
            self.packet_pipelines[interface_id] = queue.Queue()
        self.interface_shutdown_events = {}
        for interface_id in self.interfaces:
            self.interface_shutdown_events[interface_id] = threading.Event()
        self.interface_threads = {}
        accept_self_packets = False
        is_dr = False
        for interface_id in self.interfaces:
            if self.ospf_version == conf.VERSION_IPV4:
                self.interface_threads[interface_id] = threading.Thread(
                    target=self.packet_socket.receive_ipv4,
                    args=(self.packet_pipelines[interface_id], self.interface_shutdown_events[interface_id],
                          interface_id, accept_self_packets, is_dr))
            else:
                self.interface_threads[interface_id] = threading.Thread(
                    target=self.packet_socket.receive_ipv6,
                    args=(self.packet_pipelines[interface_id], self.interface_shutdown_events[interface_id],
                          interface_id, accept_self_packets, is_dr))
            self.interface_threads[interface_id].start()
        self.command_pipeline = command_pipeline
        self.data_pipeline = data_pipeline
        self.router_shutdown_event = router_shutdown_event

    #  OSPF router main loop
    def main_loop(self):
        while not (self.router_shutdown_event.is_set()):  # Until router is signalled to shutdown
            for interface_id in self.packet_pipelines:
                pipeline = self.packet_pipelines[interface_id]
                if not pipeline.empty():
                    packet_data = pipeline.get()
                    packet_bytes = packet_data[0]
                    source_ip = packet_data[1]
                    received_packet = packet.Packet.unpack_packet(packet_bytes)
                    interface_pipeline = self.interfaces[interface_id][area.PIPELINE]
                    interface_pipeline.put([received_packet, source_ip])

        #  Router signalled to shutdown
        self.shutdown_router()

    #  Ensures router is down, and with it all of its area data structures and interfaces
    def shutdown_router(self):
        for s in self.interface_shutdown_events:
            self.interface_shutdown_events[s].set()
        for t in self.interface_threads:
            self.interface_threads[t].join()
        for a in self.areas:
            self.areas[a].shutdown_area()
