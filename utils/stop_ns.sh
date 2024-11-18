#!/bin/bash

# Check if the PID file exists
if [ -f pyro5-ns.pid ]; then
    # Read the PID from the file
    PID=$(cat pyro5-ns.pid)
    echo "Stopping datanode server with PID $PID..."
    
    # Kill the process
    kill $PID
    
    # Remove the PID file
    rm pyro5-ns.pid

    echo "pyro5-ns server stopped."
else
    echo "No PID file found. Is the pyro5-ns server running?"
    pkill -f pyro5-ns
fi
