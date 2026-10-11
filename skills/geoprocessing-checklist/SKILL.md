---
name: geoprocessing-checklist
description: Puts vector and raster geoprocessing steps in the right order and checks each result. Covers CRS checks and reprojection, fixing invalid geometries, clip, buffer, dissolve, overlay and spatial join, raster alignment before map algebra, with QGIS Processing algorithm ids, qgis_process and processing.run, PostGIS and shapely equivalents. Use when someone asks to buffer, clip, intersect, dissolve, join by location, compute areas or distances, run map algebra, chain QGIS tools, or asks why a buffer, area or overlay result looks wrong.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
---

# Geoprocessing checklist

## What goes wrong without this skill

- Buffers and areas computed in EPSG:4326 (degrees) or EPSG:3857 (inflated away from the equator).
- Overlay and dissolve steps fail or drop features because of invalid geometries.
- Layers in different CRS are clipped or joined, giving empty or shifted results.
- Rasters with different resolution, extent or nodata are combined cell by cell.
- No check between steps, so an empty or broken layer flows to the end.

## Vector order

Run the steps in this order. Skip the ones you do not need, never reorder them.

1. **Inspect**: CRS, geometry type, feature count, extent. Note the counts.
2. **Reproject** every input to one projected CRS suited to the area: the national grid (for example EPSG:2154 in France, EPSG:27700 in Great Britain) or the local UTM zone. Use an equal-area CRS for area totals over large regions.
3. **Fix geometries** on every input.
4. **Clip** or filter to the study area early, to keep later steps small.
5. **Buffer**, distance in meters (only meaningful in a projected CRS).
6. **Dissolve** if overlapping buffers or parts must merge.
7. **Overlay** (intersection, difference, union).
8. **Spatial join** to carry attributes across.
9. **Compute** areas and lengths last, in the projected CRS.

## Check after each step

| Check | How | Red flag |
|---|---|---|
| Feature count | compare with previous step | 0, or a sudden large drop |
| Extent | layer properties, `ST_Extent` | wrong place, near 0,0, degrees in a metric CRS |
| Validity | QGIS Check validity tool, `ST_IsValid`, `shapely.is_valid` | any invalid |
| Area sum | sum of `$area` before and after a dissolve | dissolve should keep the total minus overlaps |
| Nulls | count null geometries and key attributes | join produced unmatched rows |
| Geometry type | polygon stays polygon | mixed types after overlay |

## QGIS Processing ids

| Step | Algorithm id |
|---|---|
| Reproject | `native:reprojectlayer` |
| Fix geometries | `native:fixgeometries` |
| Clip | `native:clip` |
| Extract by location | `native:extractbylocation` |
| Buffer | `native:buffer` |
| Dissolve | `native:dissolve` |
| Intersection | `native:intersection` |
| Difference | `native:difference` |
| Union | `native:union` |
| Join attributes by location | `native:joinattributesbylocation` |
| Join by nearest | `native:joinbynearest` |
| Add geometry attributes | `native:exportaddgeometrycolumns` |
| Warp (reproject raster) | `gdal:warpreproject` |
| Raster calculator | `qgis:rastercalculator`, `gdal:rastercalculator` |

Confirm an id on your install: `qgis_process list | grep -i buffer`, and its parameters: `qgis_process help native:buffer`.

## Running them

Command line:

```bash
qgis_process run native:fixgeometries -- INPUT=parcels.gpkg OUTPUT=parcels_fixed.gpkg
qgis_process run native:reprojectlayer -- INPUT=parcels_fixed.gpkg TARGET_CRS=EPSG:2154 OUTPUT=parcels_2154.gpkg
qgis_process run native:buffer -- INPUT=parcels_2154.gpkg DISTANCE=50 SEGMENTS=8 DISSOLVE=false OUTPUT=buf.gpkg
```

QGIS Python console:

```python
import processing
fixed = processing.run("native:fixgeometries", {"INPUT": "parcels.gpkg", "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
proj = processing.run("native:reprojectlayer", {"INPUT": fixed, "TARGET_CRS": "EPSG:2154", "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
buf = processing.run("native:buffer", {"INPUT": proj, "DISTANCE": 50, "SEGMENTS": 8,
                                       "DISSOLVE": False, "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
print(buf.featureCount(), buf.extent().toString())
```

PostGIS:

```sql
SELECT id, ST_Buffer(ST_Transform(ST_MakeValid(geom), 2154), 50) AS geom FROM parcels;
```

GeoPandas and shapely:

```python
from shapely import make_valid
gdf["geometry"] = gdf.geometry.apply(make_valid)
gdf = gdf.to_crs(gdf.estimate_utm_crs())
gdf["geometry"] = gdf.buffer(50)
```

`make_valid` can return a GeometryCollection; keep only the polygon parts before saving to a polygon layer.

## Raster order

1. **Inspect** each raster: CRS, pixel size, extent, data type, nodata value (`gdalinfo`).
2. **Align**: same CRS, same pixel size, same grid origin and extent. Use `gdal:warpreproject` or `gdalwarp -t_srs -tr -te -tap`, or QGIS Align Rasters.
3. **Resample right**: nearest for categories (land cover, classes), bilinear or cubic for continuous values (elevation, reflectance).
4. **Set nodata** explicitly on every input, so it is not treated as 0.
5. **Map algebra** only after steps 1 to 4.
6. **Check**: min, max, mean (`gdalinfo -stats`), nodata share, visual check against the inputs.

## Before you hand the result over

- Output CRS stated, and the one the user expects.
- Format: GeoPackage, not Shapefile (field names over 10 characters are cut in Shapefile).
- Counts and area totals reported next to the input numbers.

## Script

`python3 scripts/layer_report.py data.gpkg [--layer name]` prints feature count, CRS, extent, invalid and null geometries, and total area or length in meters. Run it before and after each step and compare. Needs GDAL Python bindings or geopandas (inside QGIS, use its Python). Exit code 1 when geometries are invalid or null.

## Going further

AI Agent for QGIS runs these Processing steps from a chat inside QGIS: https://terra-lab.ai/ai-agent?utm_source=skills&utm_medium=geoai-skills&utm_campaign=geoprocessing-checklist
