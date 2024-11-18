#!/bin/bash

IP=$(ip -4 addr show $(ip route show default | awk '/default/ {print $5}') | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
echo "Starting Main server on $IP..."

echo Killing previous process
pkill -f main.py
rm main.pid

echo "Starting main.py"
python3 main.py &
disown

echo $! > main.pid
echo "Main server started with PID $(cat main.pid)"
sleep 1 # resolve o $ não aparecendo (precisamos para o expect)
#echo '$' # opção 2
