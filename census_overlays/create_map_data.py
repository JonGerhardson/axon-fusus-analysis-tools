import pandas as pd
import geopandas as gpd
import json
import os

def analyze_camera_distribution(census_data_path, camera_csv_path, tracts_shapefile_path, output_geojson_path):
    """
    Performs a spatial analysis to overlay camera locations on census tracts
    and correlate them with income data. This version uses a CSV file for camera
    locations for a more accurate count.

    Args:
        census_data_path (str): Path to the joined census data CSV.
        camera_csv_path (str): Path to the CSV file containing camera locations.
        tracts_shapefile_path (str): Path to the census tracts shapefile (.shp).
        output_geojson_path (str): Path to save the final GeoJSON for mapping.
    """
    try:
        # --- 1. Load and Prepare Census Data ---
        print(f"Loading joined census data from: {census_data_path}")
        census_df = pd.read_csv(census_data_path, dtype={'GEO_ID': str})
        
        # The GEOID from data.census.gov has a prefix '1400000US'. We need to strip
        # this to match the 'GEOID' format in the shapefile (just the 11-digit code).
        census_df['GEOID'] = census_df['GEO_ID'].apply(lambda x: x.split('US')[-1])
        
        # Select and rename key income columns for clarity
        # DP03_0062E: Median household income
        income_df = census_df[['GEOID', 'NAME', 'DP03_0062E']].copy()
        income_df.rename(columns={
            'GEOID': 'GEOID',
            'NAME': 'TractName',
            'DP03_0062E': 'MedianHouseholdIncome'
        }, inplace=True)
        
        # Convert income column to numeric, coercing errors to NaN, then fill with 0
        income_df['MedianHouseholdIncome'] = pd.to_numeric(income_df['MedianHouseholdIncome'], errors='coerce')
        income_df.fillna(0, inplace=True)
        print("Census data prepared.")

        # --- 2. Load and Prepare Camera Data from CSV ---
        print(f"Loading camera CSV data from: {camera_csv_path}")
        # Load the deduplicated logs. The column names are case-sensitive.
        camera_locations_df = pd.read_csv(camera_csv_path)
        
        # Corrected column names to match the likely CSV header (capitalized)
        lat_col = 'Latitude'
        lon_col = 'Longitude'

        # Verify that the columns exist before proceeding
        if lat_col not in camera_locations_df.columns or lon_col not in camera_locations_df.columns:
            raise KeyError(f"The required columns '{lat_col}' and '{lon_col}' were not found in {camera_csv_path}. Please check the CSV file's header.")

        # Count the number of cameras at each unique coordinate pair
        # We assume each row in the CSV represents one camera.
        camera_counts_by_loc = camera_locations_df.groupby([lat_col, lon_col]).size().reset_index(name='num_cameras')
        
        print(f"Found a total of {camera_locations_df.shape[0]} cameras at {camera_counts_by_loc.shape[0]} unique locations.")

        # Create a GeoDataFrame from the aggregated camera locations
        camera_gdf = gpd.GeoDataFrame(
            camera_counts_by_loc, 
            geometry=gpd.points_from_xy(camera_counts_by_loc[lon_col], camera_counts_by_loc[lat_col]),
            crs="EPSG:4326" # Standard CRS for lat/lon
        )
        print("Camera data prepared.")

        # --- 3. Load Census Tract Shapefiles ---
        print(f"Loading census tract shapefile from: {tracts_shapefile_path}...")
        tracts_gdf = gpd.read_file(tracts_shapefile_path)
        
        # Ensure both GeoDataFrames use the same CRS for accurate spatial operations
        if camera_gdf.crs != tracts_gdf.crs:
            print(f"Reprojecting tracts from {tracts_gdf.crs} to {camera_gdf.crs}...")
            tracts_gdf = tracts_gdf.to_crs(camera_gdf.crs)
        print("Census tracts loaded.")

        # --- 4. Perform Spatial Join ---
        # This joins the camera points to the census tract polygons they fall within.
        print("Performing spatial join to map cameras to tracts...")
        joined_gdf = gpd.sjoin(camera_gdf, tracts_gdf, how="inner", predicate='within')

        # --- 5. Aggregate Camera Counts per Tract ---
        print("Aggregating camera counts per tract...")
        camera_counts_per_tract = joined_gdf.groupby('GEOID')['num_cameras'].sum().reset_index()
        camera_counts_per_tract.rename(columns={'num_cameras': 'TotalCameras'}, inplace=True)
        
        total_cameras_mapped = camera_counts_per_tract['TotalCameras'].sum()
        print(f"Total cameras mapped to tracts: {total_cameras_mapped}")

        # --- 6. Merge Data for Final GeoJSON ---
        print("Merging aggregated data with tract geometries...")
        final_gdf = tracts_gdf.merge(income_df, on='GEOID', how='left')
        final_gdf = final_gdf.merge(camera_counts_per_tract, on='GEOID', how='left')
        
        # Fill tracts with no cameras with a count of 0 and handle potential missing income
        final_gdf['TotalCameras'].fillna(0, inplace=True)
        final_gdf['MedianHouseholdIncome'].fillna(0, inplace=True)
        
        # --- 7. Save Final GeoJSON ---
        print(f"Saving final enriched GeoJSON to: {output_geojson_path}")
        final_gdf.to_file(output_geojson_path, driver='GeoJSON')
        print(f"Analysis complete. GeoJSON file ready for mapping: {output_geojson_path}")

    except FileNotFoundError as e:
        print(f"Error: A required file was not found. {e}")
        print("Please ensure all file paths are correct and the files are in the right directory.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    # Define file paths based on the user's directory structure
    census_file = 'ACSDP_DP03_DP05_Joined.csv'
    camera_file = 'deduplicated_logs.csv' # Use the new CSV file
    shapefile_path = os.path.join('tl_2024_25_tract', 'tl_2024_25_tract.shp')
    output_geojson_file = 'camera_income_analysis.geojson'

    # Check for required files before running
    if not os.path.exists(census_file):
        print(f"ERROR: The census data file '{census_file}' was not found.")
    elif not os.path.exists(camera_file):
        print(f"ERROR: The camera csv file '{camera_file}' was not found.")
    elif not os.path.exists(shapefile_path):
        print(f"ERROR: The shapefile '{shapefile_path}' was not found. Please ensure the tl_2024_25_tract folder is present.")
    else:
        # Run the analysis
        analyze_camera_distribution(census_file, camera_file, shapefile_path, output_geojson_file)

