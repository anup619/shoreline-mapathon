import rasterio
import numpy as np
from rasterio.mask import mask
from rasterio.fill import fillnodata
import geopandas as gpd
from shapely.geometry import shape
import os
import subprocess
import tempfile
from pathlib import Path
import pandas as pd

MONTHS = [
    ("2023_02_21", "February"),
    ("2023_04_18", "April"),
    ("2023_05_20", "May"),
    ("2023_06_29", "June"),
    ("2023_07_15", "July"),
    ("2023_08_24", "August"),
    ("2023_12_14", "December"),
]

CLOUD_SKIP_THRESHOLD = 30

MIN_SHORELINE_LENGTH = 10000

BASE_PATH = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI")
OUTPUT_BASE = Path(r"D:\shoreline-mapathon\SHORELINE_DATA\PYTHON_OUTPUTS_V2")
AOI_FILE = BASE_PATH / "AOI.kml"

def apply_cloud_mask(b3_path, b5_path, qa_path, output_b3_path, output_b5_path):
    with rasterio.open(qa_path) as qa_src:
        qa = qa_src.read(1).astype('uint16')
        profile =  qa_src.profile.copy()

    cloud_mask = ((qa >> 3) & 1).astype(bool)
    shadow_mask = ((qa >> 4) & 1).astype(bool)
    combined_mask = cloud_mask | shadow_mask

    for band_path , output_path in [(b3_path, output_b3_path), (b5_path, output_b5_path)]:
        with rasterio.open(band_path) as src:
            data = src.read(1).astype('float32')
            band_profile = src.profile.copy()
            band_profile.update(dtype=rasterio.float32, nodata=-9999)

        data[combined_mask] = -9999

        with rasterio.open(output_path, 'w', **band_profile) as dst:
            dst.write(data, 1)

    print(f"Cloud mask applied - B3 and B5 masked")
    return output_b3_path, output_b5_path

def calculate_cloud_coverage(qa_path, aoi_path):
    aoi = gpd.read_file(aoi_path)

    with rasterio.open(qa_path) as src:
        aoi_reprojected = aoi.to_crs(src.crs)
        geoms = [shape(geom) for geom in aoi_reprojected.geometry]
        qa_clipped, _ = mask(src, geoms, crop=True)
        qa_clipped = qa_clipped[0].astype('uint16')

    cloud_mask = ((qa_clipped >> 3) & 1).astype(bool)
    shadow_mask = ((qa_clipped >> 4) & 1).astype(bool)
    combined = cloud_mask | shadow_mask

    fill_mask = (qa_clipped == 1) | (qa_clipped == 0)
    valid_pixels = np.sum(~fill_mask)
    cloud_pixels = np.sum(combined &~fill_mask)

    if valid_pixels == 0:
        return 100.0
    
    coverage = (cloud_pixels / valid_pixels) * 100
    return round(coverage, 2)

def calculate_ndwi(b3_path, b5_path, output_path):
    with rasterio.open(b3_path) as b3_src:
        b3 = b3_src.read(1).astype('float32')
        profile = b3_src.profile.copy()
        nodata_val =  b3_src.nodata if b3_src.nodata else -9999

    with rasterio.open(b5_path) as b3_src:
        b5 = b3_src.read(1).astype('float32')

    valid = (b3 != nodata_val) & (b5 != nodata_val) & (b3+b5 != 0)
    ndwi = np.full(b3.shape, -9999, dtype='float32')
    ndwi[valid] = (b3[valid] - b5[valid]) / (b3[valid] + b5[valid] + 1e-10)

    profile.update(dtype=rasterio.float32, count=1, nodata=-9999)

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(ndwi, 1)

    print(f"NDWI calculated: {output_path}")
    return output_path

def clip_raster_to_aoi(raster_path, aoi_path, output_path):
    aoi = gpd.read_file(aoi_path)

    with rasterio.open(raster_path) as src:
        aoi_projected = aoi.to_crs(src.crs)
        geoms = [shape(geom) for geom in aoi_projected.geometry]
        out_image, out_transform = mask(src, geoms, crop=True, nodata=-9999)
        out_meta = src.meta.copy()
        out_meta.update({
            "height" : out_image.shape[1],
            "width" : out_image.shape[2],
            "transform" : out_transform,
            "nodata" : -9999
        })

        with rasterio.open(output_path, 'w', **out_meta) as dst:
            dst.write(out_image)

    print(f"Raster clipped to AOI : {output_path}")
    return output_path

