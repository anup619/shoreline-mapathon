import geopandas as gpd
import pandas as pd
from pathlib import Path

print("\n" + "="*80)
print("SHORELINE EXTRACTION RESULTS - 2023")
print("="*80)

# Load Python-generated shorelines
python_path = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\PYTHON_OUTPUTS")

april = gpd.read_file(python_path / "2023_04_18" / "Shoreline_April_2023.gpkg")
may = gpd.read_file(python_path / "2023_05_20" / "Shoreline_May_2023.gpkg")
august = gpd.read_file(python_path / "2023_08_24" / "Shoreline_August_2023.gpkg")

# Shoreline lengths
length_data = {
    'Month': ['April 2023', 'May 2023', 'August 2023'],
    'Shoreline Length (m)': [
        round(april.geometry.length.sum(), 2),
        round(may.geometry.length.sum(), 2),
        round(august.geometry.length.sum(), 2)
    ]
}

length_df = pd.DataFrame(length_data)
print("\nEXTRACTED SHORELINE LENGTHS:")
print(length_df.to_string(index=False))

# Load transect distances
transect_file = Path(r".\Automated_Transect_Distances.csv")
transect_df = pd.read_csv(transect_file)

print("\n" + "="*80)
print("SHORELINE POSITION CHANGE AT BEACH REFERENCE POINTS:")
print("="*80)
print(transect_df.to_string(index=False))
print("="*80)

# Save combined summary
output_file = Path(r".\Final_Summary.csv")
with open(output_file, 'w') as f:
    f.write("SHORELINE LENGTHS\n")
    length_df.to_csv(f, index=False)
    f.write("\n\nSHORELINE POSITION CHANGES\n")
    transect_df.to_csv(f, index=False)

print(f"\nSummary saved to: {output_file}")