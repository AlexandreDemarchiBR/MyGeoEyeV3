import Pyro4
import os
import time
import threading
from typing import List, Dict

@Pyro4.expose
class Controller:
    def __init__(self, num_datanodes: int = 3):
        self.datanodes = []
        self.num_datanodes = num_datanodes
        self.image_metadata: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def register_datanode(self, datanode):
        """Registra um datanode no controlador"""
        with self.lock:
            if len(self.datanodes) < self.num_datanodes:
                self.datanodes.append(datanode)
                return True
            return False

    def distribute_image(self, filename: str, image_data: bytes) -> bool:
        """Distribui uma imagem entre os datanodes"""
        if not self.datanodes:
            raise RuntimeError("Nenhum datanode disponível")

        chunk_size = len(image_data) // len(self.datanodes)
        image_chunks = [
            image_data[i:i+chunk_size] 
            for i in range(0, len(image_data), chunk_size)
        ]

        # Garantir que todos os chunks sejam distribuídos
        if len(image_chunks) > len(self.datanodes):
            image_chunks = image_chunks[:len(self.datanodes)]

        try:
            with self.lock:
                # Distribuir chunks entre os datanodes
                for i, (datanode, chunk) in enumerate(zip(self.datanodes, image_chunks)):
                    datanode.store_chunk(filename, chunk, i)

                # Registrar metadados da imagem
                self.image_metadata[filename] = {
                    'total_chunks': len(image_chunks),
                    'size': len(image_data)
                }
            return True
        except Exception as e:
            print(f"Erro ao distribuir imagem: {e}")
            return False

    def list_images(self) -> List[str]:
        """Lista todas as imagens armazenadas"""
        return list(self.image_metadata.keys())

    def retrieve_image(self, filename: str) -> bytes:
        """Recupera uma imagem distribuída"""
        if filename not in self.image_metadata:
            raise FileNotFoundError(f"Imagem {filename} não encontrada")

        metadata = self.image_metadata[filename]
        chunks = [None] * metadata['total_chunks']

        # Recuperar chunks de cada datanode
        for i, datanode in enumerate(self.datanodes[:metadata['total_chunks']]):
            chunks[i] = datanode.retrieve_chunk(filename, i)

        return b''.join(chunks)

    def delete_image(self, filename: str) -> bool:
        """Remove uma imagem de todos os datanodes"""
        if filename not in self.image_metadata:
            return False

        try:
            for i in range(self.image_metadata[filename]['total_chunks']):
                self.datanodes[i].delete_chunk(filename)
            
            del self.image_metadata[filename]
            return True
        except Exception as e:
            print(f"Erro ao deletar imagem: {e}")
            return False

def start_controller(num_datanodes: int = 3):
    """Inicia o serviço de controlador Pyro"""
    controller = Controller(num_datanodes)
    daemon = Pyro4.Daemon()
    uri = daemon.register(controller)

    print(f"Controller URI: {uri}")
    daemon.requestLoop()

if __name__ == "__main__":
    start_controller()
