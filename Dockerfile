FROM ubuntu:18.04

WORKDIR /ospf

RUN apt update && apt install --yes python3 \
python3-testresources \
python3-pip \
net-tools \
iproute2 \
iputils-ping \
nano \
ifupdown

RUN pip3 install netifaces \
setuptools \
tblib \
timeout-decorator \
utils \
wheel

VOLUME /ospf