import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging
from scipy.stats import pearsonr

# --- 1. Setup Logging ---
# Use Python's logging module for better feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 8. Modularize Plot Generation ---
def _save_regplot(data, x_var, y_var, title, path, xlabel, ylabel, annotation_text):
    """Helper function to create and save a regression plot."""
    try:
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.regplot(x=x_var, y=y_var, data=data, ax=ax,
                    scatter_kws={'alpha': 0.6, 'color': '#2c7fb8'}, 
                    line_kws={'color': '#d95f02'})
        ax.set_title(title, fontsize=16)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        # Add annotation for correlation
        ax.annotate(annotation_text, xy=(0.05, 0.95), xycoords='axes fraction',
                    fontsize=12, ha='left', va='top',
                    bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.5))
        # Prevent y-axis from showing negative values for density
        ax.set_ylim(bottom=0)
        # Format x-axis for currency if it's income
        if 'Income' in xlabel:
            ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        logger.info(f"Saved plot: {path}")
    except Exception as e:
        logger.error(f"Failed to generate regression plot for {x_var}: {e}")

def _save_barplot(data, x_var, y_var, title, path, xlabel, ylabel, overall_mean=None):
    """Helper function to create and save a bar plot."""
    try:
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.barplot(x=x_var, y=y_var, data=data, ax=ax, palette='viridis', hue=x_var, dodge=False, legend=False)
        ax.set_title(title, fontsize=16)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        # Add a horizontal line for the overall mean
        if overall_mean is not None:
            ax.axhline(y=overall_mean, color='r', linestyle='--', label=f'Overall Mean ({overall_mean:.2f})')
            ax.legend()
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        logger.info(f"Saved plot: {path}")
    except Exception as e:
        logger.error(f"Failed to generate bar plot for {x_var}: {e}")

def _save_hexbin_plot(data, x_var, y_var, title, path, xlabel, ylabel, city_median=None, state_median=None):
    """Helper function to create and save a hexbin plot to show data density."""
    try:
        fig, ax = plt.subplots(figsize=(12, 8))
        # Use a logarithmic color scale if the counts vary widely
        hb = ax.hexbin(x=data[x_var], y=data[y_var], gridsize=25, cmap='cividis', mincnt=1)
        ax.set_title(title, fontsize=16)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        
        # Add a color bar to show the number of data points in each hex
        cb = fig.colorbar(hb, ax=ax)
        cb.set_label('Number of Census Tracts')
        
        # Add reference lines for city and state medians
        if city_median:
            ax.axvline(x=city_median, color='cyan', linestyle='--', linewidth=2, label=f'Chicopee Median (${city_median:,.0f})')
        if state_median:
            ax.axvline(x=state_median, color='magenta', linestyle='--', linewidth=2, label=f'MA Median (${state_median:,.0f})')
        
        if city_median or state_median:
            ax.legend()

        # Format x-axis for currency
        if 'Income' in xlabel:
            ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))
        
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        logger.info(f"Saved plot: {path}")
    except Exception as e:
        logger.error(f"Failed to generate hexbin plot for {x_var}: {e}")


