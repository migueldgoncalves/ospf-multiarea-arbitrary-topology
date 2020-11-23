FROM ubuntu:18.04

WORKDIR /ospf

# Python 3.6 as of November 2020
RUN apt update && apt install --yes python3 \
python3-pip \
iproute2 \
iputils-ping \
traceroute

RUN pip3 install netifaces \
timeout-decorator

VOLUME /ospf