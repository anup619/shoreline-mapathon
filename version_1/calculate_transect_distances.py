import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import LineString, Point
import numpy as np

def create_perpendicular_transect(point, shoreline, length=1000):
    #Create a perpendicular line at a point crossing the shoreline
    # Find nearest point on shoreline
    nearest_point = shoreline.interpolate(shoreline.project(point))
    
    # Get local shoreline direction
    offset = 10
    p1 = shoreline.interpolate(max(0, shoreline.project(nearest_point) - offset))
    p2 = shoreline.interpolate(min(shoreline.length, shoreline.project(nearest_point) + offset))
    
    # Calculate perpendicular angle
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    angle = np.arctan2(dy, dx)
    perp_angle = angle + np.pi/2
    
    # Create transect line perpendicular to shoreline
    x_offset = length/2 * np.cos(perp_angle)
    y_offset = length/2 * np.sin(perp_angle)
    
    transect = LineString([
        (nearest_point.x - x_offset, nearest_point.y - y_offset),
        (nearest_point.x + x_offset, nearest_point.y + y_offset)
    ])
    
    return transect

def calculate_distance_at_point(beach_point, shoreline1, shoreline2):
    #Calculate distance between two shorelines at a beach point#
    # Create transect
    transect = create_perpendicular_transect(beach_point, shoreline1, length=1000)
    
    # Find intersections
    int1 = transect.intersection(shoreline1)
    int2 = transect.intersection(shoreline2)
    
    # Get intersection points (handle MultiPoint)
    if int1.is_empty or int2.is_empty:
        return None
    
    pt1 = Point(int1.coords[0]) if hasattr(int1, 'coords') else int1
    pt2 = Point(int2.coords[0]) if hasattr(int2, 'coords') else int2
    
    return pt1.distance(pt2)

# Main processing
base_path = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI")
python_path = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\PYTHON_OUTPUTS")

# Load beach points
beach_files = {
    'T.Mariyur Beach': 'T.Mariyur Beach.kml',
    'Sayalkudi beach': 'Sayalkudi beach.kml',
    'Keelvaipar Beach': 'Keelvaipar Beach.kml',
    'Ervadi Beach': 'Ervadi Beach.kml'
}

beach_points = {}
for name, filename in beach_files.items():
    gdf = gpd.read_file(base_path / filename)
    beach_points[name] = gdf.geometry.iloc[0]

# Load shorelines
april = gpd.read_file(python_path / "2023_04_18" / "Shoreline_April_2023.gpkg")
may = gpd.read_file(python_path / "2023_05_20" / "Shoreline_May_2023.gpkg")
august = gpd.read_file(python_path / "2023_08_24" / "Shoreline_August_2023.gpkg")

# Reproject beach points to match shoreline CRS
beach_points_proj = {}
for name, point in beach_points.items():
    gdf_temp = gpd.GeoDataFrame([{'geometry': point}], crs='EPSG:4326')
    gdf_proj = gdf_temp.to_crs(april.crs)
    beach_points_proj[name] = gdf_proj.geometry.iloc[0]

# Get shoreline geometries
april_geom = april.geometry.iloc[0]
may_geom = may.geometry.iloc[0]
august_geom = august.geometry.iloc[0]

# Calculate distances
results = []
for beach_name, point in beach_points_proj.items():
    apr_may = calculate_distance_at_point(point, april_geom, may_geom)
    may_aug = calculate_distance_at_point(point, may_geom, august_geom)
    apr_aug = calculate_distance_at_point(point, april_geom, august_geom)
    
    results.append({
        'Beach': beach_name,
        'Apr-May (m)': round(apr_may, 2) if apr_may else None,
        'May-Aug (m)': round(may_aug, 2) if may_aug else None,
        'Apr-Aug (m)': round(apr_aug, 2) if apr_aug else None
    })

# Create DataFrame
df = pd.DataFrame(results)

print("\n" + "="*80)
print("AUTOMATED TRANSECT DISTANCE ANALYSIS")
print("="*80)
print(df.to_string(index=False))
print("="*80)

# Save
output_file = Path(r".\Automated_Transect_Distances.csv")
df.to_csv(output_file, index=False)
print(f"\nResults saved to: {output_file}")