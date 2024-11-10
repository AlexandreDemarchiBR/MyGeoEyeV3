import Pyro5.api
import os

class Client:
    def __init__(self) -> None:
        self.controller = Pyro5.api.Proxy("PYRONAME:controller")    # use name server object lookup uri shortcut

    def upload_image(self, image_path: str):
        image_name = os.path.basename(image_path)

    def list_images(self) -> str:
        return self.controller.list_images()
    
    def download_image(self, image_name: str):
        pass

    def delete_image(self, image_name: str):
        pass

    def start(self):
        pass
if __name__ == '__main__':
    pass