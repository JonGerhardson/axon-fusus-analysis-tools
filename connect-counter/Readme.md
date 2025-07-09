Axon Fusus Community Camera Scraper

This Python script scrapes public camera statistics (Registered and Integrated) from a list of Axon Fusus community program landing pages, such as [Connect Chicopee](https://connectchicopee.org) or [NYC Connect](https://newyorkcityconnect.org/), among others, and saves the results to a csv file.  
![Screenshot from 2025-07-09 16-03-29](https://github.com/user-attachments/assets/f443f938-f6a2-431a-ab33-9f1c4ae2f76e)

It is designed to be run automatically on a schedule (e.g., using a cron job) to log the camera counts over time from multiple sources into a single file.
Features

    Processes a list of URLs in a single run.

    Navigates to each specified community landing page.

    Waits for dynamic content and "count-up" animations to finish for accurate data capture.

    Scrapes the number of "Registered Cameras" and "Integrated Cameras."

    Appends the results for each site as a new row to a single camlogs.csv file.

    Logs errors to the CSV if scraping fails for a specific site.

Requirements

    Python 3

    Playwright library:

    pip install playwright

    Playwright browser binaries (installs the necessary headless browsers):

    python -m playwright install

Usage

    Configure the Script: Open the Python script and add all the target URLs to the URLS_TO_SCRAPE list at the top of the file.

    # e.g., for multiple cities
    URLS_TO_SCRAPE = [
        'https://connectchicopee.org/',
        'https://newyorkcityconnect.org/',
        'https://connectberkshires.org/'
    ]

    Run Manually: You can execute the script directly from your terminal to perform a single scrape of all URLs in the list:

    python3 camcount.py

    Check the Output: After running, a camlogs.csv file will be created or updated in the same directory. Each run will add multiple rows—one for each URL in your list.

Timestamp
	

URL
	

Registered Cameras
	

Integrated Cameras

2023-10-27 12:00:01
	

https://connectchicopee.org/
	

56
	

476

2023-10-27 12:00:15
	

https://newyorkcityconnect.org/
	

1234
	

5678
Automation with Cron

This script is ideal for automation. You can set up a cron job to run it on a regular schedule (e.g., every 12 hours). The same cron command will now trigger a run for all the URLs in your list.
