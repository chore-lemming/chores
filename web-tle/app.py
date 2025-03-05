from flask import Flask, render_template, request, send_file
import ephem
from datetime import datetime, timedelta
import numpy as np
from tabulate import tabulate
import os
import json
import io
import requests
import logging
from logging.handlers import TimedRotatingFileHandler


app = Flask(__name__)


# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging with daily rotation
log_filename = f'logs/app_{datetime.now().strftime("%Y-%m-%d")}.log'
handler = TimedRotatingFileHandler(log_filename, when='midnight', interval=1)
handler.suffix = "%Y-%m-%d"
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Set up the root logger
logger = logging.getLogger('SatelliteVisibilityCalculator')
logger.setLevel(logging.INFO)
logger.addHandler(handler)



# Load site locations from JSON files
sites_dir = os.path.join(os.path.dirname(__file__),'..', 'sites')
sites = {}
site_names = []
for filename in os.listdir(sites_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(sites_dir, filename)
        with open(filepath, 'r') as file:
            site = json.load(file)
            sites[site['name']] = {"lat": site['lat'], "lon": site['lon']}
            site_names.append(site['name'])

@app.route('/')
def index():
    return render_template('index.html', sites=site_names, datetime=datetime)

@app.route('/calculate', methods=['POST'])
def calculate():
    site1 = request.form['site1']
    site2 = request.form['site2']
    time_str = request.form['time']
    tle_url = request.form['tle_url']
    
    if not tle_url:
        return "No TLE URL provided", 400

    response = requests.get(tle_url)
    if response.status_code != 200:
        return f"Failed to download TLE file: {response.status_code}", 400

    satellites = []
    lines = response.text.splitlines()
    for i in range(0, len(lines), 3):
        if i + 2 < len(lines):
            name = lines[i].strip()
            line1 = lines[i + 1].strip()
            line2 = lines[i + 2].strip()
            norad_id = line1.split()[1]
            satellite = ephem.readtle(name, line1, line2)
            epoch_year = int("20" + line1[18:20])
            epoch_day = float(line1[20:32])
            epoch = datetime(epoch_year, 1, 1) + timedelta(days=epoch_day - 1)
            satellites.append((name, satellite, norad_id, epoch))

    # Create observer locations
    site1_obs = ephem.Observer()
    site1_obs.lat = str(sites[site1]["lat"])
    site1_obs.lon = str(sites[site1]["lon"])
    site1_obs.elevation = 0

    site2_obs = ephem.Observer()
    site2_obs.lat = str(sites[site2]["lat"])
    site2_obs.lon = str(sites[site2]["lon"])
    site2_obs.elevation = 0

    # Set time
    time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    site1_obs.date = time
    site2_obs.date = time

    results = []
    for name, sat, norad_id, epoch in satellites:
        # Calculate position
        sat.compute(site1_obs)
        alt1 = float(sat.alt) * 180 / np.pi
        az1 = float(sat.az) * 180 / np.pi

        sat.compute(site2_obs)
        alt2 = float(sat.alt) * 180 / np.pi
        az2 = float(sat.az) * 180 / np.pi

        # Calculate days between TLE epoch and generation time
        days_between = (time - epoch).days

        # Check if visible from both sites (above horizon)
        if alt1 > 0 and alt2 > 0:
            results.append([norad_id, name, f"{alt1:.1f}", f"{az1:.1f}", f"{alt2:.1f}", f"{az2:.1f}", days_between])

    # Sort results by longitude (Site 1 Azimuth)
    results.sort(key=lambda x: float(x[3]))

    summary = (f"{len(results)} satellites visible from {site1} "
               f"({sites[site1]['lat']}, {sites[site1]['lon']}) and {site2} "
               f"({sites[site2]['lat']}, {sites[site2]['lon']}) at {time_str}\n")
    headers = ["NORAD ID", "Satellite", f"{site1} Elevation", f"{site1} Azimuth", f"{site2} Elevation", f"{site2} Azimuth", "Days Since Epoch"]
    table = tabulate(results, headers=headers, tablefmt="pipe")

    output = summary + table
    
    # Log the calculation
    logger.info(f"Visibility calculated for sites {site1} and {site2} at {time_str}")
    
    
    return render_template('index.html', sites=site_names, output=output, datetime=datetime)

@app.route('/download', methods=['POST'])
def download():
    output = request.form['output']
    site1 = request.form['site1']
    site2 = request.form['site2']
    time_str = request.form['time']

    datetime_str = time_str.replace(":", "").replace(" ", "T")
    filename = f"{site1}-{site2}-{datetime_str}.txt"

    return send_file(
        io.BytesIO(output.encode('utf-8')),
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain'
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6101)
    #app.run(debug=True)