def perform_statistical_analysis(geojson_path, census_data_path, output_dir="analysis_results", chicopee_median=66927, ma_median=101341):
    """
    Loads the enriched GeoJSON file and performs a statistical analysis
    on camera distribution versus income and poverty data.

    Args:
        geojson_path (str): Path to the GeoJSON file created by the data prep script.
        census_data_path (str): Path to the original joined census data CSV to pull more variables.
        output_dir (str): Directory to save the output plots and data.
        chicopee_median (int): Median household income for Chicopee.
        ma_median (int): Median household income for Massachusetts.
    """
    try:
        # --- 2. Dynamic Output Directory ---
        os.makedirs(output_dir, exist_ok=True)

        # --- 1. Load the Data ---
        logger.info(f"Loading data from {geojson_path}...")
        gdf = gpd.read_file(geojson_path)

        # --- 6. Data Validation Checks ---
        assert not gdf.empty, "GeoJSON file is empty or could not be loaded."
        assert 'TotalCameras' in gdf.columns, "GeoJSON is missing 'TotalCameras' data. Please re-run the data creation script."
        assert 'TotalPopulation' in gdf.columns, "GeoJSON is missing 'TotalPopulation' data. Please re-run the data creation script."

        logger.info(f"Loading additional census data from {census_data_path}...")
        census_df = pd.read_csv(census_data_path, dtype={'GEO_ID': str})
        census_df['GEOID'] = census_df['GEO_ID'].apply(lambda x: x.split('US')[-1])
        
        # Select poverty column
        extra_vars_df = census_df[['GEOID', 'DP03_0128PE']].copy()
        extra_vars_df.rename(columns={'DP03_0128PE': 'PovertyRate'}, inplace=True)
        
        analysis_gdf = gdf.merge(extra_vars_df, on='GEOID', how='left')

        # --- 2. Feature Engineering & Data Cleaning ---
        analysis_gdf['CamerasPer1000People'] = analysis_gdf.apply(
            lambda row: (row['TotalCameras'] / row['TotalPopulation'] * 1000) if row['TotalPopulation'] > 0 else 0,
            axis=1
        )
        
        # --- 1. Handle Missing Census Data Gracefully ---
        analysis_gdf['PovertyRate'] = pd.to_numeric(analysis_gdf['PovertyRate'], errors='coerce')
        missing_poverty = analysis_gdf['PovertyRate'].isna().sum()
        if missing_poverty > 0:
            logger.warning(f"{missing_poverty} tracts have missing poverty data and will be excluded from poverty-specific analysis.")
        
        analysis_gdf_clean = analysis_gdf[analysis_gdf['TotalPopulation'] > 0].copy()
        
        # --- Contextual Income Analysis ---
        logger.info("\n--- Contextual Income Analysis ---")
        tracts_above_city_median = analysis_gdf_clean[analysis_gdf_clean['MedianHouseholdIncome'] > chicopee_median].shape[0]
        total_tracts = analysis_gdf_clean.shape[0]
        percent_above_city = (tracts_above_city_median / total_tracts) * 100 if total_tracts > 0 else 0
        avg_tract_income = analysis_gdf_clean['MedianHouseholdIncome'].mean()
        logger.info(f"The average median income of tracts in this dataset is ${avg_tract_income:,.0f}.")
        logger.info(f"Comparison with Chicopee Median Income (${chicopee_median:,}):")
        logger.info(f"{tracts_above_city_median} of {total_tracts} tracts ({percent_above_city:.1f}%) are above the city's median income.")

        # --- 3. Statistical Significance Testing ---
        logger.info("\n--- Correlation Analysis ---")
        
        # Income Correlation
        income_data = analysis_gdf_clean[['MedianHouseholdIncome', 'CamerasPer1000People']].dropna()
        corr_income, p_income = pearsonr(income_data['MedianHouseholdIncome'], income_data['CamerasPer1000People'])
        logger.info(f"Income vs. Cameras: r={corr_income:.4f}, p-value={p_income:.4g}")
        
        # Poverty Correlation
        poverty_data = analysis_gdf_clean[['PovertyRate', 'CamerasPer1000People']].dropna()
        corr_poverty, p_poverty = pearsonr(poverty_data['PovertyRate'], poverty_data['CamerasPer1000People'])
        logger.info(f"Poverty Rate vs. Cameras: r={corr_poverty:.4f}, p-value={p_poverty:.4g}")

        # --- 4. Error-Proof Income Brackets ---
        logger.info("\n--- Camera Density by Income Bracket ---")
        valid_income_gdf = analysis_gdf_clean[analysis_gdf_clean['MedianHouseholdIncome'] > 0]
        if len(valid_income_gdf) >= 5:
            valid_income_gdf['IncomeBracket'] = pd.qcut(
                valid_income_gdf['MedianHouseholdIncome'], 
                q=5, 
                labels=['Lowest', 'Low-Mid', 'Mid', 'Mid-High', 'Highest'],
                duplicates='drop'
            )
            bracket_analysis = valid_income_gdf.groupby('IncomeBracket', observed=False)['CamerasPer1000People'].mean().reset_index()
            print(bracket_analysis.to_string(index=False))
            
            # --- 5. Enhanced Visualization (Bar Chart) ---
            _save_barplot(
                data=bracket_analysis,
                x_var='IncomeBracket', y_var='CamerasPer1000People',
                title='Average Camera Density by Income Bracket',
                path=os.path.join(output_dir, 'camera_density_by_income_bracket.png'),
                xlabel='Income Bracket', ylabel='Average Cameras per 1,000 People',
                overall_mean=analysis_gdf_clean['CamerasPer1000People'].mean()
            )
        else:
            logger.warning("Insufficient data for income quintiles. Skipping bracket analysis and bar chart.")

        # --- 5 & 7. Generate Visualizations ---
        logger.info("\nGenerating analysis plots...")
        
        _save_hexbin_plot(
            data=income_data, x_var='MedianHouseholdIncome', y_var='CamerasPer1000People',
            title='Density of Census Tracts by Income and Camera Count',
            path=os.path.join(output_dir, 'income_vs_cameras_hexbin.png'),
            xlabel='Median Household Income ($)', ylabel='Cameras per 1,000 People',
            city_median=chicopee_median, state_median=ma_median
        )
        
        _save_regplot(
            data=poverty_data, x_var='PovertyRate', y_var='CamerasPer1000People',
            title='Poverty Rate vs. Camera Density',
            path=os.path.join(output_dir, 'poverty_vs_cameras.png'),
            xlabel='Poverty Rate (%)', ylabel='Cameras per 1,000 People',
            annotation_text=f'r = {corr_poverty:.2f}\np-value = {p_poverty:.3g}'
        )

    # --- 10. Improved Error Handling ---
    except (FileNotFoundError, KeyError, AssertionError) as e:
        logger.error(f"Data processing failed: {e}")
    except Exception as e:
        logger.exception("An unexpected and critical error occurred:")

# --- Main Execution Block ---
if __name__ == "__main__":
    geojson_file = 'camera_income_analysis.geojson'
    census_file = 'ACSDP_DP03_DP05_Joined.csv'
    if not os.path.exists(geojson_file):
        logger.error(f"Analysis file '{geojson_file}' not found. Please run 'create_map_data.py' first.")
    else:
        perform_statistical_analysis(geojson_file, census_file)
