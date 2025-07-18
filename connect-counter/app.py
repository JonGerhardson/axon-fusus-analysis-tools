
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import datetime
import csv
import os
import threading
from playwright.sync_api import sync_playwright

# --- Your Original Scraping and Logging Logic (with minor adjustments for GUI) ---

def get_camera_stats(url, update_callback):
    """
    Launches a headless browser to scrape camera stats from a given URL.
    Includes a delay to allow for page animations to complete.
    Now includes a callback to update the GUI.
    """
    try:
        with sync_playwright() as p:
            update_callback(f"  -> Launching browser for {url}...")
            browser = p.chromium.launch()
            page = browser.new_page()
            
            update_callback("  -> Navigating to page...")
            page.goto(url, timeout=60000)

            update_callback("  -> Page loaded. Waiting for elements...")
            page.wait_for_selector('p:text("Registered Cameras")', timeout=30000)

            update_callback("  -> Elements found. Waiting 5 seconds for animations...")
            page.wait_for_timeout(5000)

            update_callback("  -> Scraping data...")
            registered_text_element = page.locator('p:text("Registered Cameras")')
            registered_cameras = registered_text_element.locator('xpath=preceding-sibling::p[1]').inner_text()

            integrated_text_element = page.locator('p:text("Integrated Cameras")')
            integrated_cameras = integrated_text_element.locator('xpath=preceding-sibling::p[1]').inner_text()

            browser.close()
            update_callback("  -> Browser closed.")
            return registered_cameras, integrated_cameras

    except Exception as e:
        # Ensure browser is closed on error
        if 'browser' in locals() and browser.is_connected():
            browser.close()
        update_callback(f"  -> An error occurred: {e}")
        return None, None

def write_log_to_csv(filepath, data_to_log):
    """Writes the collected data to a user-specified CSV file."""
    if not data_to_log:
        return

    try:
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['Timestamp', 'URL', 'Registered Cameras', 'Integrated Cameras']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_to_log)
        return True
    except IOError as e:
        print(f"Error writing to CSV: {e}")
        return False

# --- Tkinter GUI Application Class ---

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper Application")
        self.root.geometry("700x600")

        self.results_data = []
        
        # --- GUI Widgets ---
        
        # URL Input Frame
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=False)

        tk.Label(frame, text="Enter URLs (one per line):", font=("Helvetica", 12)).pack(anchor=tk.W)
        self.url_text = scrolledtext.ScrolledText(frame, height=10, width=80, wrap=tk.WORD)
        self.url_text.pack(fill=tk.BOTH, expand=True)
        self.url_text.insert(tk.END, "https://connectchicopee.org/\nhttps://connectspringfield.org/\nhttps://connectholyoke.org/")

        # Control Buttons Frame
        button_frame = tk.Frame(root, pady=5)
        button_frame.pack(fill=tk.X, padx=10)

        self.start_button = tk.Button(button_frame, text="Start Scraping", command=self.start_scraping_thread, font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white")
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.save_button = tk.Button(button_frame, text="Save Log as CSV", command=self.save_log, font=("Helvetica", 12), state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Log Output Frame
        log_frame = tk.Frame(root, padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="Log:", font=("Helvetica", 12)).pack(anchor=tk.W)
        self.log_widget = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED, wrap=tk.WORD, bg="#f0f0f0")
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        """Thread-safe method to append messages to the log widget."""
        def append_message():
            self.log_widget.config(state=tk.NORMAL)
            self.log_widget.insert(tk.END, message + "\n")
            self.log_widget.config(state=tk.DISABLED)
            self.log_widget.see(tk.END) # Auto-scroll
        # Schedule the GUI update to run in the main thread
        self.root.after(0, append_message)

    def start_scraping_thread(self):
        """Starts the scraping process in a separate thread to avoid freezing the GUI."""
        urls = self.url_text.get("1.0", tk.END).strip().split('\n')
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            messagebox.showerror("Error", "Please enter at least one URL.")
            return
            
        # Disable button and reset state
        self.start_button.config(state=tk.DISABLED, text="Scraping...")
        self.save_button.config(state=tk.DISABLED)
        self.results_data = []

        # Run the main scraping logic in a new thread
        thread = threading.Thread(target=self.run_scraping_logic, args=(urls,))
        thread.daemon = True # Allows main window to close even if thread is running
        thread.start()

    def run_scraping_logic(self, urls):
        """The main logic that loops through URLs and calls the scraper."""
        self.log("--- Starting scraping process ---")
        
        for url in urls:
            self.log(f"\n[BEGIN] Processing: {url}")
            
            registered_count, integrated_count = get_camera_stats(url, self.log)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if registered_count is not None and integrated_count is not None:
                self.log(f"[SUCCESS] Logged for {url}: Registered={registered_count}, Integrated={integrated_count}")
                self.results_data.append({
                    'Timestamp': now,
                    'URL': url,
                    'Registered Cameras': registered_count,
                    'Integrated Cameras': integrated_count
                })
            else:
                self.log(f"[ERROR] Failed to retrieve stats for {url}. Logged error.")
                self.results_data.append({
                    'Timestamp': now,
                    'URL': url,
                    'Registered Cameras': 'Error',
                    'Integrated Cameras': 'Error'
                })

        self.log("\n--- Scraping finished ---")
        # Re-enable buttons once done (must be done via root.after)
        self.root.after(0, self.scraping_complete)

    def scraping_complete(self):
        """Resets the UI after scraping is done."""
        self.start_button.config(state=tk.NORMAL, text="Start Scraping")
        if self.results_data:
            self.save_button.config(state=tk.NORMAL)
        messagebox.showinfo("Complete", "Scraping process has finished.")

    def save_log(self):
        """Opens a file dialog to save the collected data as a CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Log File"
        )
        if not filepath:
            return # User cancelled
        
        if write_log_to_csv(filepath, self.results_data):
            messagebox.showinfo("Success", f"Log successfully saved to {filepath}")
        else:
            messagebox.showerror("Error", f"Failed to save log file to {filepath}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
  
