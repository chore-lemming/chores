import tkinter as tk
from tkinter import filedialog, messagebox
from sgp4.earth_gravity import wgs84
from sgp4.io import twoline2rv
import ephem
from datetime import datetime, timedelta
import numpy as np
from tabulate import tabulate
import os
import json

class SatelliteVisibilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Satellite Visibility Calculator")
        self.satellites = []
        self.tle_filename = ""
        
        # Load site locations from JSON files
        self.sites_dir = os.path.join(os.path.dirname(__file__), 'sites')
        self.sites = {}
        site_names = []
        for filename in os.listdir(self.sites_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.sites_dir, filename)
                with open(filepath, 'r') as file:
                    site = json.load(file)
                    self.sites[site['name']] = {"lat": site['lat'], "lon": site['lon']}
                    site_names.append(site['name'])
        
        # Use the first two sites as default selections
        default_site1 = site_names[0] if len(site_names) > 0 else ""
        default_site2 = site_names[1] if len(site_names) > 1 else ""
        
        # Create GUI elements
        tk.Label(root, text="Select Site 1:").grid(row=0, column=0, pady=5)
        tk.Label(root, text="Latitude:").grid(row=1, column=0)
        tk.Label(root, text="Longitude:").grid(row=2, column=0)
        
        tk.Label(root, text="Select Site 2:").grid(row=3, column=0, pady=5)
        tk.Label(root, text="Latitude:").grid(row=4, column=0)
        tk.Label(root, text="Longitude:").grid(row=5, column=0)
        
        tk.Label(root, text="Time (YYYY-MM-DD HH:MM:SS):").grid(row=6, column=0, pady=5)
        
        # Drop-down menus and labels
        self.site1_var = tk.StringVar(value=default_site1)
        self.site2_var = tk.StringVar(value=default_site2)
        self.lat1_var = tk.StringVar(value=str(self.sites[default_site1]["lat"]) if default_site1 else "")
        self.lon1_var = tk.StringVar(value=str(self.sites[default_site1]["lon"]) if default_site1 else "")
        self.lat2_var = tk.StringVar(value=str(self.sites[default_site2]["lat"]) if default_site2 else "")
        self.lon2_var = tk.StringVar(value=str(self.sites[default_site2]["lon"]) if default_site2 else "")
        self.time_var = tk.StringVar(value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        
        tk.OptionMenu(root, self.site1_var, *self.sites.keys(), command=self.update_site1).grid(row=0, column=1)
        self.lat1_label = tk.Label(root, text=self.lat1_var.get())
        self.lat1_label.grid(row=1, column=1)
        self.lon1_label = tk.Label(root, text=self.lon1_var.get())
        self.lon1_label.grid(row=2, column=1)
        
        tk.OptionMenu(root, self.site2_var, *self.sites.keys(), command=self.update_site2).grid(row=3, column=1)
        self.lat2_label = tk.Label(root, text=self.lat2_var.get())
        self.lat2_label.grid(row=4, column=1)
        self.lon2_label = tk.Label(root, text=self.lon2_var.get())
        self.lon2_label.grid(row=5, column=1)
        
        tk.Entry(root, textvariable=self.time_var).grid(row=6, column=1)
        
        # Buttons and TLE file display
        tk.Button(root, text="Load TLE File", command=self.load_tle).grid(row=7, column=0, pady=10)
        self.tle_file_label = tk.Label(root, text="")
        self.tle_file_label.grid(row=7, column=1, pady=10)
        
        # Centered Calculate Visibility button
        tk.Button(root, text="Calculate Visibility", command=self.calculate_visibility).grid(row=8, column=0, columnspan=2, pady=10)
        
        # Results area
        self.results_text = tk.Text(root, height=20, width=160)
        self.results_text.grid(row=9, column=0, columnspan=2, pady=10)
        
        # Save button
        tk.Button(root, text="Save Results", command=self.save_results).grid(row=10, column=0, columnspan=2)
        
    def update_site1(self, selection):
        self.lat1_var.set(self.sites[selection]["lat"])
        self.lon1_var.set(self.sites[selection]["lon"])
        self.lat1_label.config(text=self.lat1_var.get())
        self.lon1_label.config(text=self.lon1_var.get())
    
    def update_site2(self, selection):
        self.lat2_var.set(self.sites[selection]["lat"])
        self.lon2_var.set(self.sites[selection]["lon"])
        self.lat2_label.config(text=self.lat2_var.get())
        self.lon2_label.config(text=self.lon2_var.get())
        
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
                            norad_id = line1.split()[1]
                            satellite = ephem.readtle(name, line1, line2)
                            epoch_year = int("20" + line1[18:20])
                            epoch_day = float(line1[20:32])
                            epoch = datetime(epoch_year, 1, 1) + timedelta(days=epoch_day - 1)
                            self.satellites.append((name, satellite, norad_id, epoch))
                self.tle_filename = filename
                self.tle_file_label.config(text=filename)
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
            for name, sat, norad_id, epoch in self.satellites:
                # Calculate position
                
                # Convert to ephem body
                sat_ephem = sat
                sat_ephem.compute(site1)
                alt1 = float(sat_ephem.alt) * 180/np.pi
                az1 = float(sat_ephem.az) * 180/np.pi
                
                sat_ephem.compute(site2)
                alt2 = float(sat_ephem.alt) * 180/np.pi
                az2 = float(sat_ephem.az) * 180/np.pi
                
                # Calculate days between TLE epoch and generation time
                days_between = (time - epoch).days
                
                # Check if visible from both sites (above horizon)
                if alt1 > 0 and alt2 > 0:
                    results.append([norad_id, name, f"{alt1:.1f}", f"{az1:.1f}", f"{alt2:.1f}", f"{az2:.1f}", days_between])
            
            # Sort results by longitude (Site 1 Azimuth)
            results.sort(key=lambda x: float(x[3]))
            
            self.results_text.delete(1.0, tk.END)
            if results:
                summary = (f"{len(results)} satellites visible from {self.site1_var.get()} "
                           f"({self.lat1_var.get()}, {self.lon1_var.get()}) and {self.site2_var.get()} "
                           f"({self.lat2_var.get()}, {self.lon2_var.get()}) at {self.time_var.get()}\n")
                tle_summary = f"TLE File: {self.tle_filename}\n\n"
                headers = ["NORAD ID", "Satellite", f"{self.site1_var.get()} Elevation", f"{self.site1_var.get()} Azimuth", f"{self.site2_var.get()} Elevation", f"{self.site2_var.get()} Azimuth", "Days Since Epoch"]
                table = tabulate(results, headers=headers, tablefmt="pipe")
                self.results_text.insert(tk.END, summary + tle_summary + table)
            else:
                self.results_text.insert(tk.END, "No satellites visible from both sites")
                
        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")
    
    def save_results(self):
        datetime_str = self.time_var.get().replace(":", "").replace(" ", "T")
        default_filename = f"{self.site1_var.get()}-{self.site2_var.get()}-{datetime_str}.txt"
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                              filetypes=[("Text Files", "*.txt")],
                                              initialfile=default_filename)
        if filename:
            with open(filename, 'w') as file:
                file.write(self.results_text.get(1.0, tk.END))
            messagebox.showinfo("Success", "Results saved successfully")

if __name__ == "__main__":
    root = tk.Tk()
    app = SatelliteVisibilityApp(root)
    root.mainloop()