import threading
import time

import neighbor.neighbor as neighbor
import packet.packet as packet
import conf.conf as conf
import general.timer as timer
import general.sock as sock

'''
This class represents the OSPF interface and contains its data and operations
'''


class Interface:
    #  TODO: Allow router to operate with both OSPF versions at the same time
    version = 0

    #  OSPF interface parameters
    type = 0
    physical_identifier = ''  # Ex: ens33 - Interface identifier given by the OS
    ospf_identifier = 0  # Just for OSPFv3 - Interface identifier given by OSPF
    ip_address = ''  # Link-local address in OSPFv3
    network_mask = '0.0.0.0'  # Just for OSPFv2
    link_prefixes = []  # Just for OSPFv3
    area_id = '0.0.0.0'  # 0.0.0.0 - Backbone area
    hello_interval = 0
    router_dead_interval = 0
    router_priority = 0
    neighbors = None
    designated_router = '0.0.0.0'  # 0.0.0.0 - No DR known
    backup_designated_router = '0.0.0.0'
    cost = 0
    max_ip_datagram = 0
    instance_id = 0  # Just for OSPFv3 - Default is 0 TODO: Allow router to operate more than one instance of OSPFv3

    #  Implementation-specific parameters
    socket = None  # Socket that will send packets
    pipeline = None  # For receiving incoming packets
    interface_shutdown = None  # Signals interface thread to shutdown
    hello_packet_to_send = None
    hello_thread = None

    #  Hello timer and its parameters
    hello_timer = None
    offset = 0
    timeout = None
    timer_shutdown = None
    timer_seconds = 0

    def __init__(self, version, physical_identifier, ip_address, network_mask, link_prefixes, area_id, pipeline,
                 interface_shutdown):
        self.version = version

        self.type = conf.BROADCAST_INTERFACE
        self.physical_identifier = physical_identifier
        self.ospf_identifier = Interface.ospf_identifier_generator(self.physical_identifier, conf.INTERFACE_NAMES)
        self.ip_address = ip_address
        self.network_mask = network_mask
        self.link_prefixes = link_prefixes
        self.area_id = area_id
        self.hello_interval = conf.HELLO_INTERVAL
        self.router_dead_interval = conf.ROUTER_DEAD_INTERVAL
        self.router_priority = conf.ROUTER_PRIORITY
        self.neighbors = {}
        self.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.cost = conf.INTERFACE_COST
        self.max_ip_datagram = conf.MTU
        self.instance_id = 0

        self.socket = sock.Socket()
        self.pipeline = pipeline
        self.interface_shutdown = interface_shutdown
        self.hello_packet_to_send = packet.Packet()
        self.hello_packet_to_send.create_header_v2(conf.PACKET_TYPE_HELLO, conf.ROUTER_ID, area_id,
                                                   conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH)

        self.hello_timer = timer.Timer()
        self.timeout = threading.Event()
        self.timer_shutdown = threading.Event()
        self.timer_seconds = self.hello_interval

    #  Interface main method
    def interface_loop(self):
        #  Starts Hello timer
        self.hello_thread = threading.Thread(target=self.hello_timer.interval_timer,
                                             args=(self.offset, self.timeout, self.timer_shutdown, self.timer_seconds))
        self.hello_thread.start()
        self.timeout.set()  # If this thread reaches "if" below before losing CPU, it will immediately send Hello packet
        self.interface_shutdown.clear()

        while not(self.interface_shutdown.is_set()):  # Until interface is signalled to shutdown
            #  Deletes neighbors that reached timeout
            for n in list(self.neighbors):
                if self.neighbors[n].is_expired():  # Neighbors that reached timeout can be deleted
                    self.delete_neighbor(n)

            #  Processes incoming packets
            if not self.pipeline.empty():
                data_array = self.pipeline.get()
                incoming_packet = data_array[0]
                source_ip = data_array[1]
                version = incoming_packet.header.version
                packet_type = incoming_packet.header.packet_type

                if version == conf.VERSION_IPV4:
                    if packet_type == conf.PACKET_TYPE_HELLO:

                        neighbor_id = incoming_packet.header.router_id
                        #  New neighbor
                        if neighbor_id not in self.neighbors:
                            neighbor_options = incoming_packet.body.options
                            new_neighbor = neighbor.Neighbor(neighbor_id, 0, '::', neighbor_options, '0.0.0.0',
                                                             '0.0.0.0')  # Neighbor state is Init
                            self.neighbors[neighbor_id] = new_neighbor

                        # Existing neighbor
                        self.neighbors[neighbor_id].reset_timer()
                        time.sleep(0.1)
                        if conf.ROUTER_ID in incoming_packet.body.neighbors:  # Neighbor acknowledges router as neighbor
                            self.neighbors[neighbor_id].set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
                        else:  # Neighbor does not, even if it did in the last packets
                            self.neighbors[neighbor_id].set_neighbor_state(conf.NEIGHBOR_STATE_INIT)

            #  Sends Hello packet
            if self.timeout.is_set():
                packet_bytes = self.create_packet()
                self.socket.send_ipv4(packet_bytes, conf.ALL_OSPF_ROUTERS_IPV4, self.physical_identifier)
                self.timeout.clear()

        #  Interface signalled to shutdown
        self.shutdown_interface()

    #  Creates an OSPF packet to be sent
    def create_packet(self):
        self.hello_packet_to_send.create_hello_v2_packet_body(
            self.network_mask, self.hello_interval, conf.OPTIONS, self.router_priority, self.router_dead_interval,
            self.designated_router, self.backup_designated_router, self.neighbors)
        return self.hello_packet_to_send.pack_packet()

    #  Deletes a neighbor from the list of active neighbors
    def delete_neighbor(self, neighbor_id):
        if neighbor_id in self.neighbors:
            self.neighbors[neighbor_id].delete_neighbor()  # Stops neighbor timer thread
            self.neighbors.pop(neighbor_id)

    #  Performs shutdown operations on the interface
    def shutdown_interface(self):
        for n in self.neighbors:  # Stops timer thread in all neighbors
            self.neighbors[n].delete_neighbor()
        self.neighbors = {}  # Cleans neighbor list - It will be reconstructed if interface is reactivated
        self.timer_shutdown.set()
        self.hello_thread.join()

    #  Given interface physical identifier, returns an unique OSPF interface identifier
    @staticmethod
    def ospf_identifier_generator(physical_identifier, identifiers_tuple):
        if physical_identifier in identifiers_tuple:
            i = 1
            for identifier in identifiers_tuple:
                if identifier == physical_identifier:
                    return i
                i += 1
        return 0
