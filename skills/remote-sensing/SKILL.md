---
name: remote-sensing
description: Picks satellite imagery and processes it correctly as ordered workflows with checks. Covers choosing Sentinel-2, Landsat, Sentinel-1 SAR, DEMs and orthophotos, STAC search on Earth Search and Planetary Computer, Sentinel-2 and Landsat reflectance scale and offsets (processing baseline 04.00, Collection 2 Level-2), cloud masks (SCL, QA_PIXEL, Cloud Score+), composites, NDVI, NDWI, NDMI, NBR and other indices, Google Earth Engine collection ids, scale factors and reduceRegion scale, change detection (dNBR, NDVI difference), land cover classification with training samples and a confusion matrix, and raster operations in QGIS and GDAL (clip by mask, warp, raster calculator, alignment). Use when the user asks for NDVI or another index, satellite images of an area, a cloud-free composite, Sentinel-2 or Landsat in QGIS, rasterio or Earth Engine, burn severity, before and after change, a land cover map, accuracy assessment, or to clip, reproject or combine rasters.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
  version: "1.1.0"
---

# Remote sensing

Each workflow below is ordered; run the check after each step. Most wrong answers in remote sensing come from a skipped step (no cloud mask, offset forgotten, rasters not aligned), not from the formula.

## Always first

1. **Inspect** each raster: `gdalinfo -stats file.tif`. Note CRS, pixel size, band count and order, data type, NoData, min and max. Integer values in the thousands mean DN, not reflectance.
2. **Frame**: which area (exact boundary), which dates or season, which sensor resolution is enough for the smallest object, and which product the user expects (map, statistic, time series). Ask when the area or the period is missing. When the imagery cannot answer (single trees on 10 m pixels, a date before the sensor existed), say so and propose what can.
3. **Return the code** that was run, with dataset ids, dates and thresholds, so the user can rerun it.

## Workflow index

