import cmd
import multiprocessing

import router.router as router
import conf.conf as conf

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
    shutdown_event_v2 = None
    shutdown_event_v3 = None
    router_v2 = None
    router_v3 = None
    process_v2 = None
    process_v3 = None
    option = 0

    def do_show(self, arg):
        'Prints general protocol information: SHOW'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("OSPFv2")
            self.router_v2.show_general_data()
            print()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("OSPFv3")
            self.router_v3.show_general_data()

    def do_show_interface(self, arg):
        'Prints interface information: SHOW_INTERFACE'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("OSPFv2")
            self.router_v2.show_interface_data()
            print()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("OSPFv3")
            self.router_v3.show_interface_data()

    def do_show_neighbor(self, arg):
        'Prints neighbor information: SHOW_NEIGHBOR'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("OSPFv2")
            self.router_v2.show_neighbor_data()
            print()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("OSPFv3")
            self.router_v3.show_neighbor_data()

    def do_show_lsdb(self, arg):
        'Prints LSDB content: SHOW_LSDB'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            print("OSPFv2")
            self.router_v2.show_lsdb_content()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            print("OSPFv3")
            self.router_v3.show_lsdb_content()

    def do_shutdown_interface(self, arg):
        'Performs shutdown of specified interface: SHUTDOWN_INTERFACE ens33'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            self.router_v2.shutdown_interface(arg)
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.router_v3.shutdown_interface(arg)

    def do_start_interface(self, arg):
        'Starts specified interface: START_INTERFACE ens33'
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            self.router_v2.start_interface(arg)
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.router_v3.start_interface(arg)

    def do_shutdown(self, arg):
        'Performs the router shutdown: SHUTDOWN'
        return True

    def preloop(self):
        self.option = int(input(
            "Write " + str(BOTH_VERSIONS) + " for running both OSPF versions, " + str(OSPF_V2) +
            " for running just OSPFv2, or " + str(OSPF_V3) + " for running just OSPFv3, then press ENTER:"))
        while self.option not in [BOTH_VERSIONS, OSPF_V2, OSPF_V3]:
            try:
                self.option = int(input(str("Write " + str(BOTH_VERSIONS) + ", " + str(OSPF_V2) + ", " + "or " +
                                            str(OSPF_V3) + ", then press ENTER:")))
            except ValueError:
                pass
        print(conf.ROUTER_ID + ": Starting router...")
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            self.shutdown_event_v2 = multiprocessing.Event()
            self.router_v2 = router.Router(conf.ROUTER_ID, conf.VERSION_IPV4, self.shutdown_event_v2,
                                           conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False)
            self.process_v2 = multiprocessing.Process(target=self.router_v2.main_loop)
            self.process_v2.start()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.shutdown_event_v3 = multiprocessing.Event()
            self.router_v3 = router.Router(conf.ROUTER_ID, conf.VERSION_IPV6, self.shutdown_event_v3,
                                           conf.INTERFACE_NAMES, conf.INTERFACE_AREAS, False)
            self.process_v3 = multiprocessing.Process(target=self.router_v3.main_loop)
            self.process_v3.start()
        print(conf.ROUTER_ID + ": Router started")

    def postloop(self):
        print(conf.ROUTER_ID + ": Shutting down router...")
        if self.option in [BOTH_VERSIONS, OSPF_V2]:
            self.shutdown_event_v2.set()
            self.process_v2.join()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.shutdown_event_v3.set()
            self.process_v3.join()
        print(conf.ROUTER_ID + ": Router down")


if __name__ == '__main__':
    Main().cmdloop()
