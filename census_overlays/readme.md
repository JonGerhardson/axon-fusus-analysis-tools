Prerequisites

    Python 3: Ensure you have Python 3 installed on your system.

    pip: Python's package installer, which usually comes with Python.

    Required Data Files: Make sure the following files are all in the same directory:

        ACSDP5Y2023.DP03-Data.csv

        ACSDP5Y2023.DP05-Data.csv

        deduplicated_logs.csv

        data.geojson

        The tl_2024_25_tract folder containing the census shapefiles.

Step 1: Install Necessary Libraries

Before running the scripts, you need to install the required Python libraries. Open your terminal or command prompt and run the following command:

pip install pandas geopandas matplotlib seaborn

Step 2: Running the Scripts

The scripts must be run in a specific order, as each one generates a file that the next one depends on.
Script 1: Join the Census Data

This script merges the economic (DP03) and demographic (DP05) data tables into a single file.

    Script Name: join_script.py

    Command:

    python join_script.py

    Output: This will create the file ACSDP_DP03_DP05_Joined.csv.

Script 2: Create the Geospatial Data for the Map

This script performs the spatial join, linking camera locations to census tracts and adding income and population data.

    Script Name: create_map_data.py

    Command:

    python create_map_data.py

    Output: This creates camera_income_analysis.geojson, which is the primary data source for the map and the final analysis.

Script 3: Perform the Statistical Analysis

This script reads the final GeoJSON file, calculates correlations, and generates plots.

    Script Name: perform_analysis.py

    Command:

    python perform_analysis.py

    Output:

        Prints a statistical summary to your terminal.

        Creates an analysis_results folder.

        Saves the following plots inside the analysis_results folder:

            income_vs_cameras_hexbin.png

            poverty_vs_cameras.png

            camera_density_by_income_bracket.png

Step 4: View the Interactive Map

After running the first two scripts, you can view the final map by opening the HTML file in any web browser.

    File Name: camera_map.html

    Action: Double-click the file or use your browser's "Open File" option.
