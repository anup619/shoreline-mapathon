import rasterio
import numpy as np
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import shape
import os
from pathlib import Path
import pandas as pd

def calculate_ndwi(b3_path, b5_path, output_path):
    #Calculate NDWI from Green and NIR bands
    with rasterio.open(b3_path) as b3_src:
        b3 = b3_src.read(1).astype('float32')
        profile = b3_src.profile
        
    with rasterio.open(b5_path) as b5_src:
        b5 = b5_src.read(1).astype('float32')
    
    # Calculate NDWI
    ndwi = (b3 - b5) / (b3 + b5 + 1e-10)  # Add small value to avoid division by zero
    
    # Update profile for output
    profile.update(dtype=rasterio.float32, count=1)
    
    # Write NDWI
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(ndwi, 1)
    
    print(f"NDWI calculated: {output_path}")
    return output_path

def clip_raster_to_aoi(raster_path, aoi_path, output_path):
    #Clip raster to AOI polygon
    aoi = gpd.read_file(aoi_path)
    
    with rasterio.open(raster_path) as src:
        # Reproject AOI to match raster CRS
        aoi_reprojected = aoi.to_crs(src.crs)
        
        geoms = [shape(geom) for geom in aoi_reprojected.geometry]
        out_image, out_transform = mask(src, geoms, crop=True)
        out_meta = src.meta.copy()
        
        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })
        
        with rasterio.open(output_path, 'w', **out_meta) as dst:
            dst.write(out_image)
    
    print(f"Raster clipped to AOI: {output_path}")
    return output_path

def fill_nodata(input_path, output_path, max_distance=5):
    #Fill NoData pixels using nearest neighbor interpolation
    from rasterio.fill import fillnodata
    
    with rasterio.open(input_path) as src:
        data = src.read(1)
        profile = src.meta.copy()
        
        # Create mask (True where data exists)
        mask = data != src.nodata
        
        # Fill nodata
        filled = fillnodata(data, mask, max_search_distance=max_distance)
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(filled, 1)
    
    print(f"NoData filled: {output_path}")
    return output_path


def extract_shoreline_by_proximity(ndwi_path, beach_points_dir, output_path, min_length=10000):
    #Extract shoreline based on proximity to beach reference points
    import subprocess
    import tempfile
    
    temp_dir = tempfile.gettempdir()
    temp_contour = os.path.join(temp_dir, "temp_contours.shp")
    
    cmd = [
        'gdal_contour',
        '-b', '1',
        '-a', 'ELEV',
        '-i', '0.1',
        '-f', 'ESRI Shapefile',
        ndwi_path,
        temp_contour
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Load all beach points
    beach_files = list(Path(beach_points_dir).glob("*Beach.kml"))
    all_points = []
    for bf in beach_files:
        pts = gpd.read_file(bf)
        all_points.append(pts)
    beach_points = gpd.GeoDataFrame(pd.concat(all_points, ignore_index=True))
    
    # Load contours
    contours = gpd.read_file(temp_contour)
    zero_contours = contours[contours['ELEV'] == 0].copy()
    zero_contours['length'] = zero_contours.geometry.length
    
    # Filter by minimum length
    valid_contours = zero_contours[zero_contours['length'] > min_length].copy()
    
    if len(valid_contours) == 0:
        print("No valid contours found")
        return None
    
    # Reproject beach points to match contours CRS
    beach_points_proj = beach_points.to_crs(valid_contours.crs)
    
    # Calculate minimum distance from each contour to any beach point
    valid_contours['min_dist_to_beach'] = valid_contours.geometry.apply(
        lambda geom: min([geom.distance(pt) for pt in beach_points_proj.geometry])
    )
    
    # Select contour with minimum distance to beaches
    best_shoreline = valid_contours.nsmallest(1, 'min_dist_to_beach')
    
    best_shoreline.to_file(output_path)
    print(f"Shoreline saved: {output_path}")
    print(f"Shoreline length: {best_shoreline['length'].values[0]:.2f} meters")
    print(f"Distance to nearest beach point: {best_shoreline['min_dist_to_beach'].values[0]:.2f} meters")
    
    return output_path

def extract_shoreline_contour(ndwi_path, output_path, min_length=10000):
    #Extract zero contour from NDWI and filter by length
    import subprocess
    import tempfile
    
    temp_dir = tempfile.gettempdir()
    temp_contour = os.path.join(temp_dir, "temp_contours.shp")
    
    cmd = [
        'gdal_contour',
        '-b', '1',
        '-a', 'ELEV',
        '-i', '0.1',
        '-f', 'ESRI Shapefile',
        ndwi_path,
        temp_contour
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    
    contours = gpd.read_file(temp_contour)
    zero_contours = contours[contours['ELEV'] == 0].copy()
    zero_contours['length'] = zero_contours.geometry.length
    
    # Get only the longest contour
    longest = zero_contours.nlargest(1, 'length')
    
    if len(longest) > 0 and longest['length'].values[0] > min_length:
        longest.to_file(output_path)
        print(f"Shoreline saved: {output_path}")
        print(f"Shoreline length: {longest['length'].values[0]:.2f} meters")
        return output_path
    else:
        print("No valid shoreline found")
        return None

if __name__ == "__main__":
    base_path = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI")
    output_base = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\PYTHON_OUTPUTS")
    aoi_file = base_path / "AOI.kml"
    
    months = [
        ("2023_04_18", "April"),
        ("2023_05_20", "May"),
        ("2023_08_24", "August")
    ]
    
    for folder_name, month_name in months:
        print(f"\n{'='*60}")
        print(f"Processing {month_name} 2023...")
        print(f"{'='*60}")
        
        # Create month-specific output folder
        output_path = output_base / folder_name
        output_path.mkdir(exist_ok=True)
        
        month_folder = base_path / folder_name
        b3_file = list(month_folder.glob("*_SR_B3.TIF"))[0]
        b5_file = list(month_folder.glob("*_SR_B5.TIF"))[0]
        
        print(f"B3: {b3_file.name}")
        print(f"B5: {b5_file.name}")
        
        ndwi_output = output_path / f"NDWI_{month_name}_2023.tif"
        calculate_ndwi(str(b3_file), str(b5_file), str(ndwi_output))
        
        ndwi_clipped = output_path / f"NDWI_{month_name}_2023_AOI.tif"
        clip_raster_to_aoi(str(ndwi_output), str(aoi_file), str(ndwi_clipped))
        
        ndwi_filled = output_path / f"NDWI_{month_name}_2023_AOI_filled.tif"
        fill_nodata(str(ndwi_clipped), str(ndwi_filled), max_distance=5)
        
        shoreline_output = output_path / f"Shoreline_{month_name}_2023.gpkg"
        extract_shoreline_by_proximity(
            str(ndwi_filled), 
            str(base_path),
            str(shoreline_output), 
            min_length=10000
        )
    
    print(f"\n{'='*60}")
    print("All months processed successfully!")
    print(f"{'='*60}")