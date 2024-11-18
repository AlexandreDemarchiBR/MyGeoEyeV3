#!/bin/bash

# Checa se a quantidade de parametros está correta
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 {start|stop|update} {main|datanode|ns|all}"
    exit 1
fi

# Assign arguments to variables
ACTION=$1
TARGET=$2

stop_ns() {
    ip=$(cat main_dir/ns_host.txt)
    echo "Stopping nameserver on $ip"
    ./utils/control_host.exp $ip stop ns
}
# Mata o processo do servidor main
stop_main() {
    ip=$(cat main_dir/main_host.txt)
    echo "Stopping main on $ip"
    ./utils/control_host.exp $ip stop main
}

# Mata todos os processos de datanodes
stop_datanode() {
    echo "Stopping datanode service"
    for ip in $(cat main_dir/workers.txt); do
        echo "Stopping datanode on $ip"
        ./utils/control_host.exp $ip stop datanode
    done
}

# Mata todos os processos do sistema
stop_all() {
    stop_datanode
    stop_main
    stop_ns
}

start_ns() {
    ip=$(cat main_dir/ns_host.txt)
    echo "Starting nameserver on $ip"
    ./utils/control_host.exp $ip start ns
    # Add actual start command for main here
}

# Inicia uma instância do servidor main
start_main() {
    ip=$(cat main_dir/main_host.txt)
    echo "Starting main on $ip"
    ./utils/control_host.exp $ip start main
    # Add actual start command for main here
}

# Inicia instâncias de todos os datanodes
start_datanode() {
    for ip in $(cat main_dir/workers.txt); do
        echo "Starting datanode on $ip"
        ./utils/control_host.exp $ip start datanode
    done
}

# Inicia instâncias de todo o sistema
start_all() {
    start_ns
    start_main
    start_datanode
}

# Atualiza os arquivos de main
update_main() {
    echo "Updating main service"
    # Add actual update command for main here
}

# Atualiza os arquivos do datanode
update_datanode() {
    echo "Update datanode service"
    for ip in $(cat ../main_dir/workers.txt); do
        echo "Update datanode on $ip"
    done
}

# Atualiza os arquivos de todo o sistema
update_all() {
    echo "Update main service"
    echo "Update datanode service"
    for ip in $(cat ../main_dir/workers.txt); do
        echo "Update datanode on $ip"
    done
}

# Logic for handling actions and targets
if [ "$ACTION" == "stop" ]; then
    if [ "$TARGET" == "main" ]; then
        stop_main
    elif [ "$TARGET" == "ns" ]; then
        stop_ns
    elif [ "$TARGET" == "datanode" ]; then
        stop_datanode
    elif [ "$TARGET" == "all" ]; then
        stop_all
    else
        echo "Invalid target: $TARGET"
        exit 1
    fi
elif [ "$ACTION" == "start" ]; then
    if [ "$TARGET" == "main" ]; then
        start_main
    elif [ "$TARGET" == "ns" ]; then
        start_ns
    elif [ "$TARGET" == "datanode" ]; then
        start_datanode
    elif [ "$TARGET" == "all" ]; then
        start_all
    else
        echo "Invalid target: $TARGET"
        exit 1
    fi
elif [ "$ACTION" == "restart" ]; then
    if [ "$TARGET" == "main" ]; then
        stop_main
        start_main
    elif [ "$TARGET" == "ns" ]; then
        stop_ns
        start_ns
    elif [ "$TARGET" == "datanode" ]; then
        stop_datanode
        start_datanode
    elif [ "$TARGET" == "all" ]; then
        stop_all
        start_all
    else
        echo "Invalid target: $TARGET"
        exit 1
    fi
elif [ "$ACTION" == "update" ]; then
    if [ "$TARGET" == "main" ]; then
        update_main
    elif [ "$TARGET" == "datanode" ]; then
        update_datanode
    elif [ "$TARGET" == "all" ]; then
        update_all
    else
        echo "Invalid target: $TARGET"
        exit 1
    fi
else
    echo "Invalid action: $ACTION"
    exit 1
fi
