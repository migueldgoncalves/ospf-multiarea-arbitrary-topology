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
        self.neighbors = []
        self.designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.backup_designated_router = conf.DEFAULT_DESIGNATED_ROUTER
        self.cost = conf.INTERFACE_COST
        self.max_ip_datagram = conf.MTU

        self.socket = socket_python.Socket()
        self.pipeline = pipeline
        self.interface_shutdown = interface_shutdown
        packet_creator_parameters = [conf.VERSION_IPV4, conf.PACKET_TYPE_HELLO, conf.ROUTER_ID, area_id,
                                     conf.AUTH_TYPE, conf.AUTHENTICATION]
        self.packet_creator = packet_creator.PacketCreator(packet_creator_parameters)

        self.hello_timer = timer.Timer()
        self.timeout = threading.Event()
        self.timer_shutdown = threading.Event()
        self.timer_seconds = self.hello_interval

        #  Starts Hello timer
        self.hello_thread = threading.Thread(target=self.hello_timer.interval_timer,
                                             args=(self.offset, self.timeout, self.timer_shutdown, self.timer_seconds))
        self.hello_thread.start()

    #  Interface main method
    def interface_loop(self):
        self.timeout.set()  # If this thread reaches "if" below before losing CPU, it will immediately send Hello packet
        while not(self.interface_shutdown.is_set()):
            #  Sends Hello packet
            if self.timeout.is_set():
                packet = self.create_packet()
                self.socket.send_ipv4(packet, conf.ALL_OSPF_ROUTERS_IPV4, self.identifier)
                self.timeout.clear()

        #  Interface signalled to shutdown
        self.timer_shutdown.set()
        self.hello_thread.join()

    #  Creates an OSPF packet to be sent
    def create_packet(self):
        return self.packet_creator.create_hello_v2_packet(self.network_mask, self.hello_interval, conf.OPTIONS,
                                                          self.router_priority, self.router_dead_interval,
                                                          self.designated_router, self.backup_designated_router,
                                                          self.neighbors)
