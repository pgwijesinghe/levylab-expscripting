import zmq

class Experiment:
    def __init__(self, host='localhost', port=15555):
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{self.host}:{self.port}')

    def set_temp(self, temp, rate=1):
        self.socket.send_string(f'set_temp:{temp},{rate}')
        print(self.socket.recv_string()) 
    
    def set_field(self, field, rate=1):
        self.socket.send_string(f'set_field:{field},{rate}')
        print(self.socket.recv_string()) 
    
    def set_AO(self, channel, DC):
        self.socket.send_string(f'set_AO:{channel},{DC}')
        print(self.socket.recv_string()) 

class Sequence(Experiment):
    pass

    