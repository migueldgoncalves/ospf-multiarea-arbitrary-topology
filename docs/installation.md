## Installation, execution and testing

### Prerequisites

* **Host machine OS**: Ubuntu 18.04

* **Additional programs**: GNS3, Docker Engine

### Installation

1. Extract the [Dockerfile](https://github.com/migueldgoncalves/ospf-multiarea-arbitrary-topology/blob/master/Dockerfile) and place it in an empty directory of the host machine;

2. With a terminal, go to the directory containing the Dockerfile, and run the command `docker build -t ospf .`. It will create a Docker image called `ospf`, and takes a few minutes to complete;

3. Open GNS3, click on Edit > Preferences > QEMU, then disable all the options referring to hardware acceleration. This will allow the Cisco network routers to be started without running GNS3 as root;

4. Copy the /gns3 folder of this repository, containing 3 networks, to the host machine, and with GNS3 open one of the networks;

5. Copy the /src folder of this repository to the directories /project-files/docker/<hexadecimal-id>/ospf inside the folder of the opened GNS3 network, where <hexadecimal-id> is the id of each Docker container of the network;

* It is possible that a non-root user does not have access to the /ospf directories. Change the permissions of the directory if desired;

* To identify which hexadecimal ID corresponds to each Docker container of the network, right-click on the desired container in GNS3 and then click on _Show node information_. The field _Server ID_ contains the container hexadecimal ID;

### Configuration

The configurable parameters are located in the beginning of the [conf.py](https://github.com/migueldgoncalves/ospf-multiarea-arbitrary-topology/blob/master/src/conf/conf.py) file.

The following parameters are configurable:

* Router ID
* Router priority
* Interface IDs (must match interface IDs of the machine)
* Interface areas
* Interface costs

The interface parameters are stored in lists containing two sub-lists. The first sub-list applies to the [network 1-1](https://github.com/migueldgoncalves/ospf-multiarea-arbitrary-topology/tree/master/gns3/network_1_1) and to the [network 1-2](https://github.com/migueldgoncalves/ospf-multiarea-arbitrary-topology/tree/master/gns3/network_1_2), while the second sub-list applies to the [network 2-1](https://github.com/migueldgoncalves/ospf-multiarea-arbitrary-topology/tree/master/gns3/network_2_1).

Inside each sub-list, each element contains the configuration value for a specific interface. For example, in the network 2-1, the interface eth1 belongs to the area 0.0.0.2 and has a cost of 10.

### Execution

1. Inside GNS3, start the desired Docker containers, then double-click on them in order to open the respective terminal. The starting directory will be the /ospf directory mentioned in the step 5 of the Installation section;

2. Enter the /src directory (it may be necessary to re-enter the /ospf directory), and run `python3 main.py`;

3. When prompted, select the desired OSPF version to be run by writing the respective number and pressing ENTER;

* The OSPF program is now operating.

### Testing

A number of `unittest` [automated tests](https://github.com/migueldgoncalves/ospf-multiarea-arbitrary-topology/tree/master/src/test) are provided with the source code.

All tests are designed to run in R4 of the network 1-1, after R1, R2 and R3 have converged and with R5 and R6 down. The VPCSs have no effect on the tests. Some tests can pass in different environments, and some can even run in Windows.

Before running the tests, it is necessary to start the main program and wait for the prompt for the OSPF version to appear. Then, the program can be stopped with Ctrl+C. This allows any automatic IPv6 addresses to be flushed, which would cause some tests to fail.

The following commands allow to run a single test, a test module, a test package, or the entire test suite. They must be run the /src folder of the project.

`python3 -m unittest test.packet.test_header.TestHeader.test_pack_header` - Runs the _test_pack_header_ test of the _TestHeader_ module of the _packet_ test package;

`python3 -m unittest test.packet.test_header` - Runs all tests inside the _TestHeader_ module of the _packet_ test package;

`python3 -m unittest discover test.packet` - Runs all tests inside the _packet_ test package;

`python3 -m unittest discover` - Runs the entire test suite.

A test can be executed instantly or take up to 2-3 minutes to complete. The entire test suite takes around 10 minutes to complete. It is possible that a few tests fail in one test run and pass in the next run, and vice versa.