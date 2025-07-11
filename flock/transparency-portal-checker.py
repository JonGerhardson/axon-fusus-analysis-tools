import os
import re
import sys
import csv
import requests
import logging
import time  
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import base64
from datetime import datetime

# --- Configuration ---
# Name of your CSV file containing URLs to scrape
CSV_FILENAME = 'urls.csv'
# File to store the last processed row number
PROGRESS_FILENAME = 'progress.txt'
# Name for the log file
LOG_FILENAME = 'scraper.log'
# Base directory where all structured data will be saved
BASE_OUTPUT_DIR = 'scraped_data'
# Seconds to wait between requests to a domain
REQUEST_DELAY = 1  # <--- ADDED: Delay in seconds
# User-Agent to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# Set of 50 US state abbreviations for validation
USA_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
}


# --- Logging Setup ---
def setup_logging():
    """Sets up logging to both a file and the console."""
    # Ensure logs aren't duplicated if this function is called multiple times
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILENAME, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

# --- Helper Functions ---

def sanitize_for_path(name):
    """Removes or replaces characters that are not allowed in file/directory names."""
    name = re.sub(r'[<>:"/\\|?*]+', '_', name)
    name = name.strip()
    if not name:
        name = "untitled"
    return name[:150] # Allow for longer agency names

def extract_state_from_agency(agency_name):
    """
    Finds a valid two-letter US state code from an agency name string.
    """
    # Find all two-letter words bounded by spaces or ends of string
    potential_codes = re.findall(r'\b([A-Z]{2})\b', agency_name.upper())
    for code in potential_codes:
        if code in USA_STATES:
            return code
    return "Uncategorized"

def download_file(url, folder_path, filename=None):
    """Downloads a file from a URL and saves it."""
    try:
        if filename is None:
            filename = unquote(url.split('/')[-1].split('?')[0])
        filename = sanitize_for_path(filename or "downloaded_file")
        file_path = os.path.join(folder_path, filename)

        if os.path.exists(file_path):
            logging.info(f"File already exists: {filename}. Skipping download.")
            return file_path, True
        
        response = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded: {filename}")
        return file_path, True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading {url}: {e}")
        return None, False

def save_data_uri(data_uri, folder_path, preferred_filename):
    """Saves content from a data URI to a file."""
    try:
        filename = sanitize_for_path(preferred_filename)
        file_path = os.path.join(folder_path, filename)

        if os.path.exists(file_path):
            logging.info(f"File already exists: {filename}. Skipping save.")
            return file_path, True

        header, encoded = data_uri.split(',', 1)
        if ';base64' in header:
            data = base64.b64decode(encoded)
            with open(file_path, 'wb') as f: f.write(data)
        else:
            data = unquote(encoded)
            with open(file_path, 'w', encoding='utf-8') as f: f.write(data)
        
        logging.info(f"Saved data URI to: {filename}")
        return file_path, True
    except Exception as e:
        logging.error(f"Error saving data URI {preferred_filename}: {e}")
        return None, False

def get_start_row():
    """Gets the starting row from user input or the progress file."""
    last_processed_row = 0
    if os.path.exists(PROGRESS_FILENAME):
        try:
            with open(PROGRESS_FILENAME, 'r') as f:
                content = f.read().strip()
                if content:
                    last_processed_row = int(content)
        except (ValueError, IOError):
            logging.warning(f"Could not read {PROGRESS_FILENAME}. Starting from the beginning.")
            last_processed_row = 0
    
    resume_row = last_processed_row + 1
    
    try:
        prompt = (f"\nEnter a row number to start from, or press Enter to "
                  f"resume from row {resume_row} (last processed: {last_processed_row}): ")
        user_input = input(prompt)
        if user_input.strip() == "":
            return resume_row
        return int(user_input)
    except ValueError:
        logging.warning("Invalid input. Please enter a number. Resuming automatically.")
        return resume_row
    except (KeyboardInterrupt, EOFError):
        logging.info("\nExiting script.")
        sys.exit(0)

def setup_output_csv(file_path, header):
    """Creates a CSV file and writes the header if it doesn't exist."""
    # Ensure the history directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write header only if the file is new/empty
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

