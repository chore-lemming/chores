# Satellite Visibility Calculator

The Satellite Visibility Calculator is a Python application that calculates the visibility of satellites from two different observation sites on Earth. This application uses TLE (Two-Line Element) files to compute satellite positions and determine whether they are visible from the specified sites at a given time.

## Features

- Load TLE files to get satellite data.
- Select observation sites from predefined JSON files.
- Calculate satellite visibility from two observation sites.
- Display results in a tabulated format with relevant details.
- Save results to a text file with a default filename based on the selected sites and time.

## Requirements

- Python 3.x
- Required Python packages:
  - `tkinter`
  - `sgp4`
  - `ephem`
  - `numpy`
  - `tabulate`

You can install the required packages using the following command:

```sh
pip install sgp4 ephem numpy tabulate
```

## Usage

1. Clone the repository and navigate to the project directory:

```sh
git clone https://github.com/chore-lemming/chores.git
cd chores
```

2. Ensure the `sites` directory contains JSON files for the observation sites. Each JSON file should have the following structure:

```json
{
  "name": "Site Name",
  "lat": latitude_value,
  "lon": longitude_value
}
```

Example JSON file for Dallas (`sites/Dallas.json`):

```json
{
  "name": "Dallas",
  "lat": 32.7767,
  "lon": -96.7970
}
```

3. Run the application:

```sh
python tle_app.py
```

4. The application window will open. Follow these steps to use the application:
   - Select Site 1 and Site 2 from the drop-down menus. The latitude and longitude fields will be populated automatically based on the selected sites.
   - Adjust the time if necessary (default is the current UTC time).
   - Click the "Load TLE File" button to load a TLE file. The file name will be displayed next to the button.
   - Click the "Calculate Visibility" button to compute the visibility of satellites from the two selected sites. The results will be displayed in the text area.
   - Click the "Save Results" button to save the results to a text file. The default filename will be based on the selected sites and time.

## Example

1. Select "Dallas" as Site 1 and "New York" as Site 2.
2. Load a TLE file (e.g., `satellites.tle`).
3. Click "Calculate Visibility" to see the results.
4. Click "Save Results" to save the results to a text file (e.g., `Dallas-New_York-20250302T041016.txt`).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please create an issue or submit a pull request for any improvements or bug fixes.

## Contact

For questions or support, please contact [chore-lemming](https://github.com/chore-lemming).