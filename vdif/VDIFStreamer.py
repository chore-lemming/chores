import tkinter as tk
from tkinter import filedialog
import baseband
from baseband import vdif
import socket
import threading
import time

class VDIFStreamer:
    def __init__(self):
       self.root = tk.Tk()
       self.root.title("VDIF Streamer")

       # Create main frame
       self.main_frame = tk.Frame(self.root)
       self.main_frame.pack(fill=tk.BOTH, expand=True)

       # Create left frame
       self.left_frame = tk.Frame(self.main_frame)
       self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

       # Create right frame
       self.right_frame = tk.Frame(self.main_frame)
       self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

       # Create file selector button
       self.file_label = tk.Label(self.left_frame, text="Select VDIF file:")
       self.file_label.pack()
       self.file_button = tk.Button(self.left_frame, text="Browse", command=self.select_file)
       self.file_button.pack()
       self.file_path = tk.StringVar()
       self.file_path_label = tk.Label(self.left_frame, textvariable=self.file_path)
       self.file_path_label.pack()

       # Create frame rate entry field
       self.frame_rate_label = tk.Label(self.left_frame, text="Frame rate (frames per second):")
       self.frame_rate_label.pack()
       self.frame_rate_entry = tk.Entry(self.left_frame)
       self.frame_rate_entry.pack()

       # Create destination address entry field
       self.destination_label = tk.Label(self.left_frame, text="Destination address (IP:port):")
       self.destination_label.pack()
       self.destination_entry = tk.Entry(self.left_frame)
       self.destination_entry.insert(0, "127.0.0.1:7100")  # Default destination
       self.destination_entry.pack()

       # Create start and stop buttons
       self.start_button = tk.Button(self.left_frame, text="Start streaming", command=self.start_streaming)
       self.start_button.pack()
       self.stop_button = tk.Button(self.left_frame, text="Stop streaming", command=self.stop_streaming, state=tk.DISABLED)
       self.stop_button.pack()

       # Create status label
       self.status_label = tk.Label(self.left_frame, text="Ready")
       self.status_label.pack()

       # Create text box to display file info
       self.file_info_text = tk.Text(self.right_frame, width=60, height=20)
       self.file_info_text.pack(fill=tk.BOTH, expand=True)

       # Initialize streaming variables
       self.streaming = False
       self.vdif_file = None
       self.socket = None
        
       # Create aux information
       self.vdif_info = None
       self.vdif_threads = None
       self.num_frames = 0
       self.frame_rate = 0
       self.frame_nbytes = 0

    def select_file(self):
        path = filedialog.askopenfilename()
        self.file_path.set(path)
        self.vdif_info = baseband.file_info(self.file_path.get())
        self.vdif_threads = self.vdif_info.file_info()['thread_ids']
        self.num_frames = self.vdif_info.file_info()['number_of_framesets']
        
        # Get bytes per frame as a parameter of interest to show
        tmp_file = vdif.open(self.file_path.get(), 'rb')
        tmp_frame = tmp_file.read_frame()
        tmp_file.close()
        self.frame_nbytes = tmp_frame.nbytes
        
        # Show file info in right box
        self.display_file_info()
        

    def display_file_info(self):
        self.file_info_text.delete('1.0', tk.END)
        self.file_info_text.insert(tk.END, str(self.vdif_info) + '\n\n' + 
                                   'Bytes per Frame: ' + str(self.frame_nbytes))

    def start_streaming(self):
        # self.vdif_file = vdif.open(self.file_path.get(), 'rb')
        print('start_streaming: ' + str(self.file_path.get()))
        self.vdif_file = open(str(self.file_path.get()), 'rb')
        self.frame_rate = float(self.frame_rate_entry.get())
        self.destination = self.destination_entry.get().split(":")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.streaming = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.stream_thread = threading.Thread(target=self.stream_vdif)
        self.stream_thread.start()

    def stop_streaming(self):
        self.vdif_file.close()
        self.streaming = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def stream_vdif(self):
        for fs_ct in range(self.num_frames):
            if not self.streaming:
                break
            for ii in range(len(self.vdif_threads)):
                frame = self.vdif_file.read(self.frame_nbytes)
                self.socket.sendto(frame, (self.destination[0], int(self.destination[1])))
            if fs_ct % self.frame_rate == 0:
                self.status_label.config(text=f"Streaming frame {fs_ct} of {self.num_frames}")
            self.root.update()
            time.sleep(1 / self.frame_rate)
        self.status_label.config(text=f"Finished at frame {fs_ct+1} of {self.num_frames}")
        self.streaming = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = VDIFStreamer()
    app.run()
