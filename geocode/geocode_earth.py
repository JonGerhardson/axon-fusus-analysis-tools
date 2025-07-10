import pandas as pd
import requests
import time
import urllib.parse
import os
import re

#This script uses geocode earth API call. You can get a free trial for 1,000 requests per day at https://geocode.earth/ 
# --- Configuration ---
# Replace with your actual Geocode Earth API key
API_KEY = "PASTE YOUR API KEY HERE" 
INPUT_CSV_PATH = "/media/jon/MEDIA/FUXUS/v3/mod/locations.csv"
OUTPUT_CSV_PATH = "/media/jon/MEDIA/FUXUS/v3/mod/locations-geocoded-earth_v1.csv" # New output file name
GEOCODING_URL = "https://api.geocode.earth/v1/autocomplete"
ADDRESS_COLUMN_NAME = "Address" # <--- IMPORTANT: Change this if your address column is named differently!

# --- Best Practices: Set a focus point to improve result relevance and performance ---
# Coordinates for Chicopee, MA. Set to None to disable.
FOCUS_POINT = {
    "lat": 42.1584,
    "lon": -72.6079
}

# --- Address Cleaning Function ---
def clean_address(address):
    """
    Cleans and standardizes address strings for better geocoding results,
    with specific handling for intersections.
    """
    if pd.isna(address) or not str(address).strip():
        return None

    cleaned = str(address).strip()

    # 1. Handle intersection patterns first
    # Looks for "Street & Street" or "Street and Street"
    intersection_match = re.search(
        r"(\b\w+[\w\s]*? (?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Blvd|Boulevard|Pkwy|Parkway|Ct|Court|Pl|Place|Pond|Center))\s*(?:&|and)\s*(\b\w+[\w\s]*? (?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Blvd|Boulevard|Pkwy|Parkway|Ct|Court|Pl|Place|Pond|Center))(?:,\s*(.*))?",
        cleaned,
        re.IGNORECASE
    )

    if intersection_match:
        street1 = intersection_match.group(1).strip()
        street2 = intersection_match.group(2).strip()
        remaining_address = intersection_match.group(3) if intersection_match.group(3) else ''
        cleaned = f"{street1} & {street2}"
        if remaining_address:
            cleaned += f", {remaining_address.strip()}"
        cleaned = re.sub(r"^[Ii]ntersection of\s*", "", cleaned).strip()
    else:
        # 2. If not an intersection, apply general cleaning
        # Remove common descriptive prefixes
        cleaned = re.sub(
            r"^(Main Library|Parking|Access|Spans|near|Pumping Station|Area around Chicopee City Hall|Chicopee Comp\. High|Chicopee Water Pollution Control Facility|Connecticut Riverwalk & Bikeway|River Mills Assisted Living):?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        ).strip()
        # Remove parenthetical notes
        cleaned = re.sub(r"\s*\([^)]*\)\s*", " ", cleaned).strip()

    # 3. Apply general standardization for all cases
    # Standardize street abbreviations
    replacements = {
        r'\bSt\b': 'Street', r'\bAve\b': 'Avenue', r'\bRd\b': 'Road',
        r'\bDr\b': 'Drive', r'\bLn\b': 'Lane', r'\bBlvd\b': 'Boulevard',
        r'\bPkwy\b': 'Parkway', r'\bCt\b': 'Court', r'\bPl\b': 'Place'
    }
    for old, new in replacements.items():
        cleaned = re.sub(old, new, cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace and commas
    cleaned = re.sub(r"\s+", " ", cleaned).strip().strip(',')

    if not cleaned:
        return None
    return cleaned

# --- Geocoding Function (Updated for Geocode Earth) ---
def geocode_address(address, api_key, original_address_for_log, focus_point=None):
    """
    Sends a request to the Geocode Earth Autocomplete API.
    Returns (latitude, longitude) or (None, None) on failure.
    """
    if address is None:
        return None, None

    params = {
        "text": address,
        "api_key": api_key
    }
    # Add focus point to parameters if provided
    if focus_point:
        params['focus.point.lat'] = focus_point['lat']
        params['focus.point.lon'] = focus_point['lon']

    try:
        response = requests.get(GEOCODING_URL, params=params, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()

        # Geocode Earth returns a GeoJSON FeatureCollection
        if data and 'features' in data and len(data['features']) > 0:
            # The first result is the most likely match
            first_feature = data['features'][0]
            # Coordinates are in [longitude, latitude] format
            coordinates = first_feature.get('geometry', {}).get('coordinates')
            if coordinates and len(coordinates) == 2:
                longitude, latitude = coordinates
                return latitude, longitude
            else:
                print(f"DEBUG: No coordinates found in feature for Cleaned: '{address}' (Original: '{original_address_for_log}')")
                return None, None
        else:
            print(f"DEBUG: No geocoding results found for Cleaned: '{address}' (Original: '{original_address_for_log}')")
            return None, None
    except requests.exceptions.HTTPError as http_err:
        print(f"ERROR: HTTP error for Cleaned: '{address}' (Original: '{original_address_for_log}'): {http_err} - Response: {response.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"ERROR: Request failed for Cleaned: '{address}' (Original: '{original_address_for_log}'): {req_err}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred for Cleaned: '{address}' (Original: '{original_address_for_log}'): {e}")
    
    return None, None


# --- Main Script ---
def main():
    print(f"Starting geocoding with Geocode Earth Autocomplete API: {INPUT_CSV_PATH}")
    print(f"Output will be saved to: {OUTPUT_CSV_PATH}")

    if not os.path.exists(INPUT_CSV_PATH):
        print(f"Error: Input CSV file not found at '{INPUT_CSV_PATH}'")
        return

    try:
        df = pd.read_csv(INPUT_CSV_PATH)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    if ADDRESS_COLUMN_NAME not in df.columns:
        print(f"Error: Address column '{ADDRESS_COLUMN_NAME}' not found in the CSV.")
        print(f"Available columns are: {df.columns.tolist()}")
        print("Please update 'ADDRESS_COLUMN_NAME' in the script.")
        return

    # Initialize new columns
    df['Cleaned_Address'] = None
    df['Latitude'] = None
    df['Longitude'] = None
    df['Geocoding_Status'] = 'Pending'

    total_addresses = len(df)
    print(f"Found {total_addresses} addresses to process.")

    for index, row in df.iterrows():
        original_address = row[ADDRESS_COLUMN_NAME]
        
        cleaned_address = clean_address(original_address)
        df.at[index, 'Cleaned_Address'] = cleaned_address

        lat, lon = None, None
        if cleaned_address:
            # Pass original address for logging and the focus point for better results
            lat, lon = geocode_address(cleaned_address, API_KEY, original_address, FOCUS_POINT)
            df.at[index, 'Geocoding_Status'] = 'Success' if lat is not None else 'Failed'
        else:
            df.at[index, 'Geocoding_Status'] = 'Skipped (Empty/Uncleanable)'

        df.at[index, 'Latitude'] = lat
        df.at[index, 'Longitude'] = lon

        print(
            f"Processed {index + 1}/{total_addresses}: "
            f"Original: '{original_address}' -> Cleaned: '{cleaned_address}' -> "
            f"Lat: {lat}, Lon: {lon}"
        )

        # Adhere to a safe rate limit
        time.sleep(1)

    # Save the results to a new CSV file
    try:
        df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8')
        print(f"\nGeocoding complete! Results saved to '{OUTPUT_CSV_PATH}'")
    except Exception as e:
        print(f"Error saving output CSV: {e}")

if __name__ == "__main__":
    main()
