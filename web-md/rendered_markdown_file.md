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

## Sample Table

Here is a sample table to test the no-break feature when printing:

| ID  | Name         | Age | Occupation       |
|-----|--------------|-----|------------------|
| 1   | Alice        | 30  | Software Engineer |
| 2   | Bob          | 25  | Designer         |
| 3   | Charlie      | 35  | Product Manager   |
| 4   | David        | 28  | Data Analyst      |
| 5   | Eva          | 22  | Marketing Specialist |
| 6   | Frank        | 40  | Sales Executive   |
| 7   | Grace        | 29  | UX Researcher     |
| 8   | Henry        | 33  | DevOps Engineer   |
| 9   | Ivy          | 27  | QA Tester        |
| 10  | Jack         | 31  | System Administrator |


## Installation

1. Clone this repository or download the files.

2. Navigate to the project directory.

3. Install the required Python packages:

   ```bash
   pip install Flask markdown
    ```