# Automated Shoreline Extraction System

Multi-temporal coastal monitoring using NDWI-based shoreline detection from Landsat satellite imagery.

---

## Project Overview

**Objective:** Automated extraction and change analysis of shorelines from satellite imagery

**Study Area:** Sayalkudi, T.Mariyur, Keelvaipar, Ervadi Beaches, Tamil Nadu, India

**Time Period:** April, May, August 2023

**Developed by:** Anup Bagde, CDAC Pune  
**Supervised by:** Girishchandra Yendargaye, CDAC Pune

---

## Quick Start

### Prerequisites

- Python 3.10+
- Conda/Miniconda

### Installation
```bash
# Create environment
conda create -n shoreline python=3.10 -y
conda activate shoreline

# Install dependencies
conda install -c conda-forge rasterio geopandas gdal numpy shapely pandas -y
```

### Data Setup

**IMPORTANT:** Satellite imagery is NOT included in this submission due to size constraints.

### Data Setup

**IMPORTANT:** Satellite imagery is NOT included in this submission due to size constraints.

**Download Required Data:**

1. **Download the complete dataset** from the provided link:
```
https://tnthub1-my.sharepoint.com/:f:/g/personal/vasanthan_tnthub_org/IgDSE51zhfgTQaLH7yx5ODFGAW7c60SS618b6zp78LTCK9g?e=0sYtpu
```

2. **Extract the downloaded archive**

3. **Locate the data folder:**
```
   SHORELINE_DATA/SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI/
```
   This folder contains:
   - `2023_04_18/` - April Landsat scene with all bands
   - `2023_05_20/` - May Landsat scene with all bands
   - `2023_08_24/` - August Landsat scene with all bands
   - `AOI.kml` - Study area polygon
   - `*Beach.kml` - Beach reference point files (4 locations)

4. **Place the entire `SHORELINE_DATA` folder** in your project directory:
```
   SHORELINE_DATA/
    └── SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI/
        ├── 2023_04_18/
        ├── 2023_05_20/
        ├── 2023_08_24/
        ├── AOI.kml
        └── *.kml
```

**Required Files per Date:**
- `LC0*_SR_B3.TIF` (Green band)
- `LC0*_SR_B5.TIF` (NIR band)
- Other Landsat bands and metadata (included but not used in current version)

**Reference Data:**
- All reference data (AOI, beach points, tidal data) is included in the download

### Running the Analysis
```bash
# Navigate to project directory
cd SHORELINE

# Run complete automated workflow (all 3 months)
python shoreline_extraction.py

# Calculate shoreline change at beach points
python calculate_transect_distances.py

# Generate summary statistics
python generate_summary.py
```

**Processing Time:** ~15 minutes total (5 min per scene)

---

## Outputs

### Automated Results
Located in `SHORELINE_DATA/PYTHON_OUTPUTS/`:
- **NDWI Rasters:** Water index for each date
- **Shoreline Vectors:** Extracted coastlines (.gpkg format)

### Analysis Results
Located in project root:
- `Automated_Transect_Distances.csv` - Change measurements at beach points
- `Final_Summary.csv` - Combined statistics
- `Shoreline_Map_2023.png` - Multi-temporal visualization

### Manual QGIS Results
Located in `SHORELINE_DATA/OUTPUTS/`:
- Validation extractions performed in QGIS

---

## File Structure
```
SHORELINE/
├── shoreline_extraction.py          # Main pipeline
├── calculate_transect_distances.py  # Change detection
├── generate_summary.py              # Statistics
├── Shoreline.qgz                    # QGIS project
├── Shoreline_Map_2023.png           # Final map
├── *.csv                            # Results tables
│
└── SHORELINE_DATA/
    ├── SAYALKUDI,T.MARIYUR,KEELVAIPAR,ERVADI/  # [ADD LANDSAT DATA HERE]
    │   ├── 2023_04_18/              # April Landsat scene
    │   ├── 2023_05_20/              # May Landsat scene
    │   ├── 2023_08_24/              # August Landsat scene
    │   ├── AOI.kml                  # Study area
    │   └── *Beach.kml               # Reference points
    │
    ├── OUTPUTS/                     # Manual QGIS results
    └── PYTHON_OUTPUTS/              # Automated results
```

---

## Methodology Summary

1. **NDWI Calculation:** `(Green - NIR) / (Green + NIR)` separates water from land
2. **AOI Clipping:** Focus on coastal zone
3. **NoData Filling:** Ensure shoreline continuity
4. **Contour Extraction:** NDWI = 0 line is the shoreline
5. **Proximity Filtering:** Select coastline nearest to beach reference points
6. **Change Analysis:** Measure positional shifts at validation locations

**Full methodology documented in:** `Mapathon_Submission.pdf`

---

## Key Results

| Month | Shoreline Length | Processing Time |
|-------|------------------|-----------------|
| April 2023 | 99,720 m | 4 min 32 sec |
| May 2023 | 96,501 m | 4 min 18 sec |
| August 2023 | 97,358 m | 4 min 41 sec |

**Maximum shoreline change detected:** 10.69 meters (Keelvaipar Beach, Apr-May)

---

## Troubleshooting

**Issue:** `FileNotFoundError` when running scripts

**Solution:** Ensure Landsat data is placed in correct folders (see Data Setup)

**Issue:** `ModuleNotFoundError`

**Solution:** Activate conda environment: `conda activate shoreline`

**Issue:** GDAL warnings about missing data files

**Solution:** These are harmless warnings; processing will complete successfully

---

## Contact

**Developer:** Anup Bagde (anupb@cdac.in)  
**Supervisor:** Girishchandra Yendargaye (girishy@cdac.in)  
**Institution:** CDAC Pune

---

**Mapathon 2025 Submission**  
Centre for Development of Advanced Computing (CDAC), Pune