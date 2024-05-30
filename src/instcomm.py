import zmq
import json
import time
import logging

class Instrument:
    def __init__(self, host='localhost', port=15555, log_file='instrument.log'):
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{self.host}:{self.port}')
        
        # Configure logging to a file and console
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

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
                "id": "9998"}
        response = self._send_command(command)
        if response and "result" in response:
            return response["result"]
        return None  

class Cryo(Instrument):
    def set_temp(self, temp, rate=1):
        command = {
            "jsonrpc": "2.0", 
            "method": "Set Temperature", 
            "params": {"Temperature (K)": temp, "Rate (K/min)": rate}, 
            "id": "560"
        }
        response = self._send_command(command)
        if response:
            # self.logger.info(response)
            self.logger.info(f"Setting temperature to {temp} K at {rate} K/min")
            while not self._is_temperature_set(temp):
                time.sleep(1)
            self.logger.info(f"Temperature set to {temp} K")

    def set_field(self, field: float, rate= 1):
        command = {
            "jsonrpc": "2.0", 
            "method": "Set Magnet", 
            "params": {"Field (T)": field, "Rate (T/min)": rate}, 
            "id": "580"
        }
        response = self._send_command(command)
        if response:
            # self.logger.info(response)
            self.logger.info(f"Setting field to {field} T at {rate} T/min")
            while not self._is_field_set(field):
                time.sleep(1)
            self.logger.info(f"Field set to {field} T")

    def get_temp(self):
        command = {"jsonrpc": "2.0", "method": "Get Temperature", "id": "561"}
        response = self._send_command(command)
        if response and "result" in response:
            return response["result"].get("Temperature (K)")
        return None

    def get_field(self):
        command = {"jsonrpc": "2.0", "method": "Get Magnet", "id": "581"}
        response = self._send_command(command)
        if response and "result" in response:
            return response["result"].get("Field (T)")
        return None

    def _is_temperature_set(self, target_temp):
        current_temp = self.get_temp()
        if current_temp is not None:
            return current_temp == target_temp
        return False

    def _is_field_set(self, target_field):
        current_field = self.get_field()
        if current_field is not None:
            return current_field == target_field
        return False
     
class DAQ(Instrument):
    def setAO_DC(self, channel, voltage):
        command = {
            "jsonrpc": "2.0", 
            "method": "setAO_DC", 
            "params": {"AO Channel": channel, "DC (V)": voltage}, 
            "id": "600"
        }
        response = self._send_command(command)
        # if response:
            # self.logger.info(response)

    def getAO(self):
        command = {
            "jsonrpc": "2.0", 
            "method": "getAO",
            "id": "601"
        }
        response = self._send_command(command)
        if response:
            self.logger.info(response)

    def getResults(self, channel, measurement = 'X', ref = 1):
        key = f"AI{channel}.Mean" if measurement == 'Mean' else f"AI{channel}.Ref{ref}.{measurement}"
        command = {
            "jsonrpc": "2.0", 
            "method": "getResults",
            "id": "602"
        }
        response = self._send_command(command)
        results = response['result']['Results (Dictionary)']
        results_dict = {item['key']: item['value'] for item in results}
        return results_dict.get(key)
        # if response:
        #     self.logger.info(response)
