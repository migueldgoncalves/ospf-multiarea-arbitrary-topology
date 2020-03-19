import queue
import threading

import router.router as router
import conf.conf as conf
import command.command_line as command_line

command_pipeline_v2 = queue.Queue()
command_pipeline_v3 = queue.Queue()
data_pipeline_v2 = queue.Queue()
data_pipeline_v3 = queue.Queue()
shutdown_event_v2 = threading.Event()
shutdown_event_v3 = threading.Event()

router_v2 = router.Router(conf.VERSION_IPV4, command_pipeline_v2, data_pipeline_v2, shutdown_event_v2)
router_v3 = router.Router(conf.VERSION_IPV6, command_pipeline_v3, data_pipeline_v3, shutdown_event_v3)

thread_v2 = threading.Thread(target=router_v2.main_loop)
thread_v3 = threading.Thread(target=router_v3.main_loop)
thread_v2.start()
thread_v3.start()

command_line.CommandLine().cmdloop()
