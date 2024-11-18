#!/bin/bash

IP=$(ip -4 addr show $(ip route show default | awk '/default/ {print $5}') | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
echo "Starting datanode server on $IP..."

echo Killing previous process
pkill -f datanode.py
rm datanode.pid

echo "Starting datanode.py"
python3 datanode.py &
disown

echo $! > datanode.pid
echo "datanode server started with PID $(cat datanode.pid)"
sleep 1 # resolve o $ não aparecendo (precisamos para o expect)
#echo '$' # opção 2
