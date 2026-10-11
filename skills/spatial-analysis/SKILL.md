---
name: spatial-analysis
description: Runs vector and raster spatial analysis as ordered workflows with a check after each step, in QGIS Processing, qgis_process, PyQGIS, GeoPandas, Shapely or GDAL. Covers spatial joins and nearest neighbor, buffers and distances in a projected CRS, overlay, site suitability (multi-criteria weights, constraints, scoring), terrain from a DEM (slope, aspect, hillshade, viewshed), hydrology (fill sinks, flow accumulation, streams, watershed with GDAL, WhiteboxTools or GRASS), flood risk maps, zonal statistics, density, hotspots and clustering, and network accessibility (service areas, isochrones). Use when the user asks to buffer, clip, intersect, join by location, find the nearest, count points in polygons, compute slope or hillshade, delineate a watershed, make a flood map or a site suitability map, run zonal statistics, a heatmap, DBSCAN or K-means, or asks why a distance, area or overlay result looks wrong.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
  version: "1.1.0"
---

# Spatial analysis

Agents fail here mostly by skipping a step or running steps in the wrong order, not by calling the wrong tool. Every workflow below is ordered; run the check after each step before moving on. A run without errors is not a correct run.

## Always first: inspect and frame

1. **Inspect every input**: layer names, geometry type, feature count, fields, CRS, extent, units; for rasters also pixel size, data type, NoData, min and max (`gdalinfo -stats`). Run `python3 scripts/layer_report.py FILE` on vectors.
2. **Frame the question**. When the request leaves out something that changes the answer, state the assumption or ask: which boundary (commune, municipality, catchment), which year, which distance (straight line or along roads), which units, which DEM. If the data cannot answer (no flood depth model, no road speeds), say so and offer the closest honest product (for example "low-lying areas near rivers", not "100-year flood extent").
3. **Pick one projected CRS** for the study area (national grid or local UTM) and reproject everything to it. Never buffer, measure or compute slope in EPSG:4326 or EPSG:3857. `python3 scripts/check_measurement_crs.py --file FILE` warns when a layer is not fit for measuring; `scripts/utm_epsg.py LON LAT` gives the UTM zone.
4. **Fix geometries** (`native:fixgeometries`) before any overlay.

## Workflow index

