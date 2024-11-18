#!/bin/bash

IP=$(ip -4 addr show $(ip route show default | awk '/default/ {print $5}') | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
echo "Starting pyro5-ns server on $IP..."

echo "Killing previous process"
pkill -f pyro5-ns
rm pyro5-ns.pid

echo "Starting pyro5-ns"
pyro5-ns -n $IP &
disown

echo $! > pyro5-ns.pid
echo "pyro5-ns server started with PID $(cat pyro5-ns.pid)"
sleep 1 # resolve o $ não aparecendo (precisamos para o expect)
#echo '$' # opção 2