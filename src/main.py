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
    output_event_v2 = None
    output_event_v3 = None
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

    #  Waits for router process to signal printing of desired output
    @staticmethod
    def wait_for_output(event):
        while not event.is_set():
            pass
        event.clear()

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
            self.router_v2 = router.Router()
            self.command_pipeline_v2 = multiprocessing.Queue()
            self.output_event_v2 = multiprocessing.Event()
            self.shutdown_event_v2 = multiprocessing.Event()
            self.process_v2 = multiprocessing.Process(target=self.router_v2.set_up, args=(
                conf.ROUTER_ID, conf.VERSION_IPV4, self.shutdown_event_v2, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS,
                False, self.command_pipeline_v2, self.output_event_v2))
            self.process_v2.start()
        if self.option in [BOTH_VERSIONS, OSPF_V3]:
            self.router_v3 = router.Router()
            self.command_pipeline_v3 = multiprocessing.Queue()
            self.output_event_v3 = multiprocessing.Event()
            self.shutdown_event_v3 = multiprocessing.Event()
            self.process_v3 = multiprocessing.Process(target=self.router_v3.set_up, args=(
                conf.ROUTER_ID, conf.VERSION_IPV6, self.shutdown_event_v3, conf.INTERFACE_NAMES, conf.INTERFACE_AREAS,
                False, self.command_pipeline_v3, self.output_event_v3))
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
