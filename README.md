# Chores Repository

Welcome to the Chores Repository! This repository contains two distinct web applications: a Satellite Visibility Calculator and a Markdown Viewer Application. Each application is designed to serve specific purposes and is built using Python.

## Table of Contents

- [Satellite Visibility Calculator](#satellite-visibility-calculator)
- [Markdown Viewer Application](#markdown-viewer-application)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Satellite Visibility Calculator

The Satellite Visibility Calculator is a Python application that calculates the visibility of satellites from two different observation sites on Earth. This application uses TLE (Two-Line Element) files to compute satellite positions and determine whether they are visible from the specified sites at a given time.

### Features

- Load TLE files to get satellite data.
- Select observation sites from predefined JSON files.
- Calculate satellite visibility from two observation sites.
- Display results in a tabulated format with relevant details.
- Save results to a text file with a default filename based on the selected sites and time.

### Requirements

- Python 3.x
- Required Python packages:
  - `tkinter`
  - `sgp4`
  - `ephem`
  - `numpy`
  - `tabulate`

### Usage

Refer to the [Satellite Visibility Calculator README](web-tle/README.md) for detailed usage instructions.

---

## Markdown Viewer Application

This is a simple Python web application that hosts a Markdown document, renders it as HTML, and displays the last updated date. Users can print the rendered document using their system's print dialog.

### Features

- Renders Markdown content as HTML.
- Displays the last modified date of the Markdown file in the header and footer.
- Allows users to print the rendered document using the system print dialog.
- Refreshing the server will reload the latest version of the markdown document.

### Prerequisites

- Python 3.x
- Flask library

### Usage

Refer to the [Markdown Viewer Application README](markdown_viewer/README.md) for detailed usage instructions.

---

## Installation

To set up the applications, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/chore-lemming/chores.git
   cd chores

### Usage

Refer to the [Markdown Viewer Application README](markdown_viewer/README.md) for detailed usage instructions.

---

## Installation

To set up the applications, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/chore-lemming/chores.git
   cd chores
   ```

2. Install the required Python packages for each application:

   For the Satellite Visibility Calculator:

   ```bash
   cd web-tle
   pip install sgp4 ephem numpy tabulate
   ```

   For the Markdown Viewer Application:

   ```bash
   cd ../markdown_viewer
   pip install Flask markdown
   ```

---

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or support, please contact [chore-lemming](https://github.com/chore-lemming).
