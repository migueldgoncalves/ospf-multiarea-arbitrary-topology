import time
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

    router_id = '0.0.0.0'
    areas = {}
    interfaces = {}
    max_ip_datagram = 0

    receiving_socket = None
    pipeline = {}
    shutdown = {}
    thread = {}

    utils = utils.Utils()

    def __init__(self, ospf_version):
        self.ospf_version = ospf_version

        self.router_id = conf.ROUTER_ID
        area_ids = list(set(conf.INTERFACE_AREAS))
        external_routing_capable = False
        for area_id in area_ids:
            new_area = area.Area(self.ospf_version, area_id, external_routing_capable)
            self.areas[area_id] = new_area
        time.sleep(1)  # Required for giving CPU to other threads
        for a in self.areas:
            for i in a.interfaces:
                self.interfaces[i.interface_id] = i
        self.max_ip_datagram = conf.MTU

        self.receiving_socket = sock.Socket()
        for i in self.interfaces:
            self.pipeline[i.interface_id] = queue.Queue()
        for i in self.interfaces:
            self.shutdown[i.interface_id] = threading.Event()
        accept_self_packets = False
        is_dr = False
        for i in self.interfaces:
            if self.ospf_version == conf.VERSION_IPV4:
                self.thread[i.interface_id] = threading.Thread(
                    target=self.receiving_socket.receive_ipv4,
                    args=(self.pipeline, self.shutdown, i.interface_id, accept_self_packets, is_dr))
            else:
                self.thread[i.interface_id] = threading.Thread(
                    target=self.receiving_socket.receive_ipv6,
                    args=(self.pipeline, self.shutdown, i.interface_id, accept_self_packets, is_dr))
            self.thread[i.interface_id].start()
