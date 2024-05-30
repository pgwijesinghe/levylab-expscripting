'''
Modified Instrument class to dynamically create methods for each command.
Each command is acquired from the instrument by calling the 'HELP' method.
The 'HELP' method returns a list of available commands that can be used to create methods.
help(method) can be used to get the parameters for a specific method.
'''

import zmq
import json
import time
import logging

class Instrument:
    def __init__(self, name, host='localhost', port=15555, log_file='instrument.log'):
        self.name = name
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{self.host}:{self.port}')
        
        # Log to file and console
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self._initialize_commands()

    def _send_command(self, command):
        try:
            message = json.dumps(command)
            self.socket.send_string(message)
            response = self.socket.recv_string()
            return json.loads(response)
        except (zmq.ZMQError, json.JSONDecodeError) as e:
            self.logger.error(f"Error sending command: {e}")
            return None
    
    def help(self, method=None):
        if method:  
            command = {
                "jsonrpc": "2.0", 
                "method": "HELP", 
                "params": {"Command": method},
                "id": "9999"
            }
        else:
            command = {
                "jsonrpc": "2.0", 
                "method": "HELP", 
                "id": "9998"
            }
        response = self._send_command(command)
        if response and "result" in response:
            return response["result"]
        return None
    
    def _initialize_commands(self):
        commands = self.help()
        if commands:
            for command in commands:
                self._create_command_method(command)
    
    def _create_command_method(self, command_name):
        def method(self, **kwargs):
            command = {
                "jsonrpc": "2.0", 
                "method": command_name, 
                "params": kwargs,
                "id": str(int(time.time()))
            }
            print(command)
            # # response = self._send_command(command)
            # if response and "result" in response:
            #     return response["result"]
            # return None
        
        method_name = command_name
        setattr(self, method_name, method.__get__(self))
        self.logger.info(f"Created method '{method_name}' for instrument '{self.name}'")

if __name__ == "__main__":
    log_file = 'tests\instcomm_v3.log'
    lockin = Instrument(name='lockin', port=29170, log_file=log_file)
    ppms = Instrument(name='ppms', port=29270, log_file=log_file)
    # print(lockin.help('Set Temperature'))
    lockin.getAUX()
    # print(*lockin.help(), sep='\n') # better if we can give some documentation here