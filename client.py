import Pyro5.api
import os
import socket
from itertools import cycle
import threading
import time
import matplotlib.pyplot as plt
from itertools import cycle

CHUNK_SIZE = 10*1024*1024

class Client:
    '''
    Usando nameserver, nos conectamos à main, usamos a gambiarra da chamada remota pra garantir
    a conexão.
    '''
    def __init__(self) -> None:
        with open('main_dir/ns_host.txt') as f:
            ns_ip = f.readline()
        self.ns = Pyro5.api.locate_ns(ns_ip)
        self.uri = self.ns.lookup("mainserver")
        self.main = Pyro5.api.Proxy(self.uri)
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

    '''
    Só recebe os dados, sem persistir. Usado exclusivamente para benchmark
    (o objetivo é testar os servidores, não o armazenamento do cliente)
    '''
    def pseudo_download_image(self, file_name):
        new_proxy = Pyro5.api.Proxy(self.uri)
        start_time = time.time()
        port = new_proxy.download_image_socket(file_name) ############
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.main_ip, port))
            while True:
                chunk = s.recv(CHUNK_SIZE)
                if not chunk: break
        end_time = time.time()
        duration = end_time - start_time
        self.thread_data.append((start_time - self.benchmark_start_time, duration))
    

    def download_benchmark(self, file_name_list, threads_per_second, duration_seconds):
        circular_queue = cycle(file_name_list)
        self.thread_data = []
        threads = []
        self.benchmark_start_time = time.time()
        end_time = self.benchmark_start_time + duration_seconds

        interval = 1/threads_per_second
        end_time = time.time() + duration_seconds
        while time.time() < end_time:

            thread = threading.Thread(target=self.pseudo_download_image, args=(next(circular_queue),))
            threads.append(thread)
            thread.start()
            time.sleep(interval)
        for thread in threads:
            thread.join()

        self.thread_data.sort()
        x = [data[0] for data in self.thread_data]  # Start times
        y = [data[1] for data in self.thread_data]  # Durations
        plt.figure(figsize=(10, 5))
        plt.plot(x, y, 'o-', label="Thread Duration")
        plt.xlabel("Time (seconds) since program start")
        plt.ylabel("Thread Duration (seconds)")
        plt.title("Thread Execution Duration Over Time")
        plt.legend()
        plt.show()



if __name__ == '__main__':
    Pyro5.config.PREFER_IP_VERSION = 4
    c = Client()
    print("Teste de envio")
    c.send_image('client_dir/CBERS_4_AWFI_20240830_178_099_L4_BAND13.tif')

    c.send_image('client_dir/blob1.jpg')
    c.send_image('client_dir/blob2.jpg')
    c.send_image('client_dir/blob3.jpg')
    #input('...')
    #print("Teste de listagem")
    #print(c.list_images())
    #input('...')
    #print("Teste de download")
    #c.download_image('CBERS_4_AWFI_20240830_178_099_L4_BAND13.tif')
    #input('...')
    blobs = ['blob1.jpg','blob2.jpg','blob3.jpg']
    print("benchmark")
    print("1 img/s")
    c.download_benchmark(blobs, 1, 10)
    input('...')
    print("5 img/s")
    c.download_benchmark(blobs, 5, 10)
    input('...')
    print("10 img/s")
    c.download_benchmark(blobs, 10, 10)
    input('...')


    print("Teste de deleção")
    c.delete_image('CBERS_4_AWFI_20240830_178_099_L4_BAND13.tif')
    print("Teste de listagem")
    print(c.list_images())
