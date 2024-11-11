import Pyro5.api
import os
import socket
import uuid
import threading

CHUNK_SIZE = 10*1024*1024
DATANODE_INSTANCE = 1


'''
Função chamada pelo distribute_image da main. Pega um socket que se conecta com o
cliente (que neste contexto é o main) recebe dados e persiste com o nome passado no
parametro file_name
'''
def store_image(file_name: str, srv_socket: socket.socket):
    srv_socket.listen(1)
    print('aceitando conexão')
    client_socket, addr = srv_socket.accept()
    with open(f'datanode_dir/{file_name}', "wb") as file:
        print('recebendo arquivo')
        while True:
            chunk = client_socket.recv(CHUNK_SIZE)
            if not chunk: break
            file.write(chunk)
        print('encerrando socket cliente')
        client_socket.close()
    print('encerrando socket server')
    srv_socket.close()

'''
Semelhante à anterior, mas lê o arquivo de nome file_name, e envia para o socket do
cliente (que aqui é o main)
'''
def retrieve_image(file_name: str, srv_socket: socket.socket):
    srv_socket.listen(1)
    print('aceitando conexão')
    client_socket, addr = srv_socket.accept()
    with open(f'datanode_dir/{file_name}', "rb") as file:
        print('enviando arquivo')
        client_socket.sendfile(file)
        print('encerrando socket cliente')
        client_socket.close()
    print('encerrando socket server')
    srv_socket.close()

@Pyro5.api.expose
class Datanode(object):
    '''
    O servidor nesta fase de desenvolvimente apaga todos os arquivos, para simplificar a
    depuração, diminuindo comportamentos imprevisiveis por causa de efeitos colaterais.
    Futuramente a ideia é listar os arquivos para que a main faça o mapeamento das partes
    de arquivos de forma dinâmica para aruqivos existentes nos nós.
    file_locks é um dicionario para locks individuais para arquivos
    '''
    def __init__(self) -> None:
        self.clean_start()
        if not os.path.exists('datanode_dir/'):
            os.makedirs('datanode_dir/')
        self.files = os.listdir('datanode_dir/')
        self.file_locks = {}

    # limpa arquivos persistidos
    def clean_start(self):
        if os.path.exists('datanode_dir/'):
            files = os.listdir('datanode_dir/')
            for file in files:
                os.remove(f'datanode_dir/{file}')


    def get_file_lock(self, file_name):
        if file_name not in self.file_locks:
            self.file_locks[file_name] = threading.Lock()
        return self.file_locks[file_name]

    # usada na gambiarra da main
    def hello(self):
        return "hello world"

    '''
    Cria socket para main enviar arquivo, delega esse socket pra thread que roda store_image
    e retorna a porta para a main poder se conectar
    '''
    def store_image_socket(self, image_name):
        print('criando socket')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', 0))
        port = sock.getsockname()[1]
        t = threading.Thread(target=store_image, args=(image_name, sock), daemon=True)
        print('disparando thread')
        t.start()
        return port
    '''
    Semelhante à anterior, mas pra recuperar arquivo
    '''
    def retrieve_image_socket(self, image_name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', 0))
        port = sock.getsockname()[1]
        t = threading.Thread(target=retrieve_image, args=(image_name, sock), daemon=True)
        t.start()
        return port

    def list_images(self):
        return os.listdir('datanode_dir/')

    def delete_image(self, image_name):
        os.remove(f'datanode_dir/{image_name}')



if __name__ == '__main__':
    Pyro5.config.PREFER_IP_VERSION = 4
    datanode_name = f"datanode_{uuid.uuid4().hex}" # nome dinamico
    daemon = Pyro5.api.Daemon() 
    uri = daemon.register(Datanode())
    ns = Pyro5.api.locate_ns()
    ns.register(datanode_name, uri) 
    print("Ready. Object uri =", uri) 
    daemon.requestLoop()                    # start the event loop of the server to wait for calls
