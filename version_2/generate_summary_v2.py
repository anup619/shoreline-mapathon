import geopandas as gpd
import pandas as pd
from pathlib import Path

OUTPUT_BASE = Path(r'D:\shoreline-mapathon\SHORELINE_DATA\PYTHON_OUTPUTS_V2')

MONTHS = [
    ("2023_02_21", "February"),
    ("2023_04_18", "April"),
    ("2023_05_20", "May"),
    ("2023_06_29", "June"),
    ("2023_07_15", "July"),
    ("2023_08_24", "August"),
    ("2023_12_14", "December"),
]

TIDAL_DATA = {
    "February":  {"HTL": 0.85, "LTL": 0.20, "MTL": 0.525},
    "April":     {"HTL": 0.70, "LTL": 0.30, "MTL": 0.500},
    "May":       {"HTL": 0.90, "LTL": 0.25, "MTL": 0.575},
    "June":      {"HTL": 0.70, "LTL": 0.35, "MTL": 0.525},
    "July":      {"HTL": 0.70, "LTL": 0.25, "MTL": 0.475},
    "August":    {"HTL": 0.70, "LTL": 0.40, "MTL": 0.550},
    "December":  {"HTL": 1.00, "LTL": 0.45, "MTL": 0.725},
}

REFERENCE_MTL = round(
    sum(v["MTL"] for v in TIDAL_DATA.values()) / len(TIDAL_DATA), 3
)

if __name__ == "__main__":

    print(f"\n{'='*60}")
    print("SHORELINE EXTRACTION RESULTS - 2023 V2")
    print("="*60)

    log_file = OUTPUT_BASE / "Processing_Log.csv"
    if log_file.exists():
        log_df = pd.read_csv(log_file)
        print("\nPROCESSING LOG:")
        print(log_df.to_string(index=False))
    else:
        print("Processing log not found - run shoreline_extraction_v2.py first")

    length_data = []
    for folder_name, month_name in MONTHS:
        sl_file = OUTPUT_BASE / folder_name / f"Shoreline_{month_name}_2023.gpkg"
        tidal = TIDAL_DATA.get(month_name, {})
        mtl = tidal.get("MTL", None)
        mtl_diff = round(mtl - REFERENCE_MTL, 3) if mtl else None
        flag = ""
        if mtl_diff is not None:
            if mtl_diff > 0.1:
                flag = "Higher tide than reference"
            elif mtl_diff < -0.1:
                flag = "Lower tide than reference"
            else:
                flag = "Near refernce"
        
        if sl_file.exists():
            sl = gpd.read_file(sl_file)
            if len(sl) > 0:
                length_data.append({
                    'Month' : f'{month_name} 2023',
                    'Shoreline Length (m)' : round(sl.geometry.length.sum(), 2),
                    'Status': 'Extracted',
                    'HTL (m)': tidal.get("HTL"),
                    'LTL (m)': tidal.get("LTL"),
                    'MTL (m)': mtl,
                    'MTL vs Reference': mtl_diff,
                    'Tidal Flag': flag
                })
            else:
                length_data.append({
                    'Month' : f"{month_name} 2023",
                    'Shoreline Length (m)' : None,
                    'Status': 'Empty',
                    'HTL (m)': tidal.get("HTL"),
                    'LTL (m)': tidal.get("LTL"),
                    'MTL (m)': mtl,
                    'MTL vs Reference': mtl_diff,
                    'Tidal Flag': flag
                })
        else:
            length_data.append({
                'Month' : f"{month_name} 2023",
                'Shoreline Length (m)' : None,
                'Status': 'Not processed / Skipped',
                'HTL (m)': tidal.get("HTL"),
                'LTL (m)': tidal.get("LTL"),
                'MTL (m)': mtl,
                'MTL vs Reference': mtl_diff,
                'Tidal Flag': flag
            })

    length_df = pd.DataFrame(length_data)

    print("\nEXTRACTED SHORELINE LENGTHS:")
    print(length_df.to_string(index=False))

    transect_file = OUTPUT_BASE / "Automated_Transect_Distances_V2.csv"
    if transect_file.exists():
        transect_df = pd.read_csv(transect_file)
        print(f"\n{'='*60}")
        print("SHORELINE POSITION CHANGE AT BEACH REFERNCE POINTS:")
        print("="*60)
        print(transect_df.to_string(index=False))
    else:
        print("\nTransect distances not found - run calculate_transect_distances_v2.py first")

    output_file = OUTPUT_BASE / "Final_Summary_V2.csv"
    with open(output_file, 'w') as f:
        f.write("SHORELINE LENGTHS\n")
        length_df.to_csv(f, index=False)
        print(f"\nReference MTL (mean across all dates): {REFERENCE_MTL}m")
        print("Note: Tidal correction not applied spatially — MTL deviation recorded as metadata.")
        print("Reason: Microtidal coast (range 0.3-0.9m), horizontal correction < 30m pixel size.")
        if not transect_df.empty:
            f.write("\n\nSHORELINE POSITION CHANGES\n")
            transect_df.to_csv(f, index=False)

    print(f"\nSummary saved to: {output_file}")
    print("="*60)