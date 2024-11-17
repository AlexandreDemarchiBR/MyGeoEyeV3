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
        '''
        usando o nameserver, procuramos por nós cujo nome comece com datanode_
        criamos um dicionário que mapeia nome de datanode com endereços e uma
        lista com nome dos datanodes.
        Na hora de criar o proxy, o metodo retorna antes da conexão ser estabelecida,
        então uma gambiarra de chamar um método remoto qualquer antes de pegar o ip do
        datanode foi usada pra garantir que a conexão esteja estabelecida.
        A partir da lista dos nomes de datanodes, criamos uma balanceador rudimentar do
        tipo round robin, pra ciclar entre os nós disponível na hora da inserção
        Um dicionario de metadados que mapeia nome de arquivo para uma lista de partes e
        os respectivos endereços de onde estão armazenados essas partes. O objetivo é iterar
        essa lista para remontar o arquivo de volta pro cliente na hora do download
        '''
        self.ns = Pyro5.api.locate_ns()
        #dict of name: uri
        self.datanode_dict = self.ns.list(prefix="datanode_")
        #list containing names
        self.datanode_list = [name for name in self.datanode_dict]
        for node in self.datanode_list:
            # replace uri with remote object and ip
            obj = Pyro5.api.Proxy(self.datanode_dict[node])
            # uri = Pyro5.core.resolve(self.datanode_dict[node]) # to only get uri
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
    
    '''
    Por questões de desempenho, a transferência de arquivos é feita usando sockets comuns
    O cliente chama este método passando o nome do arquivo a ser enviado, o método prepara um
    socket para fazer este upload e devolve o número da porta para o cliente se conectar e enviar
    o arquivo. Como o socket é criado especificamente para o arquivo especificado, o cliente só
    precisa se conectar, enviar o arquivo completo e fechar a conexão.
    No lado do servidor (aqui), o socket é passado para uma thread que receberá as partes e irá
    distribuir nos datanodes
    '''
    def upload_image_socket(self, file_name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((my_ip, 0))
        port = sock.getsockname()[1]
        t = threading.Thread(target=self.distribute_image, args=(file_name, sock), daemon=True)
        print('disparando thread')
        t.start()
        return port

    '''
    Este método é o que recebe o socket que se conecta com o cliente e distribui o arquivo em
    partes.
    Pra cada parte de arquivo, um sufixo do tipo _part00004 é criado, um datanode é selecionado
    usando a fila circular, e o chunk é enviado pro datanode, de forma semelhante ao cliente enviando
    para o main. O dicionário de listas de partes é atualizado para possibilitar remontagem
    do arquivo.
    Ficou mais complicado do que gostaria. A ideia inicial era usar proxys prontos, definidos na __init__, mas ao usar threads, por
    algum motivo, o pyro não deixa usarmos os proxys prontos, então tive que criar um pra cada parte
    a ser enviada. Estou buscando melhorar esta parte.
    '''
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


    '''
    Semelhante a upload_image_socket, mas para baixar
    '''
    def download_image_socket(self, file_name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((my_ip, 0))
        port = sock.getsockname()[1]
        t = threading.Thread(target=self.rebuild_image, args=(file_name, sock), daemon=True)
        t.start()
        return port
    
    '''
    Faz o inverso de distribute_image. Usando o dicionário com a lista de partes, conectamos
    com o cliente, iteramos a lista de partes, baixado os dados e enviando para o cliente.
    '''
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

    
    # Usada no cliente para garantir que estamos conectados (igual fazemos aqui com hello())
    def echo_test(self):
        return 'echo'

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # goal is to automatically bind the server to the IP that
        # will be visible outside the host. This part get this IP
        s.connect(("8.8.8.8", 80))
        my_ip = s.getsockname()[0]
    daemon = Pyro5.api.Daemon(host=my_ip)
    uri = daemon.register(MainServer())
    ns = Pyro5.api.locate_ns()
    ns.register('mainserver', uri) 
    print("Ready. Object uri =", uri) 
    daemon.requestLoop()                    # start the event loop of the server to wait for calls