import geopandas as gpd
import pandas as pd
from pathlib import Path
import json
import os

project_dir = os.path.dirname(os.path.dirname(__file__))
shoreline_data_dir = os.path.join(project_dir, "SHORELINE_DATA")
OUTPUT_BASE = Path(os.path.join(shoreline_data_dir, "PYTHON_OUTPUTS_V2"))
BASE_PATH = Path(os.path.join(shoreline_data_dir,"SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI"))
GEOJSON_OUT = Path(os.path.join(OUTPUT_BASE , "geojson"))
GEOJSON_OUT.mkdir(exist_ok=True)

MONTHS = [
    ("2023_02_21", "February"),
    ("2023_04_18", "April"),
    ("2023_05_20", "May"),
    ("2023_06_29", "June"),
    ("2023_07_15", "July"),
    ("2023_08_24", "August"),
    ("2023_12_14", "December"),
]

MONTH_COLORS = {
    "February": "#4e79a7",
    "April":    "#f28e2b",
    "May":      "#59a14f",
    "June":     "#e15759",
    "July":     "#76b7b2",
    "August":   "#edc948",
    "December": "#b07aa1",
}

BEACH_FILES = {
    "T.Mariyur Beach":  "T.Mariyur Beach.kml",
    "Sayalkudi Beach":  "Sayalkudi beach.kml",
    "Keelvaipar Beach": "Keelvaipar Beach.kml",
    "Ervadi Beach":     "Ervadi Beach.kml",
}

def convert_shorelines():
    print(f"\n{'='*60}")
    print("SHORELINES")
    print(f"{'='*60}")
    gdfs = []

    for folder_name, month_name in MONTHS:
        gpkg_path = OUTPUT_BASE / folder_name / f"Shoreline_{month_name}_2023.gpkg"

        if not gpkg_path.exists():
            print(f"[SKIP] {month_name} - file not found: {gpkg_path}")
            continue

        gdf = gpd.read_file(gpkg_path)
        length_m = gdf.geometry.length.values[0]
        gdf = gdf.to_crs("EPSG:4326")
        if gdf.empty:
            print(f"[SKIP] {month_name} - empty layer")
            continue

        gdf = gdf[["geometry"]].copy()
        gdf["month"] = month_name
        gdf["date"] = folder_name
        gdf["color"] = MONTH_COLORS[month_name]
        gdf["length_m"] = length_m

        gdfs.append(gdf)
        print(f"[OK] {month_name} ({len(gdf)} feature(s))")

    if not gdfs:
        print("[ERROR]: No shoreline files found. Check OUTPUT_BASE path")

    combined = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    combined = combined.set_crs("EPSG:4326", allow_override=True)

    out_path = GEOJSON_OUT / "shorelines.geojson"
    combined.to_file(out_path, driver="GeoJSON")
    print(f"\n Saved - {out_path} ({len(combined)} total features)")


def convert_beach_points():
    print(f"\n{'='*60}")
    print("BEACH POINTS")
    print(f"{'='*60}")
    gdfs = []

    for beach_name, filename in BEACH_FILES.items():
        kml_path = BASE_PATH / filename

        if not kml_path.exists():
            print(f"[SKIP] {beach_name} - file not found: {kml_path}")
            continue

        gdf = gpd.read_file(kml_path)
        if gdf.empty:
            print(f"[SKIP] {beach_name} - empty layer")
            continue

        gdf = gdf.to_crs("EPSG:4326")

        point_row = gdf.iloc[[0]][["geometry"]].copy()
        point_row["name"] = beach_name

        gdfs.append(point_row)
        print(f"[OK] {beach_name}")

    if not gdfs:
        print("[ERROR]: No beach kml files found. Check BASE_PATH")
        return
    
    combined = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    combined = combined.set_crs("EPSG:4326", allow_override=True)

    out_path = GEOJSON_OUT / "beach_points.geojson"
    combined.to_file(out_path, driver="GeoJSON")
    print(f"\n Saved - {out_path} ({len(combined)} total features)")

