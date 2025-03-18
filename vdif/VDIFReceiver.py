import tkinter as tk
import socket
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import io
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

        # Create channel selection field
        self.channel_label = tk.Label(self.main_frame, text="Channel to process:")
        self.channel_label.pack()
        self.channel_entry = tk.Entry(self.main_frame)
        self.channel_entry.insert(0, "0")  # Default channel
        self.channel_entry.pack()

        # Create buffer length entry field
        self.buffer_length_label = tk.Label(self.main_frame, text="Buffer length (ms):")
        self.buffer_length_label.pack()
        self.buffer_length_entry = tk.Entry(self.main_frame)
        self.buffer_length_entry.insert(0, "10")  # Default buffer length
        self.buffer_length_entry.pack()

        # Create start and stop buttons
        self.start_button = tk.Button(self.main_frame, text="Start Listening", command=self.start_receiving)
        self.start_button.pack()
        self.stop_button = tk.Button(self.main_frame, text="Stop Listening", command=self.stop_receiving, state=tk.DISABLED)
        self.stop_button.pack()

        # Create status label
        self.status_label = tk.Label(self.main_frame, text="Status: Ready")
        self.status_label.pack()

        # Initialize data for plotting
        self.plot_frame = tk.Frame(self.main_frame)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create a matplotlib figure and axis
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.plot_interval_s = 0.1
        self.last_plot_time = None
        self.img = None
        self.cbar = None

        # Create checkbox to control packet writing
        # Create a variable to hold the state of the checkbox
        self.check_var = tk.IntVar()

        self.write_checkbox = tk.Checkbutton(self.main_frame, text="Write packets to file", variable=self.check_var)
        self.write_checkbox.pack()

        # Create entry fields for y-extent and x-min/x-max
        self.y_extent_label = tk.Label(self.main_frame, text="Y-extent (seconds):")
        self.y_extent_label.pack()
        self.y_extent_entry = tk.Entry(self.main_frame)
        self.y_extent_entry.insert(0, "2")  # Default y-extent
        self.y_extent_entry.pack()

        self.x_min_label = tk.Label(self.main_frame, text="X-min:")
        self.x_min_label.pack()
        self.x_min_entry = tk.Entry(self.main_frame)
        self.x_min_entry.insert(0, "-0.05")  # Default x-min
        self.x_min_entry.pack()

        self.x_max_label = tk.Label(self.main_frame, text="X-max:")
        self.x_max_label.pack()
        self.x_max_entry = tk.Entry(self.main_frame)
        self.x_max_entry.insert(0, "0.05")  # Default x-max
        self.x_max_entry.pack()

        # Reset internal variables
        self.reset()

        # Automatically start listening
        self.start_receiving()

    def start_receiving(self):
        
        # Clear old data from axis
        self.ax.clear()
        
        port = int(self.port_entry.get())
        output_file = self.file_entry.get()
        self.channel = int(self.channel_entry.get())
        self.buffer_length_ms = np.float64(self.buffer_length_entry.get())
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
        self.reset()
        print("Stopped receiving. Reset and ready for new stream")

    def reset(self):
        # Initialize socket and thread variables
        self.socket = None
        self.receiving_thread = None
        self.receiving = False

        self.buffer = io.BytesIO()
        self.fh_buff = vdif.open(self.buffer, 'rb')
        self.frame_rate = 0
        self.sample_rate = 0
        self.buffer_frame = None
        self.proc_buffer = io.BytesIO()
        self.fh_proc = vdif.open(self.proc_buffer, 'rb')
        self.proc_buffer_start_time = None

        # Initialize the plot buffer
        self.plot_buffer = []
        self.last_plot_time = None
        self.img = None
        if self.cbar is not None:
            self.cbar.remove()

    def receive_data(self, output_file):
        with open(output_file, 'wb') as f:
            self.status_label.config(text=f"Opened {output_file} for writing...")
            while self.receiving:
                try:
                    data, addr = self.socket.recvfrom(4096)  # Buffer size is 4096 bytes
                    if data:
                        if self.check_var.get():
                            f.write(data)

                        # First time receiving data, get frame & sample rates
                        if self.frame_rate == 0:
                            self.buffer.seek(0)
                            self.buffer.write(data)
                            self.buffer.seek(0)
                            self.buffer_frame = self.fh_buff.read_frame()
                            print(self.fh_buff.info())
                            self.frame_rate = np.float64(self.fh_buff.info()['frame_rate'])
                            self.sample_rate = np.float64(self.fh_buff.info()['sample_rate'])

                        # Always write packet to buffer and read as VDIF frame
                        self.buffer.seek(0)
                        self.buffer.write(data)
                        self.buffer.seek(0)
                        self.buffer_frame = self.fh_buff.read_frame()

                        # Read from single packet buffer. Build up processing buffer
                        if self.buffer_frame.header['thread_id'] == self.channel:
                            current_frame_time = self.calculate_first_sample_time(frame=self.buffer_frame)

                            if self.proc_buffer_start_time is None:
                                self.proc_buffer_start_time = current_frame_time

                            time_diff_ms = (current_frame_time - self.proc_buffer_start_time).total_seconds() * 1000

                            if time_diff_ms < self.buffer_length_ms:
                                print(f"Time Diff: {time_diff_ms} ms. Added frame to proc_buffer")
                            else:
                                print(f"Time Diff: {time_diff_ms} ms. Processing proc_buffer")
                                self.process_data()
                                self.proc_buffer = io.BytesIO()
                                self.proc_buffer_start_time = current_frame_time

                            self.proc_buffer.write(data)

                except Exception as e:
                    if not self.receiving:  # If we are stopping, ignore exceptions
                        break
                    print(f"Error receiving data: {e}")

        if self.check_var.get():
            self.status_label.config(text="Data written to " + output_file)
            print("Data written to " + output_file)
        else:
            self.status_label.config(text="Stopped listening and processing")

    def process_data(self):
        # Read number of frames that are in the buffer
        self.proc_buffer.seek(0)
        self.fh_proc = vdif.open(self.proc_buffer, 'rb')
        proc_info = self.fh_proc.info()
        print(proc_info)

        # Read data from frames in the buffer by looping
        # Technically should ensure that frames are in order
        buffer_frame = self.fh_proc.read_frame()
        proc_data = buffer_frame.data

        for i in range(proc_info['number_of_framesets']-1):
            buffer_frame = self.fh_proc.read_frame()
            proc_data = np.append(proc_data, buffer_frame.data)

        # Update the plot with the current data
        x_Hz = np.fft.fftshift(np.fft.fftfreq(len(proc_data), d=1/self.sample_rate))
        y_dB = 10*np.log10(np.abs(np.fft.fftshift(np.fft.fft(proc_data, axis=0))))

        # Add new line to the plot buffer
        if len(self.plot_buffer) == 0:
            sec_per_row = len(y_dB) * 1/self.sample_rate
            num_rows = np.int32(np.float64(self.y_extent_entry.get()) // sec_per_row)
            print(f"Initializing plot_buffer with num_rows {num_rows} and num_col {len(y_dB)}")
            self.plot_buffer = np.full((num_rows, len(y_dB)), np.nan)
        

        # Shift the existing data up by one row
        self.plot_buffer[1:] = self.plot_buffer[:-1]
        self.plot_buffer[0] = y_dB

        # Remove old data exceeding the y-extent
        y_extent = int(self.y_extent_entry.get())

        # Create/Update the color plot
        if self.last_plot_time is None:
            self.last_plot_time = self.proc_buffer_start_time
            self.img = self.ax.imshow(
                np.array(self.plot_buffer), 
                aspect='auto', 
                extent=[x_Hz.min()/1e6, x_Hz.max()/1e6, 0, y_extent], 
                origin='lower')
            self.cbar = plt.colorbar(self.img)
            self.cbar.set_label('Intensity (dB)')

        
        elif self.last_plot_time + timedelta(seconds=self.plot_interval_s) < self.proc_buffer_start_time:
            #self.ax.clear()
            self.img.set_array(self.plot_buffer) 
            
            # Set plot limits
            self.img.set_clim(
                vmin=np.nanmin(self.plot_buffer), 
                vmax=np.nanmax(self.plot_buffer))   
            self.ax.set_xlim([float(self.x_min_entry.get()), float(self.x_max_entry.get())])
            self.ax.set_ylim([0, y_extent])
            self.ax.set_xlabel('Frequency (MHz)')
            self.ax.set_ylabel('Time (s) before ' + str(self.proc_buffer_start_time))
            self.ax.set_title('Spectrogram')
            self.canvas.draw()
            self.last_plot_time = self.proc_buffer_start_time

    def calculate_first_sample_time(self, frame):
        # Function to calculate the time of the first sample in a VDIF frame
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
            base_date = datetime(2000 + years, 7, 1)

        # Calculate the time of the first sample
        first_sample_time = base_date + timedelta(seconds=seconds_from_epoch)

        return first_sample_time

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    receiver = VDIFReceiver()
    receiver.run()