def fill_nodata_adative(input_path, output_path, cloud_coverage_pct):
    if cloud_coverage_pct < 15:
        max_distance = 20
    elif cloud_coverage_pct < 30:
        max_distance = 40
    else:
        max_distance = 60
    
    print(f"Cloud coverage: {cloud_coverage_pct}% - using fill distance: {max_distance}px")

    with rasterio.open(input_path) as src:
        data = src.read(1).astype('float32')
        profile = src.meta.copy()
        nodata_val = src.nodata if src.nodata else -9999

    valid_mask = data != nodata_val

    filled = fillnodata(data, valid_mask, max_search_distance=max_distance)

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(filled, 1)
    
    print(f"NoData filled: {output_path}")
    return output_path

def calculate_otsu_threshold(ndwi_path):
    with rasterio.open(ndwi_path) as src:
        data = src.read(1).astype('float32')
        nodata_val = src.nodata if src.nodata else -9999

    valid_data = data[data != nodata_val]

    scaled = ((valid_data + 1) / 2 * 255).astype('uint8')

    hist, bin_edges = np.histogram(scaled, bins=256, range=(0,255))
    hist = hist.astype('float64')
    total = hist.sum()

    current_max = 0
    threshold = 0
    sum_total = np.sum(np.arange(256) * hist)
    sum_bg = 0
    weight_bg = 0

    for i in range(256):
        weight_bg += hist[i]
        if weight_bg == 0:
            continue

        weight_fg = total - weight_bg
        if weight_fg == 0:
            break

        sum_bg += i * hist[i]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg

        variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2

        if variance > current_max:
            current_max = variance
            threshold = i
    
    otsu_ndwi = (threshold / 255) * 2 - 1
    print(f"Otsu threshold calculated: {otsu_ndwi:.4f} (vs fixed 0.0)")
    return otsu_ndwi

def extract_shoreline_by_proximity(ndwi_path, beach_points_dir, output_path, threshold=0.0, min_length=10000):
    temp_dir = tempfile.gettempdir()
    temp_contour = os.path.join(temp_dir, "temp_contours_v2.shp")

    offset = round(threshold % 0.1, 4)

    cmd = [
        r'C:\OSGeo4W\bin\gdal_contour.exe',
        '-b', '1',
        '-a', 'ELEV',
        '-i', '0.1',
        '-off', str(offset),
        '-f', 'ESRI Shapefile',
        ndwi_path,
        temp_contour
    ]

    result = subprocess.run(cmd, check=True, capture_output=True)

    beach_files = list(Path(beach_points_dir).glob("*Beach.kml")) + \
                  list(Path(beach_points_dir).glob("*beach.kml"))
    
    if not beach_files:
        print("Warning: No beach KML files found")
        return None
    
    all_points = []
    for bf in beach_files:
        pts = gpd.read_file(bf)
        all_points.append(pts)

    beach_points = gpd.GeoDataFrame(pd.concat(all_points, ignore_index=True))

    if not os.path.exists(temp_contour):
        print("No contours generated")
        return None
    
    contours = gpd.read_file(temp_contour)

    contours['dist_to_threshold'] = abs(contours['ELEV'] - threshold)
    threshold_contours = contours[contours['dist_to_threshold'] < 0.05].copy()

    if len(threshold_contours) == 0:
        print(f"No contours found near threshold {threshold:.4f}")
        return None
    
    threshold_contours['length'] = threshold_contours.geometry.length

    valid_contours = threshold_contours[threshold_contours['length'] > min_length].copy()

    if len(valid_contours) == 0:
        print(f"No contours longer than {min_length}m found")
        return None
    
    beach_points_proj = beach_points.to_crs(valid_contours.crs)

    valid_contours['min_dist_to_beach'] = valid_contours.geometry.apply(
        lambda geom: min([geom.distance(pt) for pt in beach_points_proj.geometry])
    )

    best_shoreline = valid_contours.nsmallest(1, 'min_dist_to_beach')
    best_shoreline.to_file(output_path, driver='GPKG')

    print(f"Shoreline saved: {output_path}")
    print(f"Shoreline length: {best_shoreline['length'].values[0]:.2f} meters")
    print(f"Distance to nearest beach point: {best_shoreline['min_dist_to_beach'].values[0]:.2f} meters")
    print(f"NDWI threshold used: {threshold:.4f}")

    return output_path

