import tkinter as tk
import socket
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from multiprocessing import Process, Queue, Value
import io
from baseband import vdif
from datetime import datetime, timedelta

def receive_data(port, output_file, raw_data_queue, check_var):
    # Create a UDP socket
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_.bind(('0.0.0.0', port))
    print(f"Listening on port {port}")

    try:
        with open(output_file, 'wb') as f:
            print(f"Opened {output_file} for writing...")
            while True:
                data, addr = socket_.recvfrom(2**14)  # arg is buffer size in bytes
                if data:
                    raw_data_queue.put(data)
                    if check_var:
                        f.write(data)
    finally:
        socket_.close()
        print(f"Socket on port {port} closed.")

def process_data(raw_data_queue, processed_data_queue, channel, buffer_length_ms, frame_rate, sample_rate, proc_buffer_start_time):
    buffer = io.BytesIO()
    fh_buff = vdif.open(buffer, 'rb')
    proc_buffer = io.BytesIO()
    fh_proc = vdif.open(proc_buffer, 'rb')

    while True:
        data = raw_data_queue.get()
        buffer.seek(0)
        buffer.write(data)
        buffer.seek(0)
        buffer_frame = fh_buff.read_frame()

        if not buffer_frame.header['thread_id'] == channel:
            continue

        if frame_rate.value <= buffer_frame.header['frame_nr']:
            frame_rate.value = np.int32(buffer_frame.header['frame_nr'] + 1)
            sample_rate.value = np.int32(frame_rate.value) * np.int32(np.int32(len(data)-32)*8/2**buffer_frame.header['bits_per_sample'])
            print(f"frame_rate, sample_rate: {frame_rate.value}, {sample_rate.value}")
            if proc_buffer_start_time is not None:
                proc_buffer = io.BytesIO()
                proc_buffer_start_time = None
        else:
            current_frame_time = calculate_first_sample_time(buffer_frame, frame_rate)
            if proc_buffer_start_time is None:
                proc_buffer_start_time = current_frame_time

            time_diff_ms = (current_frame_time - proc_buffer_start_time).total_seconds() * 1000
            if time_diff_ms < buffer_length_ms:
                print(f"Time Diff: {time_diff_ms} ms. Adding frame to proc_buffer")
            else:
                proc_buffer.seek(0)
                fh_proc = vdif.open(proc_buffer, 'rb')
                proc_info = fh_proc.info()
                buffer_frame = fh_proc.read_frame()
                proc_data = buffer_frame.data

                for i in range(proc_info['number_of_framesets']-1):
                    buffer_frame = fh_proc.read_frame()
                    proc_data = np.append(proc_data, buffer_frame.data)

                x_Hz = np.fft.fftshift(np.fft.fftfreq(len(proc_data), d=1/sample_rate.value))
                y = np.abs(np.fft.fftshift(np.fft.fft(proc_data, axis=0)))

                processed_data_queue.put((x_Hz, y, proc_buffer_start_time))

                proc_buffer = io.BytesIO()
                proc_buffer_start_time = current_frame_time
                print(f"Time Diff: {time_diff_ms} ms. Processed proc_buffer and writing frame to new buffer")

            # In either case, write data to proc_buffer
            proc_buffer.write(data)

