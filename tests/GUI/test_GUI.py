import zmq
import json
import time
import logging
import tkinter as tk
from threading import Thread

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

class PPMS(Instrument):
    def set_temp(self, temp, rate=1):
        command = {
            "jsonrpc": "2.0", 
            "method": "Set Temperature", 
            "params": {"Temperature (K)": temp, "Rate (K/min)": rate}, 
            "id": "560"
        }
        response = self._send_command(command)
        if response:
            self.logger.info(response)
            self.logger.info(f"Setting temperature to {temp} K at {rate} K/min")
            while not self._is_temperature_set(temp):
                time.sleep(1)
            self.logger.info(f"Temperature set to {temp} K")

    def set_field(self, field, rate=1):
        command = {
            "jsonrpc": "2.0", 
            "method": "Set Magnet", 
            "params": {"Field (T)": field, "Rate (T/min)": rate}, 
            "id": "580"
        }
        response = self._send_command(command)
        if response:
            self.logger.info(response)
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

class Lockin(Instrument):
    def setAO_DC(self, channel, voltage):
        command = {
            "jsonrpc": "2.0", 
            "method": "setAO_DC", 
            "params": {"AO Channel": channel, "DC (V)": voltage}, 
            "id": "60"
        }
        response = self._send_command(command)
        if response:
            self.logger.info(response)

class ExperimentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Experiment Progress")
        self.label = tk.Label(root, text="Current Step: Initializing", font=("Helvetica", 16))
        self.label.pack(pady=20)
    
    def update_status(self, status):
        self.label.config(text=f"Current Step: {status}")

def run_experiment(ppms, lockin, gui):
    channel_gate = 2
    temp_list = [300, 350, 400]
    field_list = [-1, 0, 1]
    lockin_list = [0.01, 0.05, 0.1]

    try:
        for field in field_list:
            gui.update_status(f"Setting field to {field} T")
            ppms.set_field(field, 2)
            for temp, voltage in zip(temp_list, lockin_list):
                gui.update_status(f"Setting temperature to {temp} K")
                ppms.set_temp(temp, 50)
                gui.update_status(f"Setting lockin voltage to {voltage} V")
                lockin.setAO_DC(channel_gate, voltage)
    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")
        gui.update_status("Error occurred")

def main():
    ppms_port = 29270
    lockin_port = 29170
    log_file = 'instrument.log'

    # Initialize instruments
    ppms = PPMS(port=ppms_port, log_file=log_file)
    lockin = Lockin(port=lockin_port, log_file=log_file)

    # Setup GUI
    root = tk.Tk()
    gui = ExperimentGUI(root)

    # Run experiment in a separate thread to keep the GUI responsive
    experiment_thread = Thread(target=run_experiment, args=(ppms, lockin, gui))
    experiment_thread.start()

    root.mainloop()

if __name__ == "__main__":
    main()
