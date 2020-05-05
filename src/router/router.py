import queue
import threading
import datetime

import general.utils as utils
import general.sock as sock
import conf.conf as conf
import area.area as area
import packet.packet as packet

'''
This class contains the top-level OSPF data structures and operations
'''


class Router:
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
    router_shutdown_event = None
    start_time = 0

    def __init__(self, ospf_version, command_pipeline, router_shutdown_event):
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
        self.router_shutdown_event = router_shutdown_event
        self.start_time = datetime.datetime.now()

    #  OSPF router main loop
    def main_loop(self):
        while not (self.router_shutdown_event.is_set()):  # Until router is signalled to shutdown
            #  Sends received packets to receiving interface
            for interface_id in self.packet_pipelines:
                pipeline = self.packet_pipelines[interface_id]
                if not pipeline.empty():
                    packet_data = pipeline.get()
                    packet_bytes = packet_data[0]
                    source_ip = packet_data[1]
                    received_packet = packet.Packet.unpack_packet(packet_bytes)
                    interface_pipeline = self.interfaces[interface_id][area.PIPELINE]
                    interface_pipeline.put([received_packet, source_ip])

            #  For each LSA, increases LS Age field if enough time has passed
            for a in self.areas:
                area_interfaces = self.areas[a].get_interfaces()
                self.areas[a].database.increase_lsa_age(area_interfaces)

        #  Router signalled to shutdown
        self.shutdown_router()

    #  Prints general protocol information
    def show_general_data(self):
        time_elapsed = datetime.datetime.now() - self.start_time
        print("RID", self.router_id)
        print("Start time:", str(datetime.time(self.start_time.hour, self.start_time.minute, self.start_time.second)) +
              ", Time elapsed:", str(datetime.timedelta(seconds=int(time_elapsed.total_seconds()))))
        for a in self.areas:
            if a == '0.0.0.0':
                print("Area BACKBONE")
            else:
                print("Area", a)
            print("\tNumber of interfaces in this area is", len(self.areas[a].interfaces))
            for i in self.areas[a].interfaces:
                print("\t\t" + i)

    #  Prints interface information
    def show_interface_data(self):
        for a in self.areas:
            for i in self.areas[a].interfaces:
                if self.areas[a].is_interface_operating(i):
                    print("Interface", i, "is up, line protocol is up")
                else:
                    print("Interface", i, "is up, line protocol is down")

                if self.ospf_version == conf.VERSION_IPV4:
                    ip_address = utils.Utils.get_ipv4_address_from_interface_name(i)
                    prefix_length = str(utils.Utils.get_ipv4_prefix_from_interface_name(i)[1])
                    print("\tInternet Address", ip_address + "/" + prefix_length + ", Area", a)
                    cost = self.interfaces[i][0].cost
                    print("\tProcess ID 1, Router ID", self.router_id + ", Network Type BROADCAST, Cost:", cost)
                else:
                    link_local_address = utils.Utils.get_ipv6_link_local_address_from_interface_name(i)
                    interface_id = self.interfaces[i][0].ospf_identifier
                    print("\tLink Local Address", link_local_address + ", Interface ID", interface_id)
                    print("\tArea", a + ", Process ID 1, Instance ID 0, Router ID", self.router_id)
                    cost = self.interfaces[i][0].cost
                    print("\tNetwork Type BROADCAST, Cost:", cost)

                print("\tTimer intervals configured, Hello " + str(conf.HELLO_INTERVAL) + ", Dead",
                      conf.ROUTER_DEAD_INTERVAL)
                if self.areas[a].is_interface_operating(i):
                    time_to_hello = self.interfaces[i][0].hello_timer.get_timer_time()
                    print("\t\tHello due in", str(datetime.timedelta(seconds=time_to_hello)))
                    neighbor_count = self.interfaces[i][0].get_neighbor_count()
                    adjacent_neighbor_count = self.interfaces[i][0].get_adjacent_neighbor_count()
                    print("\tNeighbor Count is", str(neighbor_count) + ", Adjacent neighbor count is",
                          adjacent_neighbor_count)
                    for n in self.interfaces[i][0].neighbors:
                        print("\t\tAdjacent with neighbor", n)

    #  Prints neighbor information
    def show_neighbor_data(self):
        for i in self.interfaces:
            neighbors = self.interfaces[i][0].neighbors
            if self.ospf_version == conf.VERSION_IPV4:
                print("Neighbor ID\tState\t\tDead Time\tAddress\t\tInterface")
            else:
                print("Neighbor ID\tState\t\tDead Time\tInterface ID\tInterface")
            for n in neighbors:
                neighbor_state = neighbors[n].neighbor_state
                dead_time = str(datetime.timedelta(seconds=neighbors[n].inactivity_timer.get_timer_time()))
                neighbor_address = neighbors[n].neighbor_ip_address
                neighbor_interface_id = neighbors[n].neighbor_interface_id
                if self.ospf_version == conf.VERSION_IPV4:
                    print(n + "\t\t" + neighbor_state + "\t\t" + dead_time + "\t\t" + neighbor_address + "\t" + i)
                else:
                    print(n + "\t\t" + neighbor_state + "\t\t" + dead_time + "\t\t" + str(neighbor_interface_id) +
                          "\t\t" + i)

    #  Performs shutdown of specified interface
    def shutdown_interface(self, physical_identifier):
        if physical_identifier not in self.interfaces:
            print("OSPFv" + str(self.ospf_version), "interface not found")
        for a in self.areas:
            if physical_identifier in self.areas[a].interfaces:
                self.areas[a].shutdown_interface(physical_identifier)

    #  Starts specified interface
    def start_interface(self, physical_identifier):
        if physical_identifier not in self.interfaces:
            print("OSPFv" + str(self.ospf_version), "interface not found")
        for a in self.areas:
            if physical_identifier in self.areas[a].interfaces:
                self.areas[a].start_interface(physical_identifier)

    #  Ensures router is down, and with it all of its area data structures and interfaces
    def shutdown_router(self):
        for s in self.interface_shutdown_events:
            self.interface_shutdown_events[s].set()
        for t in self.interface_threads:
            self.interface_threads[t].join()
        for a in self.areas:
            self.areas[a].shutdown_area()
