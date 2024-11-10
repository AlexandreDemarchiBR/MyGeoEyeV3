import Pyro4
import time
import threading
import random
import os
import numpy as np
import matplotlib.pyplot as plt

class ScaleTest:
    def __init__(self, controller_uri, num_datanodes):
        self.controller = Pyro4.Proxy(controller_uri)
        self.num_datanodes = num_datanodes

    def generate_test_image(self, size_kb: int = 100) -> bytes:
        """Gera uma imagem de teste sintética"""
        return os.urandom(size_kb * 1024)

    def test_upload_time(self, num_images: int, images_per_second: int):
        """Testa o tempo de upload de múltiplas imagens"""
        upload_times = []
        
        for i in range(num_images):
            start_time = time.time()
            
            # Gera uma imagem de teste
            image_data = self.generate_test_image()
            filename = f"test_image_{i}.bin"
            
            # Realiza o upload
            self.controller.distribute_image(filename, image_data)
            
            end_time = time.time()
            upload_times.append(end_time - start_time)
            
            # Controla a taxa de upload
            if (i + 1) % images_per_second == 0:
                time.sleep(1)
        
        return upload_times

    def test_download_time(self, num_images: int, images_per_second: int):
        """Testa o tempo de download de múltiplas imagens"""
        download_times = []
        image_list = self.controller.list_images()
        
        for i in range(num_images):
            start_time = time.time()
            
            # Seleciona uma imagem aleatória
            filename = random.choice(image_list)
            
            # Realiza o download
            self.controller.retrieve_image(filename)
            
            end_time = time.time()
            download_times.append(end_time - start_time)
            
            # Controla a taxa de download
            if (i + 1) % images_per_second == 0:
                time.sleep(1)
        
        return download_times

    def run_benchmarks(self):
        """Executa benchmarks de upload e download"""
        scenarios = [
            (10, 1),   # 10 imagens, 1 por segundo
            (50, 5),   # 50 imagens, 5 por segundo
            (200, 10)  # 200 imagens, 10 por segundo
        ]
        
        results = {
            'upload_times': {},
            'download_times': {}
        }
        
        for num_images, images_per_second in scenarios:
            upload_times = self.test_upload_time(num_images, images_per_second)
            download_times = self.test_download_time(num_images, images_per_second)
            
            results['upload_times'][(num_images, images_per_second)] = {
                'mean': np.mean(upload_times),
                'std': np.std(upload_times)
            }
            
            results['download_times'][(num_images, images_per_second)] = {
                'mean': np.mean(download_times),
                'std': np.std(download_times)
            }
        
        self._plot_results(results)
        return results

    def _plot_results(self, results):
        """Gera gráficos de benchmark"""
        plt.figure(figsize=(12, 5))
        
        # Gráfico de tempos de upload
        plt.subplot(1, 2, 1)
        upload_means = [results['upload_times'][k]['mean'] for k in results['upload_times']]
        upload_labels = [f"{k[0]} imgs\n{k[1]}/s" for k in results['upload_times']]
        plt.bar(upload_labels, upload_means)
        plt.title(f'Tempo Médio de Upload\n({self.num_datanodes} Datanodes)')
        plt.ylabel('Tempo (s)')
        
        # Gráfico de tempos de download
        plt.subplot(1, 2, 2)
        download_means = [results['download_times'][k]['mean'] for k in results['download_times']]
        download_labels = [f"{k[0]} imgs\n{k[1]}/s" for k in results['download_times']]
        plt.bar(download_labels, download_means)
        plt.title(f'Tempo Médio de Download\n({self.num_datanodes} Datanodes)')
        plt.ylabel('Tempo (s)')
        
        plt.tight_layout()
        plt.savefig(f'benchmark_{self.num_datanodes}_datanodes.png')

def main():
    # URI do controlador (substitua pela URI correta)
    controller_uri = "PYRO:obj_xxxx@localhost:9090"
    
    # Testes para 3 e 6 datanodes
    for num_datanodes in [3, 6]:
        scale_test = ScaleTest(controller_uri, num_datanodes)
        results = scale_test.run_benchmarks()
        print(f"Resultados para {num_datanodes} datanodes:")
        print(results)

if __name__ == "__main__":
    main()