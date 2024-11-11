import Pyro5.api
import os
import socket
from itertools import cycle
import threading

CHUNK_SIZE = 10*1024*1024
FILE_PART_SIZE = 40*1024*1024

@Pyro5.api.expose
class MainServer(object):
    def __init__(self) -> None:
        self.ns = Pyro5.api.locate_ns()
        #dict of name: uri
        self.datanode_dict = self.ns.list(prefix="datanode_")
        #list containing names
        self.datanode_list = [name for name in self.datanode_dict]
        for node in self.datanode_list:
            # replace uri with remote object and ip
            obj = Pyro5.api.Proxy(self.datanode_dict[node])
            obj.hello() # ensure it is connected before gettin ip
            ip = obj._pyroConnection.sock.getpeername()[0]
            self.datanode_dict[node] = (obj, ip)
        if not os.path.exists('main_dir/'):
            os.makedirs('main_dir/')
        self.circular_queue = cycle(self.datanode_list)
        # key: filename. value: list of pairs, the pairs are chunk and node where chunk is stored
        self.filename_metadata = {} # filename: list[(part,node)]

    def get_next_datanode(self):
        node = next(self.circular_queue)
        return self.datanode_dict[node]
    
    def upload_image_socket(self, file_name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', 0))
        port = sock.getsockname()[1]
        t = threading.Thread(target=self.distribute_image, args=(file_name, sock), daemon=True)
        print('disparando thread')
        t.start()
        return port

    def distribute_image(self, file_name: str, srv_socket: socket.socket):
        srv_socket.listen(1)
        print('aceitando conexão')
        client_socket, addr = srv_socket.accept()
        chunk_list = []
        sent = 0
        part = 0
        partname = f'{file_name}_part{part:05}'
        node = next(self.circular_queue)
        obj = Pyro5.api.Proxy(f'PYRONAME:{node}')
        obj.hello()
        ip = obj._pyroConnection.sock.getpeername()[0]
        port = obj.store_image_socket(partname)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))

        while True:
            chunk = client_socket.recv(CHUNK_SIZE)
            if not chunk: break
            sock.sendall(chunk)
            sent += len(chunk)
            if sent >= FILE_PART_SIZE:
                sock.close()
                chunk_list.append((partname, node))
                sent = 0
                part += 1
                partname = f'{file_name}_part{part:05}'
                node = next(self.circular_queue)
                obj = Pyro5.api.Proxy(f'PYRONAME:{node}')
                obj.hello()
                ip = obj._pyroConnection.sock.getpeername()[0]
                port = obj.store_image_socket(partname)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, port))
        chunk_list.append((partname, node))
        self.filename_metadata[file_name] = chunk_list
        print(chunk_list)
        sock.close()
        client_socket.close()
        srv_socket.close()

    def download_image_socket(self, file_name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', 0))
        port = sock.getsockname()[1]
        t = threading.Thread(target=self.rebuild_image, args=(file_name, sock), daemon=True)
        t.start()
        return port
    

    def rebuild_image(self, file_name: str, srv_socket: socket.socket):
        srv_socket.listen(1)
        print('aceitando conexão')
        client_socket, addr = srv_socket.accept()
        chunk_list = self.filename_metadata[file_name]
        chunk_list.sort()
        for part in chunk_list: # (partname, datanode)
            obj = Pyro5.api.Proxy(f'PYRONAME:{part[1]}')
            obj.hello() # gambiarra pra garantir que esteja conectado
            ip = obj._pyroConnection.sock.getpeername()[0]
            port = obj.retrieve_image_socket(part[0])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            while True:
                chunk = sock.recv(CHUNK_SIZE)
                if not chunk: break
                client_socket.sendall(chunk)
            sock.close()
        srv_socket.close()
        client_socket.close()

    def list_images(self):
        return [filename for filename in self.filename_metadata]
    
    def delete_image(self, file_name):
        chunk_list = self.filename_metadata[file_name]
        for part in chunk_list: # (partname, datanode)
            obj = Pyro5.api.Proxy(f'PYRONAME:{part[1]}')
            obj.delete_image(part[0])

    def hello(self):
        node = next(self.circular_queue)
        node = self.datanode_dict[node][0]
        return node.hello()
    def echo_test(self):
        return 'echo'
    def return_ip(self):
        node = next(self.circular_queue)
        return self.datanode_dict[node][1]

if __name__ == '__main__':
    Pyro5.config.PREFER_IP_VERSION = 4
    daemon = Pyro5.api.Daemon() 
    uri = daemon.register(MainServer())
    ns = Pyro5.api.locate_ns()
    ns.register('mainserver', uri) 
    print("Ready. Object uri =", uri) 
    daemon.requestLoop()                    # start the event loop of the server to wait for calls