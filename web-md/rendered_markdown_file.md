# Markdown Viewer Application

This is a simple Python web application that hosts a Markdown document, renders it as HTML, and displays the last updated date. Users can print the rendered document using their system's print dialog.

## Features

- Renders Markdown content as HTML.
- Displays the last modified date of the Markdown file in the header and footer.
- Allows users to print the rendered document.
    - Uses the system print dialog
- Refreshing the server will reload the latest version of the markdown document.
    - Of course, the last modified date will then update too.

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.x
- Flask library

## Installation

1. Clone this repository or download the files.

2. Navigate to the project directory.

3. Install the required Python packages:

   ```bash
   pip install Flask markdown
