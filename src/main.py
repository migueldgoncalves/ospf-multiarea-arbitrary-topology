import cmd
import threading

import router.router as router
import conf.conf as conf

'''
Router program startup script and class. Run the script to launch the program
'''


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
    thread_v2 = None
    thread_v3 = None

    def do_show(self, arg):
        'Prints general protocol information: SHOW'
        print("OSPFv2")
        self.router_v2.show_general_data()
        print()
        print("OSPFv3")
        self.router_v3.show_general_data()

    def do_show_interface(self, arg):
        'Prints interface information: SHOW_INTERFACE'
        print("OSPFv2")
        self.router_v2.show_interface_data()
        print()
        print("OSPFv3")
        self.router_v3.show_interface_data()

    def do_show_neighbor(self, arg):
        'Prints neighbor information: SHOW_NEIGHBOR'
        print("OSPFv2")
        self.router_v2.show_neighbor_data()
        print()
        print("OSPFv3")
        self.router_v3.show_neighbor_data()

    def do_shutdown_interface(self, arg):
        'Performs shutdown of specified interface: SHUTDOWN_INTERFACE ens33'
        self.router_v2.shutdown_interface(arg)
        self.router_v3.shutdown_interface(arg)

    def do_start_interface(self, arg):
        'Starts specified interface: START_INTERFACE ens33'
        self.router_v2.start_interface(arg)
        self.router_v3.start_interface(arg)

    def do_shutdown(self, arg):
        'Performs the router shutdown: SHUTDOWN'
        return True

    def preloop(self):
        print(conf.ROUTER_ID + ": Starting router...")
        self.shutdown_event_v2 = threading.Event()
        self.shutdown_event_v3 = threading.Event()

        self.router_v2 = router.Router(conf.ROUTER_ID, conf.VERSION_IPV4, self.shutdown_event_v2, conf.INTERFACE_NAMES,
                                       conf.INTERFACE_AREAS, False)
        self.router_v3 = router.Router(conf.ROUTER_ID, conf.VERSION_IPV6, self.shutdown_event_v3, conf.INTERFACE_NAMES,
                                       conf.INTERFACE_AREAS, False)

        self.thread_v2 = threading.Thread(target=self.router_v2.main_loop)
        self.thread_v3 = threading.Thread(target=self.router_v3.main_loop)
        self.thread_v2.start()
        self.thread_v3.start()
        print(conf.ROUTER_ID + ": Router started")

    def postloop(self):
        print(conf.ROUTER_ID + ": Shutting down router...")
        self.shutdown_event_v2.set()
        self.shutdown_event_v3.set()
        self.thread_v2.join()
        self.thread_v3.join()
        print(conf.ROUTER_ID + ": Router down")


if __name__ == '__main__':
    Main().cmdloop()
