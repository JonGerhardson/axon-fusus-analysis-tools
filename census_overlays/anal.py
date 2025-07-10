import geopandas as gpd
import pandas as pd

def perform_statistical_analysis(geojson_path):
    """
    Loads the enriched GeoJSON file and performs a statistical analysis
    on camera distribution versus income and population.

    Args:
        geojson_path (str): Path to the GeoJSON file created by the previous script.
    """
    try:
        # --- 1. Load the Data ---
        print(f"Loading data from {geojson_path}...")
        gdf = gpd.read_file(geojson_path)

        # --- 2. Feature Engineering: Create Normalized Metrics ---
        # To make a fair comparison, we calculate camera density.
        # We avoid dividing by zero if a tract has no population.
        gdf['CamerasPer1000People'] = gdf.apply(
            lambda row: (row['TotalCameras'] / row['TotalPopulation'] * 1000) if row['TotalPopulation'] > 0 else 0,
            axis=1
        )
        
        # Filter out tracts with no population for a cleaner correlation analysis
        analysis_gdf = gdf[gdf['TotalPopulation'] > 0].copy()
        
        print("\n--- Data Overview ---")
        print(analysis_gdf[['TractName', 'MedianHouseholdIncome', 'TotalPopulation', 'TotalCameras', 'CamerasPer1000People']].head())

        # --- 3. Correlation Analysis ---
        print("\n--- Correlation Analysis ---")
        # Calculate the Pearson correlation coefficient.
        # A value of +1 is a perfect positive correlation, -1 is a perfect negative, and 0 is no correlation.
        correlation = analysis_gdf['MedianHouseholdIncome'].corr(analysis_gdf['CamerasPer1000People'])
        
        print(f"Correlation between Median Household Income and Camera Density (per 1000 people): {correlation:.4f}")
        if correlation > 0.5:
            print("Interpretation: Strong positive correlation. Higher-income areas tend to have a higher density of cameras.")
        elif correlation > 0.1:
            print("Interpretation: Weak positive correlation. There is a slight tendency for higher-income areas to have more cameras.")
        elif correlation < -0.5:
            print("Interpretation: Strong negative correlation. Higher-income areas tend to have a lower density of cameras.")
        elif correlation < -0.1:
            print("Interpretation: Weak negative correlation. There is a slight tendency for lower-income areas to have more cameras.")
        else:
            print("Interpretation: No significant linear correlation between income and camera density.")

        # --- 4. Analysis by Income Bracket ---
        print("\n--- Camera Density by Income Bracket ---")
        # Create income brackets (quintiles) to see trends across groups
        try:
            analysis_gdf['IncomeBracket'] = pd.qcut(
                analysis_gdf[analysis_gdf['MedianHouseholdIncome'] > 0]['MedianHouseholdIncome'], 
                q=5, 
                labels=['Lowest', 'Low-Mid', 'Mid', 'Mid-High', 'Highest']
            )
        except ValueError:
             # Handle cases where quintiles can't be computed (e.g., not enough unique data points)
            print("Could not compute 5 income brackets, falling back to 3.")
            analysis_gdf['IncomeBracket'] = pd.qcut(
                analysis_gdf[analysis_gdf['MedianHouseholdIncome'] > 0]['MedianHouseholdIncome'], 
                q=3, 
                labels=['Low', 'Medium', 'High']
            )


        # Calculate the average camera density for each income bracket
        bracket_analysis = analysis_gdf.groupby('IncomeBracket')['CamerasPer1000People'].mean().reset_index()
        print(bracket_analysis.to_string(index=False))
        
    except FileNotFoundError:
        print(f"Error: The file {geojson_path} was not found. Please run the 'create_map_data.py' script first.")
    except Exception as e:
        print(f"An unexpected error occurred during analysis: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    geojson_file = 'camera_income_analysis.geojson'
    if not os.path.exists(geojson_file):
        print(f"ERROR: Analysis file '{geojson_file}' not found. Please run 'create_map_data.py' first.")
    else:
        perform_statistical_analysis(geojson_file)
