import datetime
import csv
import os
from playwright.sync_api import sync_playwright

# Define the target URL and log file path
URL = 'https://newyorkcityconnect.org/'
LOG_FILE = 'connect-counter.csv'
# Assuming the script is in /home/jon/Documents/connectchicopeechron/
# You might want to use an absolute path for the log file in a cron job
# e.g., LOG_FILE = '/home/jon/Documents/connectchicopeechron/camlogs.csv'


def get_camera_stats():
    """
    Launches a headless browser to scrape camera stats from Connect Chicopee.
    Includes a delay to allow for page animations to complete.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            # Go to the target URL
            page.goto(URL, timeout=60000)

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
            # Log the error to the console (which can be seen in cron logs if configured)
            print(f"An error occurred during scraping: {e}")
            return None, None

def log_to_csv(timestamp, url, registered, integrated):
    """Appends a new row to the CSV log file."""
    # Check if the file exists to determine if we need to write a header
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, 'a', newline='') as csvfile:
        fieldnames = ['Timestamp', 'URL', 'Registered Cameras', 'Integrated Cameras']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header only if the file is new
        if not file_exists:
            writer.writeheader()
        
        # Write the data row
        writer.writerow({
            'Timestamp': timestamp,
            'URL': url,
            'Registered Cameras': registered,
            'Integrated Cameras': integrated
        })

if __name__ == "__main__":
    # Get the stats
    registered_count, integrated_count = get_camera_stats()
    
    # Get the current timestamp
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if registered_count and integrated_count:
        # Log the successful data retrieval
        log_to_csv(now, URL, registered_count, integrated_count)
        print(f"{now} - Successfully logged: Registered={registered_count}, Integrated={integrated_count}")
    else:
        # Log the failure
        log_to_csv(now, URL, 'Error', 'Error')
        print(f"{now} - Error: Failed to retrieve camera statistics. Logged error to CSV.")


