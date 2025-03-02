import tkinter as tk
from tkinter import filedialog, messagebox
from sgp4.earth_gravity import wgs84
from sgp4.io import twoline2rv
import ephem
from datetime import datetime
import numpy as np

class SatelliteVisibilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Satellite Visibility Calculator")
        self.satellites = []
        
        # Create GUI elements
        tk.Label(root, text="Site 1:").grid(row=0, column=0, pady=5)
        tk.Label(root, text="Latitude:").grid(row=1, column=0)
        tk.Label(root, text="Longitude:").grid(row=2, column=0)
        
        tk.Label(root, text="Site 2:").grid(row=3, column=0, pady=5)
        tk.Label(root, text="Latitude:").grid(row=4, column=0)
        tk.Label(root, text="Longitude:").grid(row=5, column=0)
        
        tk.Label(root, text="Time (YYYY-MM-DD HH:MM:SS):").grid(row=6, column=0, pady=5)
        
        # Entry fields
        self.lat1_var = tk.StringVar(value="0.0")
        self.lon1_var = tk.StringVar(value="0.0")
        self.lat2_var = tk.StringVar(value="0.0")
        self.lon2_var = tk.StringVar(value="0.0")
        self.time_var = tk.StringVar(value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        
        tk.Entry(root, textvariable=self.lat1_var).grid(row=1, column=1)
        tk.Entry(root, textvariable=self.lon1_var).grid(row=2, column=1)
        tk.Entry(root, textvariable=self.lat2_var).grid(row=4, column=1)
        tk.Entry(root, textvariable=self.lon2_var).grid(row=5, column=1)
        tk.Entry(root, textvariable=self.time_var).grid(row=6, column=1)
        
        # Buttons
        tk.Button(root, text="Load TLE File", command=self.load_tle).grid(row=7, column=0, pady=10)
        tk.Button(root, text="Calculate Visibility", command=self.calculate_visibility).grid(row=7, column=1, pady=10)
        
        # Results area
        self.results_text = tk.Text(root, height=20, width=60)
        self.results_text.grid(row=8, column=0, columnspan=2, pady=10)
        
        # Save button
        tk.Button(root, text="Save Results", command=self.save_results).grid(row=9, column=0, columnspan=2)
        
    def load_tle(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if filename:
            try:
                self.satellites = []
                with open(filename, 'r') as file:
                    lines = file.readlines()
                    for i in range(0, len(lines), 3):
                        if i+2 < len(lines):
                            name = lines[i].strip()
                            line1 = lines[i+1].strip()
                            line2 = lines[i+2].strip()
                            satellite = ephem.readtle(name, line1, line2)
                            self.satellites.append((name, satellite))
                messagebox.showinfo("Success", f"Loaded {len(self.satellites)} satellites")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading TLE file: {str(e)}")
    
    def calculate_visibility(self):
        if not self.satellites:
            messagebox.showerror("Error", "Please load TLE file first")
            return
            
        try:
            # Create observer locations
            site1 = ephem.Observer()
            site1.lat = str(float(self.lat1_var.get()))
            site1.lon = str(float(self.lon1_var.get()))
            site1.elevation = 0
            
            site2 = ephem.Observer()
            site2.lat = str(float(self.lat2_var.get()))
            site2.lon = str(float(self.lon2_var.get()))
            site2.elevation = 0
            
            # Set time
            time = datetime.strptime(self.time_var.get(), "%Y-%m-%d %H:%M:%S")
            site1.date = time
            site2.date = time
            
            results = []
            for name, sat in self.satellites:
                # Calculate position
                
                # Convert to ephem body
                sat_ephem = sat
                sat_ephem.compute(site1)
                alt1 = float(sat_ephem.alt) * 180/np.pi
                az1 = float(sat_ephem.az) * 180/np.pi
                
                sat_ephem.compute(site2)
                alt2 = float(sat_ephem.alt) * 180/np.pi
                az2 = float(sat_ephem.az) * 180/np.pi
                
                # Check if visible from both sites (above horizon)
                if alt1 > 0 and alt2 > 0:
                    results.append(f"Satellite: {name}\n"
                                 f"Site 1 - Altitude: {alt1:.1f}°, Azimuth: {az1:.1f}°\n"
                                 f"Site 2 - Altitude: {alt2:.1f}°, Azimuth: {az2:.1f}°\n")
            
            self.results_text.delete(1.0, tk.END)
            if results:
                self.results_text.insert(tk.END, "Visible Satellites:\n\n" + "".join(results))
            else:
                self.results_text.insert(tk.END, "No satellites visible from both sites")
                
        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")
    
    def save_results(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                              filetypes=[("Text Files", "*.txt")])
        if filename:
            with open(filename, 'w') as file:
                file.write(self.results_text.get(1.0, tk.END))
            messagebox.showinfo("Success", "Results saved successfully")

if __name__ == "__main__":
    root = tk.Tk()
    app = SatelliteVisibilityApp(root)
    root.mainloop()