| Task | Where |
| --- | --- |
| Which imagery for this job, where to download it | [Choose imagery](#choose-imagery), [references/imagery-sources.md](references/imagery-sources.md) |
| Sentinel-2 or Landsat to reflectance, cloud masks | [Reflectance and masks](#reflectance-and-masks), [references/optical-reflectance.md](references/optical-reflectance.md) |
| NDVI, NDWI, NDMI, NDBI, NBR, EVI | [Indices](#indices) |
| Cloud-free composite for a season | [Composites](#composites) |
| Earth Engine scripts | [references/earth-engine.md](references/earth-engine.md) |
| Burn severity, before and after, change map | [references/change-and-sar.md](references/change-and-sar.md) |
| Sentinel-1 SAR (floods, through clouds) | [references/change-and-sar.md](references/change-and-sar.md#sentinel-1-sar-basics) |
| Land cover map, training samples, accuracy | [references/classification.md](references/classification.md) |
| Clip, reproject, align, raster calculator | [Raster operations](#raster-operations-in-qgis-and-gdal) |
| Slope, hillshade, watershed from a DEM | the `spatial-analysis` skill (terrain and hydrology) |

## Choose imagery

| Need | Source | Pixel |
| --- | --- | --- |
| Vegetation, water, crops, burn scars since 2015 | Sentinel-2 L2A | 10 to 20 m |
| History before 2015, thermal | Landsat Collection 2 Level-2 (Landsat 5, 7, 8, 9) | 30 m |
| Cloudy regions, floods, night, ships | Sentinel-1 GRD or RTC (SAR) | 10 m |
| Terrain | Copernicus DEM GLO-30 (surface model, EGM2008 heights), national lidar | 30 m, 1 to 5 m |
| Buildings, single trees, cars | national orthophotos (IGN BD ORTHO, NAIP), not Sentinel-2 | 0.2 to 1 m |

Rule: the smallest object must span at least 3 to 5 pixels to be detected. Never analyze basemap tiles (Google, Bing, Esri): their terms forbid it and the capture date is unknown. Catalogs, collection ids, licenses and a STAC search example: [references/imagery-sources.md](references/imagery-sources.md).

## Reflectance and masks

Convert DN to reflectance once, mask clouds, then compute. Details and code: [references/optical-reflectance.md](references/optical-reflectance.md).

| Product | Reflectance | Cloud mask |
| --- | --- | --- |
| Sentinel-2 L2A, processing baseline 04.00+ (from 25 January 2022), raw DN | `(DN - 1000) / 10000` | SCL: mask 0, 1, 3, 8, 9, 10, 11 |
| Sentinel-2 L2A before baseline 04.00, or a harmonized collection (Earth Engine `S2_SR_HARMONIZED`) | `DN / 10000` | SCL, or Cloud Score+ in Earth Engine |
| Landsat Collection 2 Level-2 surface reflectance (`SR_B*`) | `DN * 0.0000275 - 0.2` | `QA_PIXEL` bits 1 dilated cloud, 2 cirrus, 3 cloud, 4 cloud shadow (5 snow) |
| Landsat Collection 2 Level-2 surface temperature (`ST_B10`, `ST_B6`) | `DN * 0.00341802 + 149.0` kelvin | same |

Checks: DN 0 is NoData, not dark; clear water NIR reflectance is near 0 to 0.05 and dense vegetation NIR 0.3 to 0.5; a water median above 0.1 means an offset was missed. Run `python3 scripts/s2_offset_check.py ITEM_JSON_OR_URL` on a Sentinel-2 STAC item to get the right formula.

## Indices

Compute on float reflectance, after masking, with all bands on one grid.

| Index | Sentinel-2 | Landsat 8/9 | Notes |
| --- | --- | --- | --- |
| NDVI | (B8 - B4) / (B8 + B4) | (B5 - B4) / (B5 + B4) | water below 0, bare soil about 0.1 to 0.2, dense vegetation 0.6 to 0.9 |
| NDWI (McFeeters), open water | (B3 - B8) / (B3 + B8) | (B3 - B5) / (B3 + B5) | water above 0 |
| NDMI (Gao NDWI), vegetation water | (B8A - B11) / (B8A + B11) | (B5 - B6) / (B5 + B6) | "NDWI" is ambiguous: say which |
| NDBI, built-up | (B11 - B8) / (B11 + B8) | (B6 - B5) / (B6 + B5) | |
| NBR, burn | (B8A - B12) / (B8A + B12) | (B5 - B7) / (B5 + B7) | |
| EVI | 2.5 (B8 - B4) / (B8 + 6 B4 - 7.5 B2 + 1) | 2.5 (B5 - B4) / (B5 + 6 B4 - 7.5 B2 + 1) | needs reflectance 0 to 1, not DN |

Landsat band numbers above are for Landsat 8 and 9 OLI; Landsat 4, 5 and 7 differ (red B3, NIR B4, SWIR1 B5, SWIR2 B7). A normalized index outside -1 to 1 means DN were not converted, NoData entered the math, or integer division was used. `python3 scripts/indices.py` prints Sentinel-2 formulas and computes one from band files.

## Composites

1. Filter by area, dates (same season across years), and scene cloud cover as a first cut only.
2. Mask clouds per pixel (step above), then reduce: median for a clean picture, a percentile or max-NDVI (greenest pixel) for vegetation peaks.
3. Never mix harmonized and non-harmonized Sentinel-2, or Landsat 7 with 8 without noting the sensor difference.
4. Check: count of valid observations per pixel (Earth Engine `.count()`, or a sum of masks). Pixels with 0 or 1 observation are unreliable; report the share.

## Raster operations in QGIS and GDAL

| Operation | QGIS id | GDAL command |
| --- | --- | --- |
| Clip to a polygon | `gdal:cliprasterbymasklayer` (INPUT, MASK, CROP_TO_CUTLINE, KEEP_RESOLUTION, NODATA) | `gdalwarp -cutline aoi.gpkg -crop_to_cutline -dstnodata 0 in.tif out.tif` |
| Reproject, resample | `gdal:warpreproject` (TARGET_CRS, RESAMPLING, TARGET_RESOLUTION) | `gdalwarp -t_srs EPSG:32631 -tr 10 10 -r bilinear in.tif out.tif` |
| Align to a reference grid | `native:alignsingleraster` (REFERENCE_LAYER), `native:alignrasters` | `gdalwarp -te xmin ymin xmax ymax -tr 10 10 -tap ...` |
| Raster calculator | `native:rastercalc` (LAYERS, EXPRESSION), `gdal:rastercalculator` | `gdal_calc.py -A b8.tif -B b4.tif --calc="(A-B)/(A+B)" --type=Float32` |
| Mosaic | `gdal:merge`, `gdal:buildvirtualraster` | `gdalbuildvrt`, `gdal_merge.py` |
| Convert, compress, COG | `gdal:translate` | `gdal_translate -of COG in.tif out.tif` |

Verified on 2026-10-11 against QGIS 3.44 (`qgis_process help`).

Rules:
- Resampling: nearest for classes (land cover, SCL, masks), bilinear or cubic for continuous values (reflectance, elevation).
- Set NoData explicitly before math, or NoData pixels are computed as 0.
- Integer inputs: cast or write Float32 output (`--type=Float32` in gdal_calc), or a ratio truncates to 0.
- Clip with a mask in the raster's CRS when possible; otherwise the cutline is reprojected on the fly, which is fine, but check the output extent.
- After any operation, compare `gdalinfo -stats` of input and output: same value range, expected pixel size, expected extent.

## Before handing over a result

- [ ] Dataset ids, dates, cloud thresholds and the reflectance formula stated.
- [ ] Clouds masked and the share of valid pixels reported.
- [ ] Value range checked against the index ranges above.
- [ ] Output looked at: a PNG or a QGIS screenshot with a sensible color ramp, over the right place.
- [ ] Attribution line, for example "Contains modified Copernicus Sentinel data 2025" or "Landsat imagery courtesy of the U.S. Geological Survey".

## Scripts

- `python3 scripts/s2_offset_check.py ITEM_JSON_OR_URL`: reads a Sentinel-2 STAC item and prints the reflectance formula to use and why (stdlib only).
- `python3 scripts/indices.py [ndvi]`: prints Sentinel-2 index formulas; `--band B04=red.tif --band B08=nir.tif -o ndvi.tif` computes one (numpy and rasterio, inputs in reflectance).
- `python3 scripts/accuracy.py matrix.csv`: overall accuracy, kappa, producer's and user's accuracy from a confusion matrix, or `--pairs ref_pred.csv` from reference and predicted labels (stdlib only).

## Going further

AI Agent for QGIS fetches Sentinel-2 and Landsat scenes and computes indices from a chat inside QGIS: https://terra-lab.ai/ai-agent?utm_source=skills&utm_medium=geoai-skills&utm_campaign=remote-sensing
