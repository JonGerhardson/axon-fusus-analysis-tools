import datetime
import csv
import os
from playwright.sync_api import sync_playwright

# --- Best Practice for Cron ---
# Change the working directory to the script's directory
# This ensures that relative paths (if any) work as expected.
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# --- Configuration ---
# Add all the URLs you want to scrape to this list
URLS_TO_SCRAPE = [
    'https://connectchicopee.org/',
    'https://newyorkcityconnect.org/',
    # Add more Axon Fusus community URLs here
]

# --- CRON JOB FIX ---
# Use an absolute path for the log file to ensure cron finds it.
# The script determines its own directory, so this is now robust.
LOG_FILE = os.path.join(script_dir, 'camlogs.csv')


def get_camera_stats(url):
    """
    Launches a headless browser to scrape camera stats from a given URL.
    Includes a delay to allow for page animations to complete.
    """
    # Use a new Playwright context for each URL to ensure isolation
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            print(f"Scraping {url}...")
            # Go to the target URL
            page.goto(url, timeout=60000)

            # Wait for a key element to ensure the page is loaded
            page.wait_for_selector('p:text("Registered Cameras")', timeout=30000)

            # Wait for 5 seconds to allow "count-up" animations to finish
            page.wait_for_timeout(5000)

            # Scrape the data
            registered_text_element = page.locator('p:text("Registered Cameras")')
            registered_cameras = registered_text_element.locator('xpath=preceding-sibling::p[1]').inner_text()

            integrated_text_element = page.locator('p:text("Integrated Cameras")')
            integrated_cameras = integrated_text_element.locator('xpath=preceding-sibling::p[1]').inner_text()

            browser.close()
            return registered_cameras, integrated_cameras

        except Exception as e:
            browser.close()
            # Log the error to the console
            print(f"An error occurred while scraping {url}: {e}")
            return None, None

def log_to_csv(timestamp, url, registered, integrated):
    """Appends a new row to the CSV log file."""
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, 'a', newline='') as csvfile:
        fieldnames = ['Timestamp', 'URL', 'Registered Cameras', 'Integrated Cameras']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'Timestamp': timestamp,
            'URL': url,
            'Registered Cameras': registered,
            'Integrated Cameras': integrated
        })

if __name__ == "__main__":
    print("Starting camera stats scraper for multiple URLs...")
    # Loop through each URL in the list
    for target_url in URLS_TO_SCRAPE:
        # Get the stats for the current URL
        registered_count, integrated_count = get_camera_stats(target_url)
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if registered_count and integrated_count:
            # Log the successful data retrieval
            log_to_csv(now, target_url, registered_count, integrated_count)
            print(f"-> Successfully logged data for {target_url}")
        else:
            # Log the failure
            log_to_csv(now, target_url, 'Error', 'Error')
            print(f"-> Failed to log data for {target_url}. Logged error to CSV.")
    
    print("Scraping run finished.")
