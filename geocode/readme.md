Geocoding Script Quick Start Guide

This Python script is designed to geocode a list of addresses from a CSV file using the Geocode Earth Autocomplete API. It reads addresses, cleans them, sends them to the API, and then writes the geocoded latitude and longitude back to a new CSV file.
Quick Start


Get API Key: Obtain a free API key from https://geocode.earth/.

Prepare CSV: Create a CSV file (e.g., locations.csv) with a header row and an "Address" column containing the addresses you want to geocode.

Example locations.csv:

    
    ID,Address,OtherData
    1,123 Main Street,Some info here
    2,Intersection of Elm and Oak,More data
    

  Configure Script: Open the Python script and edit the --- Configuration --- section:

        Replace "PASTE YOUR API KEY HERE" with your actual API key.

        Update INPUT_CSV_PATH to your input file's location.

        Update OUTPUT_CSV_PATH for your desired output file.

        Important: If your address column is not named "Address", change ADDRESS_COLUMN_NAME to match it.

        (Optional) Set FOCUS_POINT for better accuracy in a specific area by uncommenting and providing latitude/longitude.

  Install Libraries: If you haven't already, install pandas and requests:

  ```
pip install pandas requests
```
  Run Script: Execute the script from your terminal:

  ```
 python geocode_earth.py
```

  Check Output: A new CSV file will be created at OUTPUT_CSV_PATH with Latitude, Longitude, Cleaned_Address, and Geocoding_Status columns added.
