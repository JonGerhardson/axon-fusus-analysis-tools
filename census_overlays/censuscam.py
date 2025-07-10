import pandas as pd
import geopandas as gpd
import json
import os

def analyze_camera_distribution(census_data_path, camera_geojson_path, tracts_shapefile_path, output_geojson_path):
    """
    Performs a spatial analysis to overlay camera locations on census tracts
    and correlate them with income data.

    Args:
        census_data_path (str): Path to the joined census data CSV.
        camera_geojson_path (str): Path to the GeoJSON file containing camera locations.
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

        # --- 2. Load and Prepare Camera Data ---
        print(f"Loading camera GeoJSON data from: {camera_geojson_path}")
        with open(camera_geojson_path, 'r') as f:
            camera_data = json.load(f)

        locations = []
        for feature in camera_data['features']:
            properties = feature.get('properties', {})
            log_stats = properties.get('log_stats', {})
            # Count cameras if 'cameras' key exists, otherwise default to 1 if it's just a location
            num_cameras = len(log_stats.get('cameras', [])) if log_stats and 'cameras' in log_stats else 1
            
            coordinates = feature['geometry']['coordinates']
            locations.append({
                'num_cameras': num_cameras,
                'longitude': coordinates[0],
                'latitude': coordinates[1]
            })

        camera_df = pd.DataFrame(locations)
        camera_gdf = gpd.GeoDataFrame(
            camera_df, 
            geometry=gpd.points_from_xy(camera_df.longitude, camera_df.latitude),
            crs="EPSG:4326" # Standard CRS for GeoJSON
        )
        print("Camera data prepared.")

        # --- 3. Load Census Tract Shapefiles ---
        print(f"Loading census tract shapefile from: {tracts_shapefile_path}")
        tracts_gdf = gpd.read_file(tracts_shapefile_path)
        
        # Ensure both GeoDataFrames use the same CRS
        tracts_gdf = tracts_gdf.to_crs(camera_gdf.crs)
        print("Census tracts loaded.")

        # --- 4. Perform Spatial Join ---
        print("Performing spatial join to map cameras to tracts...")
        joined_gdf = gpd.sjoin(camera_gdf, tracts_gdf, how="inner", predicate='within')

        # --- 5. Aggregate Camera Counts per Tract ---
        print("Aggregating camera counts per tract...")
        camera_counts = joined_gdf.groupby('GEOID')['num_cameras'].sum().reset_index()
        camera_counts.rename(columns={'num_cameras': 'TotalCameras'}, inplace=True)

        # --- 6. Merge Data for Final GeoJSON ---
        print("Merging aggregated data with tract geometries...")
        final_gdf = tracts_gdf.merge(income_df, on='GEOID', how='left')
        final_gdf = final_gdf.merge(camera_counts, on='GEOID', how='left')
        
        # Fill tracts with no cameras with a count of 0 and handle potential missing income
        final_gdf['TotalCameras'].fillna(0, inplace=True)
        final_gdf['MedianHouseholdIncome'].fillna(0, inplace=True)
        
        # --- 7. Save Final GeoJSON ---
        print(f"Saving final enriched GeoJSON to: {output_geojson_path}")
        final_gdf.to_file(output_geojson_path, driver='GeoJSON')
        print("Analysis complete. GeoJSON file ready for mapping.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Please ensure file paths are correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    # Define file paths based on the user's directory structure
    census_file = 'ACSDP_DP03_DP05_Joined.csv'
    camera_file = 'data.geojson' # Updated to match user's file name
    shapefile_path = os.path.join('tl_2024_25_tract', 'tl_2024_25_tract.shp')
    output_geojson_file = 'camera_income_analysis.geojson'

    # Run the analysis
    analyze_camera_distribution(census_file, camera_file, shapefile_path, output_geojson_file)

