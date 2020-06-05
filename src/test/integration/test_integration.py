import unittest
import threading

import router.router as router
import conf.conf as conf

'''
This class tests integration between 2 routers running on localhost
'''


#  Full successful run - Instant
class IntegrationTest(unittest.TestCase):

    def setUp(self):
        self.router_shutdown_v2_1 = threading.Event()
        self.router_shutdown_v2_2 = threading.Event()
        self.interfaces_v2_1 = ['ens38']  # Router interfaces
        self.interfaces_v2_2 = ['ens39']
        self.areas_v2 = [conf.BACKBONE_AREA]  # One element for each router interface
        self.localhost = True
        self.network_interfaces = ['ens38', 'ens39']  # All interfaces connected to the network
        self.router_v2_1 = router.Router(conf.VERSION_IPV4, self.router_shutdown_v2_1, self.interfaces_v2_1,
                                         self.areas_v2, self.localhost, self.network_interfaces)
        self.router_v2_2 = router.Router(conf.VERSION_IPV4, self.router_shutdown_v2_2, self.interfaces_v2_2,
                                         self.areas_v2, self.localhost, self.network_interfaces)
        self.thread_v2_1 = threading.Thread(target=self.router_v2_1.main_loop)
        self.thread_v2_2 = threading.Thread(target=self.router_v2_2.main_loop)
        self.thread_v2_1.start()
        self.thread_v2_2.start()

    def test_a(self):
        pass

    def tearDown(self):
        self.router_shutdown_v2_1.set()
        self.router_shutdown_v2_2.set()
        self.thread_v2_1.join()
        self.thread_v2_2.join()
