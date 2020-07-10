import queue
import threading
import datetime
import time

import general.utils as utils
import general.sock as sock
import conf.conf as conf
import area.area as area
import packet.packet as packet
import lsa.lsa as lsa
import lsa.header as header

'''
This class contains the top-level OSPF data structures and operations
'''


class Router:

    def __init__(self, router_id, ospf_version, router_shutdown_event, interface_ids, area_ids, localhost):
        if ospf_version not in [conf.VERSION_IPV4, conf.VERSION_IPV6]:
            raise ValueError("Invalid OSPF version")
        self.ospf_version = ospf_version

        #  Localhost operation parameters - Only for test purposes

        self.localhost = localhost  # If router is operating on localhost or not - If False router operates normally
        self.interface_ids = interface_ids  # Interfaces in this machine
        self.area_ids = area_ids  # OSPF areas of the interfaces

        #  OSPF top-level parameters

        self.router_id = router_id
        self.areas = {}
        external_routing_capable = False
        for area_id in self.area_ids:
            new_area = area.Area(self.router_id, self.ospf_version, area_id, external_routing_capable,
                                 self.interface_ids, self.area_ids, self.localhost)
            self.areas[area_id] = new_area
        self.interfaces = {}
        for area_id in self.area_ids:
            for interface_id in self.areas[area_id].interfaces:
                self.interfaces[interface_id] = self.areas[area_id].interfaces[interface_id]
        self.max_ip_datagram = conf.MTU

        #  Implementation-specific parameters

        self.packet_socket = sock.Socket()
        self.packet_pipelines = {}
        for interface_id in self.interfaces:
            self.packet_pipelines[interface_id] = queue.Queue()
        self.socket_shutdown_events = {}
        for interface_id in self.interfaces:
            self.socket_shutdown_events[interface_id] = threading.Event()
        self.socket_threads = {}
        accept_self_packets = False
        is_dr = False
        for interface_id in self.interfaces:
            if self.ospf_version == conf.VERSION_IPV4:
                self.socket_threads[interface_id] = threading.Thread(
                    target=self.packet_socket.receive_ipv4,
                    args=(self.packet_pipelines[interface_id], self.socket_shutdown_events[interface_id], interface_id,
                          accept_self_packets, is_dr, localhost))
            else:
                self.socket_threads[interface_id] = threading.Thread(
                    target=self.packet_socket.receive_ipv6,
                    args=(self.packet_pipelines[interface_id], self.socket_shutdown_events[interface_id], interface_id,
                          accept_self_packets, is_dr, localhost))
            self.socket_threads[interface_id].start()
        self.router_shutdown_event = router_shutdown_event
        self.start_time = datetime.datetime.now()

    #  OSPF router main loop
    def main_loop(self):
        while not self.router_shutdown_event.is_set():  # Until router is signalled to shutdown
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

            #  Searches for LSAs to flood and floods them through the proper interfaces
            for a in self.areas:
                current_area = self.areas[a]
                for i in current_area.interfaces:
                    current_interface = current_area.interfaces[i][area.INTERFACE_OBJECT]
                    if not current_interface.flooding_pipeline.empty():  # Interface has LSA to flood
                        data = current_interface.flooding_pipeline.get()
                        lsa_instance = data[0]
                        lsa_identifier = lsa_instance.get_lsa_identifier()
                        sending_neighbor_id = data[1]  # Can be this router ID
                        ls_type = lsa_instance.get_lsa_type_from_lsa()

                        eligible_interfaces = []
                        #  Obtains the eligible interfaces for flooding the LSA
                        if self.ospf_version == conf.VERSION_IPV4:
                            if ls_type in [conf.LSA_TYPE_AS_EXTERNAL, conf.LSA_TYPE_OPAQUE_AS]:  # AS-flooding scope
                                #  All router interfaces
                                for j in self.interfaces:
                                    eligible_interfaces.append(self.interfaces[j][area.INTERFACE_OBJECT])
                            else:  # Area or link-flooding scope
                                #  All area interfaces
                                for j in current_area.interfaces:
                                    eligible_interfaces.append(current_area.interfaces[j][area.INTERFACE_OBJECT])
                        elif self.ospf_version == conf.VERSION_IPV6:
                            flooding_scope = header.Header.get_s1_s2_bits(lsa_instance.header.ls_type)
                            u_bit = header.Header.get_u_bit(lsa_instance.header.ls_type)
                            if lsa.Lsa.is_ls_type_valid(ls_type, self.ospf_version) | (u_bit == 1):
                                if flooding_scope == conf.AS_SCOPING:
                                    for j in self.interfaces:
                                        eligible_interfaces.append(self.interfaces[j][area.INTERFACE_OBJECT])
                                elif flooding_scope == conf.AREA_SCOPING:
                                    for j in current_area.interfaces:
                                        eligible_interfaces.append(current_area.interfaces[j][area.INTERFACE_OBJECT])
                                elif flooding_scope == conf.LINK_LOCAL_SCOPING:
                                    eligible_interfaces.append(current_interface)
                                else:
                                    current_interface.flooded_pipeline.put(False)
                                    time.sleep(0.1)  # Give CPU to other threads
                                    continue  # Invalid flooding scope
                            else:  # LSA with unknown LS Type and U-bit set to False has link-local flooding scope
                                eligible_interfaces.append(current_interface)

                        for j in eligible_interfaces:
                            should_retransmit_lsa = False
                            for n in j.neighbors:
                                neighbor = j.neighbors[n]
                                if neighbor.neighbor_state not in [
                                        conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING,
                                        conf.NEIGHBOR_STATE_FULL]:
                                    continue  # Neighbor does not take part in flooding
                                elif neighbor.neighbor_state in [
                                        conf.NEIGHBOR_STATE_EXCHANGE, conf.NEIGHBOR_STATE_LOADING]:
                                    if lsa_identifier in neighbor.ls_request_list:  # Router sought this LSA
                                        #  Can be None
                                        local_copy = j.lsdb.get_lsa(lsa_identifier[0], lsa_identifier[1],
                                                                    lsa_identifier[2], eligible_interfaces)
                                        if lsa.Lsa.get_fresher_lsa(lsa_instance, local_copy) == header.SECOND:
                                            continue  # Examine next neighbor
                                        elif lsa.Lsa.get_fresher_lsa(lsa_instance, local_copy) == header.BOTH:
                                            neighbor.delete_lsa_identifier(neighbor.ls_request_list, lsa_identifier)
                                            continue
                                        else:  # Sought LSA has been received
                                            neighbor.delete_lsa_identifier(neighbor.ls_request_list, lsa_identifier)
                                if sending_neighbor_id == n:  # This neighbor sent the received LSA
                                    continue
                                neighbor.add_lsa_identifier(neighbor.ls_retransmission_list, lsa_identifier)
                                should_retransmit_lsa = True

                            if not should_retransmit_lsa:
                                current_interface.flooded_pipeline.put(False)
                                time.sleep(0.1)
                                continue  # LSA will not be flooded
                            #  LSA came from DR or BDR of current interface
                            if (i == j.physical_identifier) & (sending_neighbor_id in [
                                    current_interface.designated_router, current_interface.backup_designated_router]):
                                current_interface.flooded_pipeline.put(False)
                                time.sleep(0.1)
                                continue
                            if (i == j.physical_identifier) & (current_interface.state == conf.INTERFACE_STATE_BACKUP):
                                current_interface.flooded_pipeline.put(False)
                                time.sleep(0.1)
                                continue

                            #  Flood the LSA through the interface
                            lsa_instance.increase_lsa_age()  # Increases LS Age by 1 s
                            destination_address = j.get_flooding_ip_address()
                            ls_update_packet = packet.Packet()
                            if self.ospf_version == conf.VERSION_IPV4:
                                ls_update_packet.create_header_v2(conf.PACKET_TYPE_LS_UPDATE, self.router_id, a,
                                                                  conf.DEFAULT_AUTH, conf.NULL_AUTHENTICATION)
                            else:
                                ls_update_packet.create_header_v3(
                                    conf.PACKET_TYPE_LS_UPDATE, self.router_id, a, current_interface.instance_id,
                                    current_interface.ipv6_address, destination_address)
                            ls_update_packet.create_ls_update_packet_body(self.ospf_version)
                            ls_update_packet.add_lsa(lsa_instance)
                            packet_bytes = ls_update_packet.pack_packet()
                            sending_socket = j.socket
                            if self.ospf_version == conf.VERSION_IPV4:
                                sending_socket.send_ipv4(
                                    packet_bytes, destination_address, j.physical_identifier, self.localhost)
                            elif self.ospf_version == conf.VERSION_IPV6:
                                sending_socket.send_ipv6(
                                    packet_bytes, destination_address, j.physical_identifier, self.localhost)
                            current_interface.flooded_pipeline.put(True)
                            time.sleep(0.1)
                            current_interface.update_ls_retransmission_lists(lsa_identifier, destination_address)

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
        for s in self.socket_shutdown_events:
            self.socket_shutdown_events[s].set()
        for t in self.socket_threads:
            self.socket_threads[t].join()
        for a in self.areas:
            self.areas[a].shutdown_area()
