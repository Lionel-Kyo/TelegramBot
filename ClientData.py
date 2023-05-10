import socket

class ClientData:
    def __init__(self, client : socket, address):
        self.client : socket = client
        self.address = address
        self.playerName : str = None
        self.playerID : int = -1
    
    def Close(self):
        self.client.close()