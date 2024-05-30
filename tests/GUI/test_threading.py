import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Dummy classes for Cryo and DAQ (replace these with actual implementations)
class Cryo:
    def __init__(self, port, log_file):
        pass

    def set_field(self, field, rate):
        time.sleep(1)  # simulate time delay for setting field

    def set_temp(self, temp, rate):
        time.sleep(1)  # simulate time delay for setting temperature

class DAQ:
    def __init__(self, port, log_file):
        pass

    def setAO_DC(self, channel, value):
        time.sleep(0.01)  # simulate time delay for setting DC value

    def getResults(self, channel, param, ref_channel):
        return np.random.random()  # simulate measurement

# Experiment parameters
ppms_port = 29270
lockin_port = 29170
log_file = './pyzmq/instrument.log'
channel_source = 1
channel_drain = 1
channel_gate = 2
channel_Ref = 1
temp_list = np.linspace(300, 320, 2)
field_list = np.linspace(-1, 1, 2)
V_list = np.linspace(0, 0.1, 500)
lockin_wait_time = 1

class ExperimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Experiment Control")

        # GUI layout
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(side=tk.TOP, fill=tk.X)

        self.start_button = tk.Button(self.control_frame, text="Start", command=self.start_experiment)
        self.start_button.pack(side=tk.LEFT)

        self.pause_button = tk.Button(self.control_frame, text="Pause", command=self.pause_experiment)
        self.pause_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop_experiment)
        self.stop_button.pack(side=tk.LEFT)

        self.status_text = scrolledtext.ScrolledText(root, height=10)
        self.status_text.pack(fill=tk.BOTH, expand=True)

        self.script_text = scrolledtext.ScrolledText(root, height=15)
        self.script_text.pack(fill=tk.BOTH, expand=True)
        self.load_script()

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack()

        self.paused = threading.Event()
        self.stopped = threading.Event()
        self.experiment_thread = None

    def load_script(self):
        script = """
# Define Experiment
for field in field_list:
    ppms.set_field(field, 10)
    for temp in temp_list:
        ppms.set_temp(temp, 50)
        current = []
        lockin.setAO_DC(channel_gate, V_list[0])
        time.sleep(lockin_wait_time)
        for V in V_list:
            lockin.setAO_DC(channel_gate, V)
            time.sleep(0.01)
            current.append(lockin.getResults(channel_drain, 'X', channel_Ref))

        # plotting
        plt.plot(V_list, current)
        plt.title(f'SimWG IV (B={field} T, T={temp} K)')
        plt.xlabel('Voltage (V)')
        plt.ylabel('Drain Lockin X (V)')
        plt.show()
end_time = time.time()
print(f'Experiment finished in {end_time - start_time} seconds')
"""
        self.script_text.insert(tk.END, script)
        self.script_lines = script.strip().split("\n")

    def log(self, message):
        self.status_text.insert(tk.END, message + '\n')
        self.status_text.see(tk.END)

    def highlight_line(self, line_num):
        self.script_text.tag_remove("highlight", "1.0", tk.END)
        self.script_text.tag_add("highlight", f"{line_num}.0", f"{line_num}.0 lineend")
        self.script_text.tag_config("highlight", background="yellow")
        self.script_text.see(f"{line_num}.0")

    def run_experiment(self):
        ppms = Cryo(port=ppms_port, log_file=log_file)
        lockin = DAQ(port=lockin_port, log_file=log_file)

        start_time = time.time()

        try:
            for field in field_list:
                self.highlight_line(3)
                ppms.set_field(field, 10)
                self.log(f"Set field to {field} T")
                for temp in temp_list:
                    self.highlight_line(5)
                    ppms.set_temp(temp, 50)
                    self.log(f"Set temperature to {temp} K")
                    current = []
                    self.highlight_line(7)
                    lockin.setAO_DC(channel_gate, V_list[0])
                    time.sleep(lockin_wait_time)
                    for V in V_list:
                        if self.stopped.is_set():
                            self.log("Experiment stopped")
                            return
                        self.paused.wait()  # Will block here if paused

                        self.highlight_line(9)
                        lockin.setAO_DC(channel_gate, V)
                        time.sleep(0.01)
                        current.append(lockin.getResults(channel_drain, 'X', channel_Ref))
                        self.log(f"Measured current at V={V} is {current[-1]}")

                    # plotting
                    self.highlight_line(13)
                    self.ax.clear()
                    self.ax.plot(V_list, current)
                    self.ax.set_title(f'SimWG IV (B={field} T, T={temp} K)')
                    self.ax.set_xlabel('Voltage (V)')
                    self.ax.set_ylabel('Drain Lockin X (V)')
                    self.canvas.draw()
        except Exception as e:
            self.log(f"Error: {e}")

        end_time = time.time()
        self.highlight_line(18)
        self.log(f'Experiment finished in {end_time - start_time} seconds')

    def start_experiment(self):
        if self.experiment_thread and self.experiment_thread.is_alive():
            self.log("Experiment already running")
            return
        self.stopped.clear()
        self.paused.set()  # Ensure we are not paused
        self.experiment_thread = threading.Thread(target=self.run_experiment)
        self.experiment_thread.start()
        self.log("Experiment started")

    def pause_experiment(self):
        if self.paused.is_set():
            self.paused.clear()
            self.log("Experiment paused")
        else:
            self.paused.set()
            self.log("Experiment resumed")

    def stop_experiment(self):
        self.stopped.set()
        self.paused.set()  # Ensure any paused wait is released
        self.log("Stopping experiment...")

root = tk.Tk()
app = ExperimentApp(root)
root.mainloop()
