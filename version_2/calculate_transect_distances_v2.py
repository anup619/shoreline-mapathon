import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import LineString, Point
import numpy as np

BASE_PATH = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI")
OUTPUT_BASE = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\PYTHON_OUTPUTS_V2")

MONTHS = [
    ("2023_02_21", "February"),
    ("2023_04_18", "April"),
    ("2023_05_20", "May"),
    ("2023_06_29", "June"),
    ("2023_07_15", "July"),
    ("2023_08_24", "August"),
    ("2023_12_14", "December"),
]

BEACH_FILES = {
    'T.Mariyur Beach': 'T.Mariyur Beach.kml',
    'Sayalkudi beach': 'Sayalkudi beach.kml',
    'Keelvaipar Beach': 'Keelvaipar Beach.kml',
    'Ervadi Beach': 'Ervadi Beach.kml'
}

def create_perpendicular_transect(point, shoreline, length = 1000):
    nearest_point = shoreline.interpolate(shoreline.project(point))

    offset = 10
    p1 = shoreline.interpolate(max(0, shoreline.project(nearest_point) - offset))
    p2 = shoreline.interpolate(min((shoreline.length, shoreline.project(nearest_point) + offset)))

    dx = p2.x - p1.x
    dy = p2.y - p1.y
    angle = np.arctan2(dy, dx)
    perp_angle = angle + np.pi / 2

    x_offest = length / 2 * np.cos(perp_angle)
    y_offset = length / 2 * np.sin(perp_angle)

    transect = LineString([
        (nearest_point.x - x_offest, nearest_point.y - y_offset),
        (nearest_point.x + x_offest, nearest_point.y + y_offset)
    ])
    return transect

def calculate_distance_at_point(beach_point, shoreline1, shoreline2):
    transect = create_perpendicular_transect(beach_point, shoreline1, length=1000)

    int1 = transect.intersection(shoreline1)
    int2 = transect.intersection(shoreline2)

    if int1.is_empty or int2.is_empty:
        return None
    
    pt1 = Point(int1.coords[0]) if hasattr(int1, 'coords') else int1
    pt2 = Point(int2.coords[0]) if hasattr(int2, 'coords') else int2
    
    return pt1.distance(pt2)

if __name__ == "__main__":

    beach_points_raw = {}
    for name, filename in BEACH_FILES.items():
        gdf = gpd.read_file(BASE_PATH / filename)
        beach_points_raw[name] = gdf.geometry.iloc[0]

    shorelines = {}
    for folder_name, month_name in MONTHS:
        sl_file = OUTPUT_BASE / folder_name / f"Shoreline_{month_name}_2023.gpkg"
        if sl_file.exists():
            sl = gpd.read_file(sl_file)
            if len(sl) > 0:
                shorelines[month_name] = sl
                print(f"Loaded: {month_name}")
            else:
                print(f"File not found - skipping: {month_name}")
        else:
            print(f"File not found - skipping: {month_name}")
    
    if len(shorelines) < 2:
        print("Need at least 2 shorelines for change detection")
        exit()

    ref_crs = list(shorelines.values())[0].crs

    beach_points = {}
    for name, point in beach_points_raw.items():
        gdf_temp = gpd.GeoDataFrame([{'geometry': point}], crs='EPSG:4326')
        gdf_proj = gdf_temp.to_crs(ref_crs)
        beach_points[name] = gdf_proj.geometry.iloc[0]

    month_names = list(shorelines.keys())

    results = []

    for beach_name, point in beach_points.items():
        row = {"Beach": beach_name}

        for i in range(len(month_names) - 1):
            m1 = month_names[i]
            m2 = month_names[i+1]
            geom1 = shorelines[m1].geometry.iloc[0]
            geom2 = shorelines[m2].geometry.iloc[0]
            dist = calculate_distance_at_point(point, geom1, geom2)
            col_name = f"{m1[:3]} - {m2[:3]} (m)"
            row[col_name] = round(dist, 2) if dist is not None else None

        first_month = month_names[0]
        last_month = month_names[-1]
        geom_first = shorelines[first_month].geometry.iloc[0]
        geom_last = shorelines[last_month].geometry.iloc[0]
        dist_total = calculate_distance_at_point(point, geom_first, geom_last)
        row[f"{first_month[:3]}-{last_month[:3]} Total (m)"] = round(dist_total, 2) if dist_total is not None else None

        results.append(row)

    df = pd.DataFrame(results)

    print(f"\n{'='*60}")
    print("AUTOMATED TRANSECT DISTANCE ANALYSIS -V2")
    print("="*60)
    print(df.to_string(index=False))
    print("="*60)

    output_file = OUTPUT_BASE / "Automated_Transect_Distances_V2.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

