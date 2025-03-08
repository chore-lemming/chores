import tkinter as tk
import socket
import threading

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

    def start_receiving(self):
        port = int(self.port_entry.get())
        output_file = self.file_entry.get()

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

    def receive_data(self, output_file):
        with open(output_file, 'wb') as f:
            self.status_label.config(text=f"Receiving data to {output_file}...")
            while self.receiving:
                try:
                    data, addr = self.socket.recvfrom(4096)  # Buffer size is 4096 bytes
                    if data:
                        f.write(data)
                        print(f"Received {len(data)} bytes from {addr}")
                except Exception as e:
                    if not self.receiving:  # If we are stopping, ignore exceptions
                        break
                    print(f"Error receiving data: {e}")

        self.status_label.config(text="Data written to " + output_file)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    receiver = VDIFReceiver()
    receiver.run()
