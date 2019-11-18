import threading

import neighbor.neighbor as neighbor
import packet.packet_creator as packet_creator
import conf.conf as conf
import general.timer as timer
import general.socket_python as socket_python

'''
This class represents the OSPF interface and contains its data and operations
'''


class Interface:
    #  OSPF interface parameters
    type = 0
    identifier = ''  # Ex: ens33
    ip_address = ''
    network_mask = ''
    area_id = ''
    hello_interval = 0
    router_dead_interval = 0
    router_priority = 0
    neighbors = None
    designated_router = ''
    backup_designated_router = ''
    cost = 0
    max_ip_datagram = 0

    #  Implementation-specific parameters
    socket = None  # Socket that will send packets
    pipeline = None  # For receiving incoming packets
    interface_shutdown = None  # Signals interface thread to shutdown
    packet_creator = None
    hello_thread = None

    #  Hello timer and its parameters
    hello_timer = None
    offset = 0
    timeout = None
    timer_shutdown = None
    timer_seconds = 0

    def __init__(self, identifier, ip_address, network_mask, area_id, pipeline, interface_shutdown):
        self.type = conf.BROADCAST_INTERFACE
        self.identifier = identifier
        self.ip_address = ip_address
        self.network_mask = network_mask
        self.area_id = area_id
        self.hello_interval = conf.HELLO_INTERVAL
        self.router_dead_interval = conf.ROUTER_DEAD_INTERVAL
        self.router_priority = conf.ROUTER_PRIORITY
        self.neighbors = {}
        self.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.cost = conf.INTERFACE_COST
        self.max_ip_datagram = conf.MTU

        self.socket = socket_python.Socket()
        self.pipeline = pipeline
        self.interface_shutdown = interface_shutdown
        packet_creator_parameters = [conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO, conf.ROUTER_ID, area_id,
                                     conf.NULL_AUTHENTICATION, conf.DEFAULT_AUTH]
        self.packet_creator = packet_creator.PacketCreator(packet_creator_parameters)

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
                packet = data_array[0]
                source_ip = data_array[1]
                version = packet.header.version
                packet_type = packet.header.packet_type

                if version == conf.VERSION_IPV4:
                    if packet_type == conf.PACKET_TYPE_HELLO:
                        #  New neighbor
                        neighbor_id = packet.header.router_id
                        if neighbor_id not in self.neighbors:
                            neighbor_options = packet.body.options
                            new_neighbor = neighbor.Neighbor(neighbor_id, neighbor_options)  # Neighbor state is Init
                            self.neighbors[neighbor_id] = new_neighbor

                        #  Existing neighbors
                        for n in self.neighbors:
                            if conf.ROUTER_ID in packet.body.neighbors:  # Neighbor acknowledges this router as neighbor
                                self.neighbors[n].set_neighbor_state(conf.NEIGHBOR_STATE_2_WAY)
                            else:  # Neighbor does not, even if it did in the last packets
                                self.neighbors[n].set_neighbor_state(conf.NEIGHBOR_STATE_INIT)

            #  Sends Hello packet
            if self.timeout.is_set():
                packet = self.create_packet()
                self.socket.send_ipv4(packet, conf.ALL_OSPF_ROUTERS_IPV4, self.identifier)
                self.timeout.clear()

        #  Interface signalled to shutdown
        self.shutdown_interface()

    #  Creates an OSPF packet to be sent
    def create_packet(self):
        return self.packet_creator.create_hello_v2_packet(self.network_mask, self.hello_interval, conf.OPTIONS,
                                                          self.router_priority, self.router_dead_interval,
                                                          self.designated_router, self.backup_designated_router,
                                                          self.neighbors)

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
