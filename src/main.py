import cmd
import multiprocessing
import os
import netifaces
from datetime import datetime

import router.router as router
import conf.conf as conf
import general.utils as utils

'''
Router program startup script and class. Run the script to launch the program
'''

BOTH_VERSIONS = 1
OSPF_V2 = 2
OSPF_V3 = 3


class Main(cmd.Cmd):
    #  Cmd class parameters
    intro = 'OSPF router program. Type "help" or "?" to display help'
    prompt = '(router) '
    file = None

    #  Implementation-specific parameters
    command_pipeline_v2 = None
    command_pipeline_v3 = None
    output_event_v2 = None
    output_event_v3 = None
    shutdown_event_v2 = None
    shutdown_event_v3 = None
    router_v2 = None
    router_v3 = None
    process_v2 = None
    process_v3 = None
    option = 0
    router_id = ''

    def do_show(self, arg):
        'Prints general protocol information: SHOW'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("OSPFv2")
            self.command_pipeline_v2.put([router.SHOW, None])
            Main.wait_for_output(self.output_event_v2)
            print()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("OSPFv3")
            self.command_pipeline_v3.put([router.SHOW, None])
            Main.wait_for_output(self.output_event_v3)

    def do_show_interface(self, arg):
        'Prints interface information: SHOW_INTERFACE'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("OSPFv2")
            self.command_pipeline_v2.put([router.SHOW_INTERFACE, None])
            Main.wait_for_output(self.output_event_v2)
            print()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("OSPFv3")
            self.command_pipeline_v3.put([router.SHOW_INTERFACE, None])
            Main.wait_for_output(self.output_event_v3)

    def do_show_neighbor(self, arg):
        'Prints neighbor information: SHOW_NEIGHBOR'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("OSPFv2")
            self.command_pipeline_v2.put([router.SHOW_NEIGHBOR, None])
            Main.wait_for_output(self.output_event_v2)
            print()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("OSPFv3")
            self.command_pipeline_v3.put([router.SHOW_NEIGHBOR, None])
            Main.wait_for_output(self.output_event_v3)

    def do_show_lsdb(self, arg):
        'Prints LSDB content: SHOW_LSDB'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("OSPFv2")
            self.command_pipeline_v2.put([router.SHOW_LSDB, None])
            Main.wait_for_output(self.output_event_v2)
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("OSPFv3")
            self.command_pipeline_v3.put([router.SHOW_LSDB, None])
            Main.wait_for_output(self.output_event_v3)

    def do_show_ip_route(self, arg):
        'Prints routing table content: SHOW_IP_ROUTE'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("IPv4")
            os.system("ip route")
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("IPv6")
            os.system("ip -6 route")

    def do_show_ip_address(self, arg):
        'Prints addresses of all router interfaces: SHOW_IP_ADDRESS'
        os.system("ip addr")

    def do_shutdown_interface(self, arg):
        'Performs shutdown of specified interface: SHUTDOWN_INTERFACE ens33'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            self.command_pipeline_v2.put([router.SHUTDOWN_INTERFACE, arg])
            Main.wait_for_output(self.output_event_v2)
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.command_pipeline_v3.put([router.SHUTDOWN_INTERFACE, arg])
            Main.wait_for_output(self.output_event_v3)

    def do_start_interface(self, arg):
        'Starts specified interface: START_INTERFACE ens33'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            self.command_pipeline_v2.put([router.START_INTERFACE, arg])
            Main.wait_for_output(self.output_event_v2)
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.command_pipeline_v3.put([router.START_INTERFACE, arg])
            Main.wait_for_output(self.output_event_v3)

    def do_shutdown(self, arg):
        'Performs the router shutdown: SHUTDOWN'
        return True

    def do_ping(self, arg):
        'Sends 5 pings to the specified address: PING 222.222.1.1'
        command = "ping -c 5 -i 0 " + arg  # No interval between pings
        os.system(command)

    #  Waits for router process to signal printing of desired output
    @staticmethod
    def wait_for_output(event):
        while not event.is_set():
            pass
        event.clear()

    def preloop(self):
        router_data = Main.get_router_data()
        Main.router_id = router_data[0]
        interface_ids = router_data[1]
        area_ids = router_data[2]
        print(datetime.now().time(), Main.router_id + ": Starting router...")
        Main.startup(interface_ids)
        self.option = int(input(
            "Write " + str(BOTH_VERSIONS) + " for running both OSPF versions, " + str(OSPF_V2) +
            " for running just OSPFv2, or " + str(OSPF_V3) + " for running just OSPFv3, then press ENTER:"))
        while self.option not in [BOTH_VERSIONS, OSPF_V2, OSPF_V3]:
            try:
                self.option = int(input(str("Write " + str(BOTH_VERSIONS) + ", " + str(OSPF_V2) + ", " + "or " +
                                            str(OSPF_V3) + ", then press ENTER:")))
            except ValueError:
                pass
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            self.router_v2 = router.Router()
            self.command_pipeline_v2 = multiprocessing.Queue()
            self.output_event_v2 = multiprocessing.Event()
            self.shutdown_event_v2 = multiprocessing.Event()
            self.process_v2 = multiprocessing.Process(target=self.router_v2.set_up, args=(
                Main.router_id, conf.VERSION_IPV4, self.shutdown_event_v2, interface_ids, area_ids, False,
                self.command_pipeline_v2, self.output_event_v2))
            self.process_v2.start()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.router_v3 = router.Router()
            self.command_pipeline_v3 = multiprocessing.Queue()
            self.output_event_v3 = multiprocessing.Event()
            self.shutdown_event_v3 = multiprocessing.Event()
            self.process_v3 = multiprocessing.Process(target=self.router_v3.set_up, args=(
                Main.router_id, conf.VERSION_IPV6, self.shutdown_event_v3, interface_ids, area_ids, False,
                self.command_pipeline_v3, self.output_event_v3))
            self.process_v3.start()
        print(datetime.now().time(), Main.router_id + ": Router started")

    def postloop(self):
        print(datetime.now().time(), Main.router_id + ": Shutting down router...")
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            self.shutdown_event_v2.set()
            self.process_v2.join()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.shutdown_event_v3.set()
            self.process_v3.join()
        print(datetime.now().time(), Main.router_id + ": Router down")

    #  If program is running inside a provided GNS3 network, returns router data according to router ID
    @staticmethod
    def get_router_data():
        try:
            network = int(os.environ['NETWORK'])
            rid = int(os.environ['ROUTER'])
            if (not (1 <= network <= 3)) | (not (1 <= rid <= 6)):
                print("NETWORK must be an integer between 1 and 3, ROUTER must be an integer between 1 and 6")
                return [conf.ROUTER_ID, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS]  # Default data

            if rid == 1:  # R1
                return [conf.ROUTER_IDS[rid - 1], conf.INTERFACES_R1[network - 1], conf.AREAS_R1[network - 1]]
            elif rid == 2:  # R2
                return [conf.ROUTER_IDS[rid - 1], conf.INTERFACES_R2[network - 1], conf.AREAS_R2[network - 1]]
            elif rid == 3:  # R3
                return [conf.ROUTER_IDS[rid - 1], conf.INTERFACES_R3[network - 1], conf.AREAS_R3[network - 1]]
            elif rid == 4:  # R4
                return [conf.ROUTER_IDS[rid - 1], conf.INTERFACES_R4[network - 1], conf.AREAS_R4[network - 1]]
            elif rid == 5:  # R5
                return [conf.ROUTER_IDS[rid - 1], conf.INTERFACES_R5[network - 1], conf.AREAS_R5[network - 1]]
            elif rid == 6:  # R6
                return [conf.ROUTER_IDS[rid - 1], conf.INTERFACES_R6[network - 1], conf.AREAS_R6[network - 1]]
        except ValueError:
            print("NETWORK must be an integer between 1 and 3, ROUTER must be an integer between 1 and 6")
            return [conf.ROUTER_ID, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS]
        except KeyError:
            #  Program is running outside provided GNS3 networks - Fetch default data
            return [conf.ROUTER_ID, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS]

    #  VM startup configuration
    @staticmethod
    def startup(interfaces):
        os.system("sysctl net.ipv4.ip_forward=1")
        os.system("sysctl net.ipv6.conf.all.forwarding=1")
        print(datetime.now().time(), Main.router_id + ": Packet forwarding enabled")
        os.system("sysctl net.ipv6.conf.all.autoconf=0")  # Router will not configure IPv6 address by itself
        os.system("sysctl net.ipv6.conf.all.accept_ra=0")
        #  Ensures any IPv6 address automatically configured will be removed
        for interface in interfaces:
            if len(netifaces.ifaddresses(interface)[netifaces.AF_INET6]) > 2:
                address = netifaces.ifaddresses(interface)[netifaces.AF_INET6][0]['addr']
                prefix_length = str(utils.Utils.get_ipv6_prefix_from_interface_name(interface)[1])
                os.system("ip -6 addr del " + address + "/" + prefix_length + " dev " + interface)
        print(datetime.now().time(), Main.router_id + ": Address autoconfiguration disabled")


if __name__ == '__main__':
    Main().cmdloop()