# --- Main Script ---
def main():
    if not os.path.exists(CSV_FILENAME):
        logging.error(f"{CSV_FILENAME} not found. Please create it with '[agency name],[url]' per line.")
        return

    start_row = get_start_row()
    scrape_date = datetime.now().strftime('%Y-%m-%d')
    logging.info(f"Starting scrape for date: {scrape_date}")

    # Setup output CSVs
    history_dir = os.path.join(BASE_OUTPUT_DIR, 'history')
    hits_csv_path = os.path.join(history_dir, f"{scrape_date}-hits.csv")
    four04_csv_path = os.path.join(history_dir, "404.csv")
    
    hits_header = ['agency_name', 'url', 'portal', 'csv', 'pdf', 'other']
    four04_header = ['agency_name', 'url', 'timestamp']

    setup_output_csv(hits_csv_path, hits_header)
    setup_output_csv(four04_csv_path, four04_header)
    
    hits_file = open(hits_csv_path, 'a', newline='', encoding='utf-8')
    hits_writer = csv.writer(hits_file)
    
    four04_file = open(four04_csv_path, 'a', newline='', encoding='utf-8')
    four04_writer = csv.writer(four04_file)

    try:
        with open(CSV_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
            all_rows = list(csv.reader(csvfile))
            total_rows = len(all_rows)

            for row_number, row in enumerate(all_rows, 1):
                if row_number < start_row:
                    continue

                if len(row) < 2:
                    logging.warning(f"Skipping malformed row {row_number}: Not enough columns.")
                    continue
                    
                agency_name, page_url = row[0].strip(), row[1].strip()
                hit_data = {'portal': 0, 'csv': 0, 'pdf': 0, 'other': 0}

                if not page_url.startswith(('http://', 'https://')):
                    logging.warning(f"Skipping invalid URL (line {row_number}): {page_url}")
                    hits_writer.writerow([agency_name, page_url, 0,0,0,0])
                    continue

                logging.info(f"--- Processing URL {row_number}/{total_rows}: {agency_name} ---")

                try:
                    response = requests.get(page_url, headers=HEADERS, timeout=30)
                    response.raise_for_status()
                    hit_data['portal'] = 1

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        logging.warning(f"404 Not Found for {page_url}")
                        four04_writer.writerow([agency_name, page_url, datetime.now().isoformat()])
                    else:
                        logging.error(f"HTTP Error for {page_url}: {e}")
                    hits_writer.writerow([agency_name, page_url, 0,0,0,0])
                    continue
                except requests.exceptions.RequestException as e:
                    logging.error(f"Failed to fetch page {page_url}: {e}")
                    hits_writer.writerow([agency_name, page_url, 0,0,0,0])
                    continue

                # --- Create Directory Structure ---
                state_folder = extract_state_from_agency(agency_name)
                dept_folder = sanitize_for_path(agency_name)
                output_folder_path = os.path.join(BASE_OUTPUT_DIR, state_folder, dept_folder, scrape_date)
                os.makedirs(output_folder_path, exist_ok=True)
                logging.info(f"Saving data to: {output_folder_path}")

                # --- Save HTML and Find Links ---
                soup = BeautifulSoup(response.content, 'lxml')
                html_filepath = os.path.join(output_folder_path, "page_content.html")
                with open(html_filepath, 'wb') as f: f.write(response.content)
                logging.info("Saved main HTML page")

                for a_tag in soup.find_all('a', href=True):
                    link_href = a_tag['href']
                    link_text = a_tag.get_text(strip=True)
                    preferred_filename = a_tag.get('download') or link_text

                    # Check for downloadable files by extension
                    if any(link_href.lower().endswith(ext) for ext in ['.pdf', '.csv', '.zip', '.xlsx']):
                        file_url = urljoin(page_url, link_href)
                        _, downloaded = download_file(file_url, output_folder_path, filename=preferred_filename)
                        if downloaded:
                            if file_url.lower().endswith('.pdf'): hit_data['pdf'] = 1
                            elif file_url.lower().endswith('.csv'): hit_data['csv'] = 1
                            else: hit_data['other'] = 1
                    
                    # Check for data URIs
                    elif link_href.startswith('data:'):
                        _, saved = save_data_uri(link_href, output_folder_path, preferred_filename)
                        if saved:
                                if 'application/pdf' in link_href: hit_data['pdf'] = 1
                                elif 'text/csv' in link_href: hit_data['csv'] = 1
                                else: hit_data['other'] = 1
                
                # Write hit record and save progress
                hits_writer.writerow([agency_name, page_url, hit_data['portal'], hit_data['csv'], hit_data['pdf'], hit_data['other']])
                with open(PROGRESS_FILENAME, 'w') as f:
                    f.write(str(row_number))
                logging.info(f"Successfully processed row {row_number}. Progress saved.")
                
                # --- ADDED: Rate Limiting Delay ---
                logging.info(f"Waiting for {REQUEST_DELAY} second(s) before next request...")
                time.sleep(REQUEST_DELAY)


    except (KeyboardInterrupt, EOFError):
        logging.info("\n\nScript interrupted by user. Run again to resume. Exiting.")
    except Exception as e:
        logging.critical(f"\nAn unexpected error occurred: {e}", exc_info=True)
    finally:
        # Ensure files are closed properly on exit
        if 'hits_file' in locals() and not hits_file.closed:
            hits_file.close()
        if 'four04_file' in locals() and not four04_file.closed:
            four04_file.close()
        logging.info("--- Scraping session ended ---")


if __name__ == '__main__':
    setup_logging()
    main()
