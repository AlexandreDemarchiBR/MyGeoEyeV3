import Pyro5.api
import os
import socket
from itertools import cycle
import threading

CHUNK_SIZE = 10*1024*1024

class Client:
    '''
    Usando nameserver, nos conectamos à main, usamos a gambiarra da chamada remota pra garantir
    a conexão.
    '''
    def __init__(self) -> None:
        self.ns = Pyro5.api.locate_ns()
        self.main = Pyro5.api.Proxy("PYRONAME:mainserver")
        print(self.main.echo_test())
        self.main_ip = self.main._pyroConnection.sock.getpeername()[0]
        if not os.path.exists('client_dir/'):
            os.makedirs('client_dir/')

    '''
    Usando upload_image_socket, pedimos um socket para persistir arquivo de nome file_name,
    usamos a porta retornada para conectar e enviar os dados.
    '''
    def send_image(self, file_path):
        file_name = os.path.basename(file_path)
        port = self.main.upload_image_socket(file_name)###############
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s, open(file_path, 'rb') as f:
            s.connect((self.main_ip, port))
            s.sendfile(f)
    
    '''
    Semelhante à anterior, mas para download
    '''
    def download_image(self, file_name):
        file_path = f'client_dir/downloaded_{file_name}'
        port = self.main.download_image_socket(file_name) ############
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s, open(file_path, 'wb') as f:
            s.connect((self.main_ip, port))
            while True:
                chunk = s.recv(CHUNK_SIZE)
                if not chunk: break
                f.write(chunk)
    
    def list_images(self):
        return self.main.list_images()
    
    def delete_image(self, file_name):
        self.main.delete_image(file_name)


if __name__ == '__main__':
    Pyro5.config.PREFER_IP_VERSION = 4
    c = Client()
    print("Teste de envio")
    c.send_image('client_dir/CBERS_4_AWFI_20240830_178_099_L4_BAND13.tif')
    input('...')
    print("Teste de listagem")
    print(c.list_images())
    input('...')
    print("Teste de download")
    c.download_image('CBERS_4_AWFI_20240830_178_099_L4_BAND13.tif')
    #input('...')
    #print("Teste de deleção")
    #c.delete_image('CBERS_4_AWFI_20240830_178_099_L4_BAND13.tif')