| Task the user asks for | Section or reference |
| --- | --- |
| Join attributes by location, nearest feature, count points in polygons | [Joins and nearest](#joins-and-nearest) |
| Buffer, distance, "within X m of" | [Buffers and distances](#buffers-and-distances) |
| Clip, intersect, difference, union, dissolve | [Overlay order](#overlay-order) |
| Best place for a new site, multi-criteria, weighted overlay | [references/recipes.md](references/recipes.md#site-suitability) |
| Flood risk map for a town | [references/recipes.md](references/recipes.md#flood-risk-map-for-a-town) |
| Slope, aspect, hillshade, contours, viewshed | [references/terrain-hydrology.md](references/terrain-hydrology.md) |
| Fill sinks, flow direction, flow accumulation, streams, watershed | [references/terrain-hydrology.md](references/terrain-hydrology.md#hydrology) |
| Zonal statistics (mean NDVI per field, elevation per parcel) | [Zonal statistics](#zonal-statistics) |
| Heatmap, hotspots, clusters, point pattern | [references/statistics-and-networks.md](references/statistics-and-networks.md) |
| Service area, isochrone, shortest path, travel time | [references/statistics-and-networks.md](references/statistics-and-networks.md#network-and-accessibility) |

## Joins and nearest

1. Same CRS on both layers (projected if a distance is involved). Fixed geometries.
2. Choose the predicate to match the question: `intersects` (default, touching counts), `within` (point in polygon), `contains`. Points on a shared border match two polygons with `intersects`.
3. Run:
   - QGIS: `native:joinattributesbylocation` (PREDICATE 0 intersect, 1 contain, 2 equal, 3 touch, 4 overlap, 5 are within, 6 cross; METHOD 0 one-to-many, 1 first match, 2 largest overlap), `native:joinbynearest` (NEIGHBORS, MAX_DISTANCE in layer units), `native:countpointsinpolygon`.
   - GeoPandas: `gpd.sjoin(pts, polys, predicate="within", how="left")`, `gpd.sjoin_nearest(a, b, distance_col="dist_m", max_distance=500)` (projected CRS, or distances are degrees).
4. **Check**: output count vs input count. One-to-many joins multiply rows; `how="left"` keeps unmatched rows with nulls. Report matched, unmatched and duplicated counts. Spot-check two features on the map.

```python
import geopandas as gpd
pts = gpd.read_file("schools.gpkg").to_crs(2154)
polys = gpd.read_file("communes.gpkg").to_crs(2154)
j = gpd.sjoin(pts, polys[["insee", "geometry"]], predicate="within", how="left")
print(len(pts), len(j), j["insee"].isna().sum(), j.index.duplicated().sum())
```

## Buffers and distances

1. Projected CRS in meters (step 3 above). For distances over hundreds of kilometers, use geodesic measures (`pyproj.Geod`, QGIS ellipsoidal `$length`), not a planar CRS.
2. Buffer: `native:buffer` (DISTANCE in layer units, SEGMENTS, DISSOLVE). Multi-distance rings: `native:multiringconstantbuffer` or several buffers then `native:difference`.
3. Dissolve overlapping buffers before computing a covered area, or the overlap is counted twice.
4. **Check**: one buffer's width measured with the ruler or `ST_Distance` equals the requested distance; a 100 m point buffer has an area near 31 416 m2 (pi r squared; about 0.6 % less with SEGMENTS=8, since the circle is a 32-sided polygon). An area near 31 400 on a layer still in EPSG:4326 is in square degrees (the buffer ran as 100 degrees): check the layer CRS, not only the number.

Distance to nearest feature for many points: `native:joinbynearest` (adds `distance`), or a proximity raster with `gdal:proximity` (UNITS 0 georeferenced, 1 pixels) when a continuous distance surface is needed for suitability.

## Overlay order

Inspect, reproject, fix geometries, clip to study area, buffer, dissolve, overlay, spatial join, then compute areas and lengths last. Ids: `native:clip`, `native:intersection`, `native:difference`, `native:union`, `native:dissolve`, `native:extractbylocation`, `native:exportaddgeometrycolumns`.

Check after each step: feature count (0 or a sudden drop is a red flag), extent (near 0,0 or in degrees in a metric CRS), validity, area sum (a dissolve keeps the total minus overlaps), geometry type unchanged.

## Zonal statistics

1. Raster and polygons in the same CRS. If they differ, reproject the polygons, not the raster (resampling changes values).
2. Polygons much smaller than a pixel give empty or one-pixel stats: compare polygon area with pixel area and warn when fewer than about 10 pixels fall inside.
3. NoData set on the raster, so it is not averaged as 0.
4. Run `native:zonalstatisticsfb` (INPUT, INPUT_RASTER, RASTER_BAND, COLUMN_PREFIX, STATISTICS list: 0 count, 1 sum, 2 mean, 3 median, 4 st dev, 5 min, 6 max, 7 range, 8 minority, 9 majority, 10 variety, 11 variance) or `rasterstats.zonal_stats`. Categorical rasters (land cover): `native:zonalhistogram` for counts per class, never a mean.
5. **Check**: the `count` column times pixel area is close to the polygon area; a value range that matches the raster's range.

```bash
qgis_process run native:zonalstatisticsfb -- INPUT=fields.gpkg INPUT_RASTER=ndvi.tif RASTER_BAND=1 \
  COLUMN_PREFIX=ndvi_ STATISTICS=0,2,4 OUTPUT=fields_ndvi.gpkg
```

## Tools and ids

Confirm an id and its parameters on the installed version: `qgis_process list | grep -i slope`, `qgis_process help native:slope`. In the Python console: `processing.algorithmHelp("native:slope")`. GRASS ids are `grass:r.watershed` on recent QGIS and `grass7:r.watershed` on older ones, and need GRASS installed with the GRASS provider enabled. Parameters for GRASS tools follow the GRASS module names.

Verified on 2026-10-11 against QGIS 3.44 (`qgis_process help`) for every `native:`, `qgis:` and `gdal:` id in this skill.

Running a chain from Python returns layers you can check between steps:

```python
import processing
r = processing.run("native:slope", {"INPUT": "dem_2154.tif", "Z_FACTOR": 1, "OUTPUT": "slope.tif"})
from qgis.core import QgsRasterLayer
lyr = QgsRasterLayer(r["OUTPUT"], "slope")
s = lyr.dataProvider().bandStatistics(1)
print(s.minimumValue, s.maximumValue, s.mean)   # degrees: 0 to under 90
```

## Optional fast path: TerraLab MCP

When the TerraLab MCP server is connected (tools such as `get_elevation`, `extract_open_data`, `find_places`; the prefix varies by client), use it to fetch spot elevations, boundaries or OSM features quickly. Everything here works without it.

## Before handing over a result

- [ ] Assumptions stated (boundary, year, distance type, DEM, weights).
- [ ] Output CRS named; counts, areas or lengths reported next to input numbers.
- [ ] One number cross-checked by a second method (ruler, a manual calculation, a second tool).
- [ ] Map looked at: render or screenshot the result over a basemap and check it lands in the right place.
- [ ] The code or the list of Processing calls that produced it returned, so the user can rerun it.
- [ ] GeoPackage output, not Shapefile (field names over 10 characters are cut).

## Scripts

- `python3 scripts/layer_report.py data.gpkg [--layer name]`: count, CRS, extent, invalid and null geometries, total area or length in meters. Run before and after each step. Exit code 1 on invalid or null geometries.
- `python3 scripts/check_measurement_crs.py --file data.gpkg` (or `--epsg 3857`): says whether the layer CRS is fit for distances and areas, and proposes a UTM zone.
- `python3 scripts/utm_epsg.py LON LAT`: UTM EPSG code for a point.

Need GDAL Python bindings or geopandas/pyproj (inside QGIS, use its Python).

## Going further

AI Agent for QGIS runs these analysis workflows from a chat inside QGIS: https://terra-lab.ai/ai-agent?utm_source=skills&utm_medium=geoai-skills&utm_campaign=spatial-analysis
