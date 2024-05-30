import zmq
import json
import time

class Instrument:
    def __init__(self, host='localhost', port=15555):
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{self.host}:{self.port}')

    def set_temp(self, temp, rate=1):
        command = {"jsonrpc": "2.0", "method": "Set Temperature", "params":{"Temperature (K)":temp, "Rate (K/min)": rate}, "id":"560"}
        message = json.dumps(command)
        self.socket.send_string(message)
        print(self.socket.recv_string())
        print(f"Setting temperature to {temp} K at {rate} K/min")
        while self.get_temp() != temp:
            pass
        print(f"Temperature Set to {temp} K")
    
    def set_field(self, field, rate=1):
        command = {"jsonrpc": "2.0", "method": "Set Magnet", "params":{"Field (T)":field, "Rate (T/min)": rate}, "id":"580"}
        message = json.dumps(command)
        self.socket.send_string(message)
        print(self.socket.recv_string())
        print(f"Setting field to {field} T at {rate} T/min")
        while self.get_field() != field:
            pass
        print(f"Field Set to {field} T") 

    def get_temp(self):
        command = {"jsonrpc": "2.0", "method": "Get Temperature", "id":"561"}
        message = json.dumps(command)
        self.socket.send_string(message)
        resp = json.loads(self.socket.recv_string())["result"]
        return resp["Temperature (K)"]

    def get_field(self):
        command = {"jsonrpc": "2.0", "method": "Get Magnet", "id":"581"}
        message = json.dumps(command)
        self.socket.send_string(message)
        resp = json.loads(self.socket.recv_string())["result"]
        return resp["Field (T)"]

    def setAO_DC(self, channel, voltage):
        command = {"jsonrpc": "2.0", "method": "setAO_DC", "params":{"AO Channel":channel, "DC (V)": voltage}, "id":"60"}
        message = json.dumps(command)
        self.socket.send_string(message)
        print(self.socket.recv_string()) 

class Sequence(Instrument):
    pass