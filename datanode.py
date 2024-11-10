import Pyro5.api

DATANODE_INSTANCE = 1

@Pyro5.api.expose
class Datanode(object):
    def __init__(self) -> None:
        pass
    def testing(self, n):
        return f"the answer is {n}"
    
    def store_image(self, image_id):
        pass

    def retrieve_image(self, image_id):
        pass

    def list_images(self):
        pass



if __name__ == '__main__':
    daemon = Pyro5.server.Daemon()
    ns = Pyro5.api.locate_ns()
    uri = daemon.register(Datanode)
    ns.register(f"datanode_{DATANODE_INSTANCE:02}", uri)
    print("Ready.")
    daemon.requestLoop()