#!/bin/bash
# start the pyro nameserver binding with the external ip
IP=$(ip -4 addr show $(ip route show default | awk '/default/ {print $5}') | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
pyro5-ns -n $IP