if __name__ == "__main__":

    OUTPUT_BASE.mkdir(exist_ok=True)

    results_log = []

    for folder_name, month_name in MONTHS:
        print(f"\n{'='*60}")
        print(f"Processing {month_name} 2023...")
        print(f"{'='*60}")

        month_folder = BASE_PATH / folder_name
        output_path = OUTPUT_BASE / folder_name
        output_path.mkdir(exist_ok=True)

        b3_files = list(month_folder.glob("*_SR_B3.TIF"))
        b5_files = list(month_folder.glob("*_SR_B5.TIF"))
        qa_files = list(month_folder.glob("*_QA_PIXEL.TIF"))

        if not b3_files or not b5_files or not qa_files:
            print(f"Missing input files for {month_name} - skipping")
            continue

        b3_file = b3_files[0]
        b5_file = b5_files[0]
        qa_file = qa_files[0]

        print(f"B3: {b3_file.name}")
        print(f"B5: {b5_file.name}")
        print(f"QA: {qa_file.name}")

        cloud_pct = calculate_cloud_coverage(str(qa_file), str(AOI_FILE))
        print(f"Cloud coverage in AOI: {cloud_pct}%")

        if cloud_pct > CLOUD_SKIP_THRESHOLD:
            print(f"Cloud coverage {cloud_pct}% exceeds threshold {CLOUD_SKIP_THRESHOLD}% - skipping {month_name}")
            results_log.append({
                'Month' : month_name,
                'Status' : 'Skipped',
                'Cloud Coverage (%)' : cloud_pct,
                'Shoreline Length (m)' : None,
                'NDWI Threshold' : None
            })
            continue

        b3_masked = output_path / f"B3_masked_{month_name}.tif"
        b5_masked = output_path / f"B5_masked_{month_name}.tif"
        apply_cloud_mask(str(b3_file), str(b5_file), str(qa_file),
                         str(b3_masked), str(b5_masked))
        
        ndwi_output = output_path / f"NDWI_{month_name}_2023.tif"
        calculate_ndwi(str(b3_masked), str(b5_masked), str(ndwi_output))

        ndwi_clipped = output_path / f"NDWI_{month_name}_2023_AOI.tif"
        clip_raster_to_aoi(str(ndwi_output), str(AOI_FILE), str(ndwi_clipped))

        ndwi_filled = output_path / f"NDWI_{month_name}_2023_AOI_filled.tif"
        fill_nodata_adative(str(ndwi_clipped), str(ndwi_filled), cloud_pct)

        otsu_threshold = calculate_otsu_threshold(str(ndwi_filled))

        shoreline_output = output_path / f"Shoreline_{month_name}_2023.gpkg"
        result = extract_shoreline_by_proximity(
            str(ndwi_filled),
            str(BASE_PATH),
            str(shoreline_output),
            threshold=otsu_threshold,
            min_length=MIN_SHORELINE_LENGTH
        )

        if result:
            sl = gpd.read_file(shoreline_output)
            sl_length = round(sl.geometry.length.sum(), 2)
            status = 'Success'
        else:
            sl_length = None
            status = 'Failed'

        results_log.append({
            'Month' : month_name,
            'Status': status,
            'Cloud Coverage (%)' : cloud_pct,
            'Shoreline Length (m)': sl_length,
            'NDWI Threshold': round(otsu_threshold, 4)
        })

    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE - SUMMARY")
    print(f"{'='*60}")
    log_df = pd.DataFrame(results_log)
    print(log_df.to_string(index=False))

    log_df.to_csv(OUTPUT_BASE / "Processing_Log.csv", index=False)
    print(f"\nProcessing log saved to: {OUTPUT_BASE / 'Processing_Log.csv'}")
    print(f"{'='*60}")