def write_app_data():

    app_data = {
        "tidalData": {
            "February":  {"HTL": 0.85, "LTL": 0.20, "MTL": 0.525},
            "April":     {"HTL": 0.70, "LTL": 0.30, "MTL": 0.500},
            "May":       {"HTL": 0.90, "LTL": 0.25, "MTL": 0.575},
            "June":      {"HTL": 0.70, "LTL": 0.35, "MTL": 0.525},
            "July":      {"HTL": 0.70, "LTL": 0.25, "MTL": 0.475},
            "August":    {"HTL": 0.70, "LTL": 0.40, "MTL": 0.550},
            "December":  {"HTL": 1.00, "LTL": 0.45, "MTL": 0.725},
        },
        "referenceMTL": 0.554,

        "transectChanges": {
            "T.Mariyur Beach": {
                "Feb-Apr": 2.76,  "Apr-May": 7.15,  "May-Jun": 0.68,
                "Jun-Jul": 3.07,  "Jul-Aug": 12.60, "Aug-Dec": 1.78,
                "Feb-Dec": 4.79
            },
            "Sayalkudi Beach": {
                "Feb-Apr": 1.01,  "Apr-May": 0.69,  "May-Jun": 1.80,
                "Jun-Jul": 0.64,  "Jul-Aug": 6.78,  "Aug-Dec": 6.39,
                "Feb-Dec": 0.57
            },
            "Keelvaipar Beach": {
                "Feb-Apr": 1.19,  "Apr-May": 4.75,  "May-Jun": 0.90,
                "Jun-Jul": 2.49,  "Jul-Aug": 3.28,  "Aug-Dec": 3.72,
                "Feb-Dec": 6.62
            },
            "Ervadi Beach": {
                "Feb-Apr": None,  "Apr-May": 5.59,  "May-Jun": 3.75,
                "Jun-Jul": 2.24,  "Jul-Aug": 1.81,  "Aug-Dec": 12.72,
                "Feb-Dec": None
            },
        },

        "shorelineLengths": {
            "February": 183164.39,
            "April":    316946.28,
            "May":      283894.55,
            "June":     348668.16,
            "July":     261958.16,
            "August":   243840.29,
            "December": 302301.96,
        },

        "cloudCoverage": {
            "February": 10.33,
            "April":    0.95,
            "May":      0.84,
            "June":     0.08,
            "July":     0.05,
            "August":   0.14,
            "December": 4.51,
        },

        "ndwiThresholds": {
            "February": -0.0902,
            "April":    -0.0902,
            "May":      -0.0980,
            "June":     -0.0902,
            "July":     -0.0745,
            "August":   -0.0745,
            "December": -0.1137,
        },

        "monthColors": {
            "February": "#4e79a7",
            "April":    "#f28e2b",
            "May":      "#59a14f",
            "June":     "#e15759",
            "July":     "#76b7b2",
            "August":   "#edc948",
            "December": "#b07aa1",
        },

        "months": ["February", "April", "May", "June", "July", "August", "December"],

        "timePeriods": ["Feb-Apr", "Apr-May", "May-Jun", "Jun-Jul", "Jul-Aug", "Aug-Dec"],

        "beaches": ["T.Mariyur Beach", "Sayalkudi Beach", "Keelvaipar Beach", "Ervadi Beach"],
    }

    out_path = GEOJSON_OUT / "appData.json"
    with open(out_path, "w") as f:
        json.dump(app_data, f, indent=2)

    print(f"\n{'='*60}")
    print("APP DATA")
    print(f"{'='*60}")
    print(f"  Saved - {out_path}")

