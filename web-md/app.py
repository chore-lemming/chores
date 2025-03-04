from flask import Flask, render_template, abort
import markdown
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

app = Flask(__name__)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging with daily rotation
log_filename = f'logs/app_{datetime.now().strftime("%Y-%m-%d")}.log'
handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=7)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Set up the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Path to your markdown file
MARKDOWN_FILE = 'rendered_markdown_file.md'
logger.info(f"Markdown file is: {MARKDOWN_FILE}")

@app.route('/')
def index():
    try:
        # Read the markdown file
        logger.info(f"Markdown file is: {MARKDOWN_FILE}")
        if not os.path.exists(MARKDOWN_FILE):
            logging.error(f"Markdown file not found: {MARKDOWN_FILE}")
            abort(404)  # Return a 404 error if the file does not exist

        with open(MARKDOWN_FILE, 'r') as f:
            content = f.read()

        # Convert markdown to HTML
        html_content = markdown.markdown(content)

        # Get the last modified time of the markdown file
        last_modified_time = os.path.getmtime(MARKDOWN_FILE)
        last_modified_date = datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')

        return render_template('index.html', content=html_content, last_modified_date=last_modified_date)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        abort(500)  # Return a 500 error for any other exceptions

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=6100)
    #app.run(host='0.0.0.0', port=6000)
