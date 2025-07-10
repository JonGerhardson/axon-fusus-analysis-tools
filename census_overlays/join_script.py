import pandas as pd
import os

def join_census_data(dp03_path, dp05_path, output_path):
    """
    This script joins two American Community Survey (ACS) data profiles 
    (DP03 - Economic Characteristics and DP05 - Demographic and Housing Estimates)
    on their common geographic identifier (GEO_ID).

    Args:
        dp03_path (str): The file path for the DP03 data CSV.
        dp05_path (str): The file path for the DP05 data CSV.
        output_path (str): The file path to save the merged CSV.
    """
    try:
        # --- Load the Data ---
        # The ACS data files from data.census.gov come with two header rows.
        # The first row contains the machine-readable variable names (e.g., DP03_0001E),
        # and the second row contains human-readable descriptions.
        # We will use the first row as the column headers and skip the second row.
        print(f"Loading economic data from: {dp03_path}")
        df_dp03 = pd.read_csv(dp03_path, header=0, skiprows=[1], dtype={'GEO_ID': str})
        
        print(f"Loading demographic data from: {dp05_path}")
        df_dp05 = pd.read_csv(dp05_path, header=0, skiprows=[1], dtype={'GEO_ID': str})
        
        print("\nData loaded successfully. First 5 rows of each table:")
        print("\n--- DP03 (Economic) ---")
        print(df_dp03.head())
        print("\n--- DP05 (Demographic) ---")
        print(df_dp05.head())

        # --- Perform the Join ---
        # We will perform an 'inner' join. This type of join combines rows from both
        # tables where the key ('GEO_ID') exists in BOTH tables. This is ideal for 
        # ensuring that our final dataset contains complete records.
        print("\nPerforming an inner join on 'GEO_ID'...")
        merged_df = pd.merge(df_dp03, df_dp05, on='GEO_ID', how='inner')

        # --- Clean Up Columns ---
        # When merging, pandas automatically adds suffixes ('_x', '_y') to columns
        # that have the same name in both tables (except for the join key).
        # In this case, the 'NAME' column (Geographic Area Name) is duplicated.
        # We will drop the duplicate and rename the original for a clean output.
        if 'NAME_y' in merged_df.columns:
            merged_df = merged_df.drop(columns=['NAME_y'])
        if 'NAME_x' in merged_df.columns:
            merged_df = merged_df.rename(columns={'NAME_x': 'NAME'})

        print("\nJoin complete. Columns cleaned.")
        print("Shape of the final merged table:", merged_df.shape)
        
        # --- Save the Result ---
        # The final, merged DataFrame is saved to a new CSV file.
        # `index=False` prevents pandas from writing the DataFrame index as a column.
        merged_df.to_csv(output_path, index=False)
        print(f"\nSuccessfully saved the joined data to: {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}. Please make sure the file paths are correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    # Define the file paths for your data.
    # Assumes the script is in the same directory as the CSV files.
    # If not, provide the full path to the files.
    dp03_file = 'ACSDP5Y2023.DP03-Data.csv'
    dp05_file = 'ACSDP5Y2023.DP05-Data.csv'
    output_file = 'ACSDP_DP03_DP05_Joined.csv'

    # Check if the required files exist in the current directory
    if not os.path.exists(dp03_file) or not os.path.exists(dp05_file):
        print("Error: Make sure the data files ('ACSDP5Y2023.DP03-Data.csv' and 'ACSDP5Y2023.DP05-Data.csv') are in the same directory as this script.")
    else:
        join_census_data(dp03_file, dp05_file, output_file)

