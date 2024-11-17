#!/bin/bash
# Será usado na inicialização do nameserver
ip -4 addr show $(ip route show default | awk '/default/ {print $5}') | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
# ip route show default | awk '/default/ {print $5}' # Interface que se conecta à rota padrão
# ip -4 addr show <interface> # detalhes sobre ipv4 desta interface
# grep -oP '(?<=inet\s)\d+(\.\d+){3}' # extrai o ip da saida
