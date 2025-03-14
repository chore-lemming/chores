import tkinter as tk
import socket
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import io
# import baseband
from baseband import vdif
from datetime import datetime, timedelta

class VDIFReceiver:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VDIF Receiver")

        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create port entry field
        self.port_label = tk.Label(self.main_frame, text="Port to listen on:")
        self.port_label.pack()
        self.port_entry = tk.Entry(self.main_frame)
        self.port_entry.insert(0, "7100")  # Default port
        self.port_entry.pack()

        # Create output file entry field
        self.file_label = tk.Label(self.main_frame, text="Output file name:")
        self.file_label.pack()
        self.file_entry = tk.Entry(self.main_frame)
        self.file_entry.insert(0, "received.vdif")  # Default file name
        self.file_entry.pack()

        # Create start and stop buttons
        self.start_button = tk.Button(self.main_frame, text="Start Listening", command=self.start_receiving)
        self.start_button.pack()
        self.stop_button = tk.Button(self.main_frame, text="Stop Listening", command=self.stop_receiving, state=tk.DISABLED)
        self.stop_button.pack()

        # Create status label
        self.status_label = tk.Label(self.main_frame, text="Status: Ready")
        self.status_label.pack()

        # Initialize socket and thread variables
        self.socket = None
        self.receiving_thread = None
        self.receiving = False

        # Initialize data for plotting
        self.data = []
        self.plot_frame = tk.Frame(self.main_frame)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.buffer = io.BytesIO()
        self.fh = vdif.open(self.buffer, 'rb')
        self.frame_rate = 0
        self.sample_rate = 0
        self.buffer_frame = None

        # Create a matplotlib figure and axis
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def start_receiving(self):
        port = int(self.port_entry.get())
        output_file = self.file_entry.get()
        print(f"Listening on port {port} and writing to " + output_file)

        # Create a UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', port))
        self.status_label.config(text=f"Listening on port {port}")

        self.receiving = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Start the receiving thread
        self.receiving_thread = threading.Thread(target=self.receive_data, args=(output_file,))
        self.receiving_thread.start()

    def stop_receiving(self):
        self.receiving = False
        if self.socket:
            self.socket.close()
            self.status_label.config(text="Receiver stopped.")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.frame_rate = 0
        print("Stopped receiving ")

    def receive_data(self, output_file):
        with open(output_file, 'wb') as f:
            self.status_label.config(text=f"Receiving data to {output_file}...")
            frame_count = 0
            while self.receiving:
                try:
                    data, addr = self.socket.recvfrom(4096)  # Buffer size is 4096 bytes
                    if data:
                        print(f"Received {len(data)} bytes from {addr}")
                        f.write(data)
                        self.data.append(len(data))  # Store the length of received data
                        frame_count += 1
                        
                        if self.frame_rate == 0:
                            self.buffer.seek(0)
                            self.buffer.write(data)
                            self.buffer.seek(0)
                            self.buffer_frame = self.fh.read_frame()
                            print(self.fh.info())
                            self.frame_rate = np.float64(self.fh.info()['frame_rate'])
                            self.sample_rate = np.float64(self.fh.info()['sample_rate'])

                        # Call process_data every N frames
                        if frame_count % 100 == 0:  # Change 10 to any N you want
                            self.buffer.seek(0)
                            self.buffer.write(data)
                            self.buffer.seek(0)
                            self.buffer_frame = self.fh.read_frame()
                            self.process_data()
                            

                except Exception as e:
                    if not self.receiving:  # If we are stopping, ignore exceptions
                        break
                    print(f"Error receiving data: {e}")

        self.status_label.config(text="Data written to " + output_file)
        print("Data written to " + output_file)

    def process_data(self):
        # Update the plot with the current data
        # print(baseband.file_info(self.buffer))
        self.ax.clear()
        frame_data = self.buffer_frame.data
        x_Hz = np.fft.fftshift(np.fft.fftfreq(len(frame_data),d=1/self.sample_rate))
        self.ax.plot(x_Hz/1e6, 10*np.log10(np.abs(np.fft.fft(frame_data, axis=0))))
        self.ax.set_title("FFT for " + 
                          f"Thread {self.buffer_frame.header['thread_id']} " + 
                          str(self.calculate_first_sample_time(frame=self.buffer_frame)))
        self.ax.set_xlabel('Frequency (MHz)')
        self.ax.set_ylabel('dB')
        # self.ax.legend()
        self.canvas.draw()

    def run(self):
        self.root.mainloop()
        
    # Function to calculate the time of the first sample in a VDIF frame
    def calculate_first_sample_time(self, frame):

        # Get the epoch (half years since 2000) and seconds from epoch
        epoch = frame['ref_epoch']
        whole_seconds_from_epoch = frame['seconds']
        
        # Get fractional seconds using frame number and frame rate
        seconds_from_epoch = whole_seconds_from_epoch + \
            frame['frame_nr']/self.frame_rate
        
        # Set the epoch
        years = epoch // 2
        half_year = epoch % 2
        
        if half_year == 0:
            base_date = datetime(2000 + years, 1, 1)
        else:
            base_date =  datetime(2000 + years, 7, 1)
        
        # Calculate the time of the first sample
        first_sample_time = base_date + timedelta(seconds=seconds_from_epoch)
        
        return first_sample_time
        
if __name__ == "__main__":
    receiver = VDIFReceiver()
    receiver.run()