def compute_transects():
    print(f"\n{'='*60}")
    print("TRANSECTS")
    print(f"{'='*60}")

    from shapely.geometry import LineString, Point, mapping
    import numpy as np

    # load beach points
    beach_gdfs = {}
    for beach_name, filename in BEACH_FILES.items():
        kml_path = BASE_PATH / filename
        if not kml_path.exists():
            continue
        gdf = gpd.read_file(kml_path)
        gdf = gdf.to_crs("EPSG:32643")  # work in UTM for accurate geometry
        beach_gdfs[beach_name] = gdf.geometry.iloc[0]

    # load shorelines in UTM
    shorelines = {}
    for folder_name, month_name in MONTHS:
        gpkg_path = OUTPUT_BASE / folder_name / f"Shoreline_{month_name}_2023.gpkg"
        if not gpkg_path.exists():
            continue
        gdf = gpd.read_file(gpkg_path)
        if gdf.empty:
            continue
        shorelines[month_name] = gdf.geometry.iloc[0]

    def create_transect(point, shoreline, length=2000):
        nearest = shoreline.interpolate(shoreline.project(point))
        offset = 10
        p1 = shoreline.interpolate(max(0, shoreline.project(nearest) - offset))
        p2 = shoreline.interpolate(min(shoreline.length, shoreline.project(nearest) + offset))
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        angle = np.arctan2(dy, dx)
        perp = angle + np.pi / 2
        x_off = length / 2 * np.cos(perp)
        y_off = length / 2 * np.sin(perp)
        return LineString([
            (nearest.x - x_off, nearest.y - y_off),
            (nearest.x + x_off, nearest.y + y_off)
        ])

    features = []
    month_names = list(shorelines.keys())

    for beach_name, beach_point in beach_gdfs.items():
        for i, m1 in enumerate(month_names):
            for m2 in month_names[i+1:]:
                sl1 = shorelines[m1]
                sl2 = shorelines[m2]

                transect = create_transect(beach_point, sl1)

                int1 = transect.intersection(sl1)
                int2 = transect.intersection(sl2)

                if int1.is_empty or int2.is_empty:
                    continue

                def extract_point(geom):
                    if geom.is_empty:
                        return None
                    if geom.geom_type == 'Point':
                        return geom
                    elif geom.geom_type == 'MultiPoint':
                        return geom.geoms[0]
                    elif geom.geom_type in ('LineString', 'MultiLineString'):
                        # transect runs along shoreline — take midpoint
                        return geom.interpolate(0.5, normalized=True)
                    elif geom.geom_type == 'GeometryCollection':
                        for g in geom.geoms:
                            if g.geom_type == 'Point':
                                return g
                    return None

                pt1 = extract_point(int1)
                pt2 = extract_point(int2)

                if pt1 is None or pt2 is None:
                    continue

                distance = round(pt1.distance(pt2), 2)

                # convert everything to WGS84 for GeoJSON
                def to_wgs84(geom):
                    gdf_temp = gpd.GeoDataFrame([{'geometry': geom}], crs='EPSG:32643')
                    return gdf_temp.to_crs('EPSG:4326').geometry.iloc[0]

                transect_wgs = to_wgs84(transect)
                pt1_wgs = to_wgs84(pt1)
                pt2_wgs = to_wgs84(pt2)

                features.append({
                    'beach': beach_name,
                    'month1': m1,
                    'month2': m2,
                    'transect': list(transect_wgs.coords),
                    'intersection1': list(pt1_wgs.coords)[0],
                    'intersection2': list(pt2_wgs.coords)[0],
                    'distance_m': distance,
                })

                print(f"  [OK] {beach_name} | {m1} vs {m2} | {distance}m")

    out_path = GEOJSON_OUT / "transects.json"
    with open(out_path, "w") as f:
        json.dump(features, f, indent=2)

    print(f"\n  Saved - {out_path} ({len(features)} transects)")

if __name__ == "__main__":
    print("=" * 60)
    print("  Shoreline V2 - GeoJSON Converter")
    print("=" * 60)

    convert_shorelines()
    convert_beach_points()
    compute_transects()
    write_app_data()