def calculate_first_sample_time(frame, frame_rate):
    epoch = frame['ref_epoch']
    whole_seconds_from_epoch = frame['seconds']
    seconds_from_epoch = whole_seconds_from_epoch + frame['frame_nr']/frame_rate.value
    years = epoch // 2
    half_year = epoch % 2
    if half_year == 0:
        base_date = datetime(2000 + years, 1, 1)
    else:
        base_date = datetime(2000 + years, 7, 1)
    first_sample_time = base_date + timedelta(seconds=seconds_from_epoch)
    return first_sample_time

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
        self.last_plot_time = None

        # Create checkbox to control packet writing
        self.check_var = tk.IntVar()
        self.write_checkbox = tk.Checkbutton(self.main_frame, text="Write packets to file", variable=self.check_var)
        self.write_checkbox.pack()

        # Create entry fields for integration time and x-min/x-max
        self.integration_time_label = tk.Label(self.main_frame, text="Integration time (seconds):")
        self.integration_time_label.pack()
        self.integration_time_entry = tk.Entry(self.main_frame)
        self.integration_time_entry.insert(0, "0.25")  # Default integration time
        self.integration_time_entry.pack()

        self.x_min_label = tk.Label(self.main_frame, text="X-min:")
        self.x_min_label.pack()
        self.x_min_entry = tk.Entry(self.main_frame)
        self.x_min_entry.insert(0, "-1")  # Default x-min
        self.x_min_entry.pack()

        self.x_max_label = tk.Label(self.main_frame, text="X-max:")
        self.x_max_label.pack()
        self.x_max_entry = tk.Entry(self.main_frame)
        self.x_max_entry.insert(0, "1")  # Default x-max
        self.x_max_entry.pack()
        
        
        self.plot_interval_s = np.float64(self.integration_time_entry.get())

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

        # Initialize queues
        self.raw_data_queue = Queue()
        self.processed_data_queue = Queue()

        self.receiving = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Define frame rate and sample rate, which are learned from the first 1s of data
        self.frame_rate = Value('i', 0)  # 'i' for integer, 'f' for float
        self.sample_rate = Value('i',0)

        # Start the receiving and processing processes
        self.receiver_process = Process(target=receive_data, args=(port, output_file, self.raw_data_queue, self.check_var.get()))
        self.processor_process = Process(target=process_data, args=(self.raw_data_queue, self.processed_data_queue, self.channel, self.buffer_length_ms, self.frame_rate, self.sample_rate, self.proc_buffer_start_time))
        self.receiver_process.start()
        self.processor_process.start()
        
        # Start the visualization update loop
        self.update_plot()

    def stop_receiving(self):
        self.receiving = False
        if self.receiver_process.is_alive():
            self.receiver_process.terminate()
            self.receiver_process.join()
        if self.processor_process.is_alive():
            self.processor_process.terminate()
            self.processor_process.join()
        self.status_label.config(text="Receiver stopped.")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.reset()
        print("Stopped receiving. Reset and ready for new stream")

    def reset(self):
        # Initialize socket and thread variables
        self.socket = None
        self.receiver_process = None
        self.processor_process = None
        self.receiving = False

        self.buffer = io.BytesIO()
        self.fh_buff = vdif.open(self.buffer, 'rb')        
        self.frame_rate = Value('i', 0)  # 'i' for integer, 'f' for float
        self.sample_rate = Value('i',0)
        self.buffer_frame = None
        self.proc_buffer = io.BytesIO()
        self.fh_proc = vdif.open(self.proc_buffer, 'rb')
        self.proc_buffer_start_time = None

        # Initialize the plot buffer
        self.plot_buffer = []
        self.last_plot_time = None

    def update_plot(self):
        new_data = []
        while not self.processed_data_queue.empty():
            x_Hz, y, proc_buffer_start_time = self.processed_data_queue.get()
            new_data.append((x_Hz, y, proc_buffer_start_time))
        
        if new_data:
            if len(self.plot_buffer) == 0:
                sec_per_row = len(new_data[0][1]) * 1/self.sample_rate.value
                num_rows = np.int32(np.float64(self.integration_time_entry.get()) // sec_per_row)
                print(f"Initializing plot_buffer with num_rows {num_rows} and num_col {len(new_data[0][1])}")
                self.plot_buffer = np.full((num_rows, len(new_data[0][1])), np.nan)

            for _, y, proc_buffer_start_time in new_data:
                self.plot_buffer = np.vstack((y, self.plot_buffer[:-1]))


            if self.last_plot_time is None:
                print('Initializing line plot')
                non_coherent_sum = 10*np.log10(np.nanmean(self.plot_buffer, axis=0))
                self.last_plot_time = new_data[-1][2]
                self.line, = self.ax.plot(x_Hz / 1e6, non_coherent_sum)
                self.ax.set_xlim([float(self.x_min_entry.get()), float(self.x_max_entry.get())])
                self.ax.set_xlabel('Frequency (MHz)')
                self.ax.set_ylabel('Intensity')
                self.ax.set_title(f'{self.integration_time_entry.get()}s Non-coherent sum until {new_data[-1][2]}')
                self.canvas.draw()
                
            elif self.last_plot_time + timedelta(seconds=self.plot_interval_s) <= new_data[-1][2]:
                print(f"Updating line plot. Time since plot: {new_data[-1][2] - self.last_plot_time}")
                self.last_plot_time = new_data[-1][2]
                non_coherent_sum = 10*np.log10(np.nanmean(self.plot_buffer, axis=0))
                self.line.set_ydata(non_coherent_sum)
                self.ax.set_title(f'{self.integration_time_entry.get()}s Non-coherent sum until {new_data[-1][2]}')
                self.canvas.draw()

        if self.receiving:
            self.root.after(10, self.update_plot)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    receiver = VDIFReceiver()
    receiver.run()