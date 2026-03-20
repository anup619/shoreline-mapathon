# Shoreline Mapathon 2025 — V2

**🥈 Runner-up** — Automated Shoreline Extraction & Temporal Change Analysis
Tamil Nadu Coastline (Sayalkudi, T.Mariyur, Keelvaipar, Ervadi)

**Developed by:** Anup Bagde, CDAC Pune
**Supervised by:** Girishchandra Yendargaye, CDAC Pune

---

## What's New in V2

| Feature | V1 | V2 |
|---|---|---|
| Months processed | 3 | 7 |
| Cloud masking | Manual | Automated via QA_PIXEL |
| NDWI threshold | Fixed 0.0 | Adaptive Otsu |
| NoData fill distance | Fixed 5px | Adaptive 20–60px |
| Auto skip cloudy months | No | Yes (>30% threshold) |
| Tidal data | Not used | Recorded as metadata with flags |
| Visualization | Static PNG | Interactive 3D web app |

---

## Project Structure

```
shoreline-mapathon/
  pipeline/
    shoreline_extraction_v2.py        # Main extraction pipeline
    calculate_transect_distances_v2.py # Transect change detection
    generate_summary_v2.py            # Summary report generation
    convert_to_geojson.py             # GeoJSON + transect export for viz app
  shoreline-viz/                      # React visualization app
  README.md
```

---

## Pipeline

### Prerequisites

- Python 3.10+
- Conda/Miniconda
- OSGeo4W (for `gdal_contour`)

### Installation

```bash
conda create -n shoreline python=3.10 -y
conda activate shoreline
conda install -c conda-forge rasterio geopandas gdal numpy shapely pandas -y
```

### Data Setup

Satellite imagery is NOT included due to size constraints.

**Download the dataset:**
```
https://tnthub1-my.sharepoint.com/:f:/g/personal/vasanthan_tnthub_org/IgDSE51zhfgTQaLH7yx5ODFGAW7c60SS618b6zp78LTCK9g?e=0sYtpu
```

**Expected folder structure after extraction:**
```
SHORELINE_DATA/
  SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI/
    2023_02_21/    # February — LC0*_SR_B3.TIF, LC0*_SR_B5.TIF, LC0*_QA_PIXEL.TIF
    2023_04_18/    # April
    2023_05_20/    # May
    2023_06_29/    # June
    2023_07_15/    # July
    2023_08_24/    # August
    2023_12_14/    # December
    AOI.kml
    *.kml          # Beach reference points
```

Update `BASE_PATH` and `OUTPUT_BASE` in each script to match your local paths.

### Running the Pipeline

```bash
cd pipeline

# Step 1 — Extract shorelines for all 7 months
python shoreline_extraction_v2.py

# Step 2 — Calculate transect distances between months
python calculate_transect_distances_v2.py

# Step 3 — Generate summary with tidal metadata
python generate_summary_v2.py

# Step 4 — Export GeoJSON for visualization app
python convert_to_geojson.py
```

**Processing time:** ~45 minutes total (~6 min per scene)

### Pipeline Outputs

Located in `PYTHON_OUTPUTS_V2/`:

| Output | Description |
|---|---|
| `{date}/NDWI_{month}_2023.tif` | NDWI raster |
| `{date}/NDWI_{month}_2023_AOI_filled.tif` | Cloud-filled NDWI |
| `{date}/Shoreline_{month}_2023.gpkg` | Extracted shoreline vector |
| `Processing_Log.csv` | Cloud %, NDWI threshold, status per month |
| `Automated_Transect_Distances_V2.csv` | Change detection results |
| `Final_Summary_V2.csv` | Combined summary with tidal flags |
| `geojson/shorelines.geojson` | All shorelines for viz app |
| `geojson/beach_points.geojson` | Beach reference points for viz app |
| `geojson/transects.json` | Pre-computed transect geometry for viz app |
| `geojson/appData.json` | Tidal + change data for viz app |

---

## Key Results (V2)

| Month | Cloud Cover | NDWI Threshold | Shoreline Length |
|---|---|---|---|
| February | 10.33% | -0.0902 | 183,164 m |
| April | 0.95% | -0.0902 | 316,946 m |
| May | 0.84% | -0.0980 | 283,894 m |
| June | 0.08% | -0.0902 | 348,668 m |
| July | 0.05% | -0.0745 | 261,958 m |
| August | 0.14% | -0.0745 | 243,840 m |
| December | 4.51% | -0.1137 | 302,301 m |

**Tidal note:** December MTL (0.725m) is +0.171m above reference mean (0.554m). Aug–Dec change values at Ervadi (12.72m) and Sayalkudi (6.39m) may partially reflect tidal position rather than purely coastal change. Spatial tidal correction not applied — microtidal coast (range 0.3–0.9m), horizontal correction < 30m Landsat pixel size.

---

## Visualization App

An interactive 3D web app for exploring the extracted shorelines and change data.

### Stack

| Layer | Technology |
|---|---|
| Build tool | Vite + React |
| 3D map | deck.gl + MapLibre GL |
| Charts | Recharts |
| Styling | Tailwind CSS |
| Data | Pre-computed GeoJSON |

### Views

**Map View**
- 7 monthly shorelines as toggleable colored layers
- 3D mode — shorelines stacked temporally at different elevations
- Location pin markers with change stats popup on click

**Change Chart**
- Bar chart of shoreline displacement per time period
- MTL tidal overlay as secondary line
- December tidal flag warning

**Transect Visualizer**
- Zoomed map showing perpendicular transect at selected beach
- Reference shoreline (dashed) vs comparing shoreline (solid)
- Yellow displacement segment with distance label
- Animate mode — fixed reference month, cycles through all others

### Running the App

```bash
cd shoreline-viz
npm install
npm run dev
```

Open `http://localhost:5173`

**Before running** — copy the generated GeoJSON files into `public/`:
```
shoreline-viz/public/geojson/
  shorelines.geojson
  beach_points.geojson
  transects.json
  appData.json
```

These are generated by `convert_to_geojson.py` in Step 4 of the pipeline.

---

## Methodology

1. **Cloud masking** — QA_PIXEL band bits 3 (cloud) and 4 (shadow) masked before processing
2. **NDWI calculation** — `(Green - NIR) / (Green + NIR)` using SR B3 and B5
3. **AOI clipping** — Focus on coastal zone defined by `AOI.kml`
4. **Adaptive NoData fill** — Fill distance scales with cloud coverage (20–60px)
5. **Otsu thresholding** — Adaptive NDWI threshold per scene replaces fixed 0.0
6. **Contour extraction** — `gdal_contour` at Otsu threshold
7. **Proximity filtering** — Select contour nearest to beach reference KML points, min length 10km
8. **Transect change detection** — Perpendicular transects at beach reference points measure positional shift
9. **Tidal metadata** — HTL/LTL/MTL recorded per date, MTL deviation flagged, spatial correction deferred

---

## Troubleshooting

**`FileNotFoundError`** — Check `BASE_PATH` and `OUTPUT_BASE` in each script match your data location

**`ModuleNotFoundError`** — Run `conda activate shoreline`

**`gdal_contour` not found** — Update the path in `shoreline_extraction_v2.py` to your OSGeo4W installation

**Blank map in viz app** — Ensure GeoJSON files are copied to `shoreline-viz/public/geojson/`

---

## Contact

**Developer:** Anup Bagde (anupb@cdac.in)
**Supervisor:** Girishchandra Yendargaye (girishy@cdac.in)
**Institution:** Centre for Development of Advanced Computing (CDAC), Pune

---

*Mapathon 2025 — SGE, Anna University × iTNT Hub*