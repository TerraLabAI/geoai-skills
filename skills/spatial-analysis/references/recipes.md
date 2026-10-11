# End-to-end recipes

Both recipes are what users mean by "make a flood map" or "find the best site". Each starts with questions, because the honest answer depends on them.

## Flood risk map for a town

### 1. Frame it before computing

Ask or state:
- Is there an official flood map? Many countries publish them (for example Géorisques and the PPRI zoning in France, FEMA flood maps in the US, the EU Floods Directive hazard maps). If one exists, use it first and say so. A DEM screening never replaces an official hazard map.
- Which flood type: river (fluvial), heavy rain runoff (pluvial), coastal. The method differs.
- Hazard or risk: hazard is where water may go; risk adds what is exposed (buildings, people, roads).

Without a hydraulic model and discharge data, the product is a **screening of low-lying, flow-concentrating areas**, not a return-period extent. Label it that way on the map and in the reply.

### 2. Data

| Input | Open source example |
| --- | --- |
| DEM, ideally lidar DTM | national lidar; else Copernicus DEM GLO-30 (surface model) |
| Rivers | national hydrography, or OSM `waterway=river|stream` |
| Town boundary | national admin boundaries or OSM `boundary=administrative` |
| Exposed assets | buildings and roads from OSM or Overture, national cadastre |

### 3. Steps (river flooding screening with HAND)

1. Reproject the DEM to a metric CRS; clip to the town plus its upstream catchment margin.
2. Condition the DEM (breach then fill), compute D8 pointer and accumulation ([terrain-hydrology.md](terrain-hydrology.md#hydrology)).
3. Extract streams with a threshold that reproduces the mapped rivers. Overlay on the OSM rivers and adjust the threshold until main channels line up.
4. Height above nearest drainage: WhiteboxTools `ElevationAboveStream --dem=dem_br.tif --streams=streams.tif -o=hand.tif`.
5. Classify HAND into hazard classes, stated as relative: for example 0 to 1 m high, 1 to 3 m medium, 3 to 5 m low, above 5 m none. Write the thresholds into the legend. `native:reclassifybytable` with TABLE `0,1,3,1,3,2,3,5,1,5,100000,0` (rows of min, max, value: 3 high, 2 medium, 1 low, 0 none) and RANGE_BOUNDARIES 1 (min <= value < max).
6. Optionally add a slope mask (flat ground floods more): `native:slope`, keep cells under 5 degrees in the high class.
7. Exposure: polygonize hazard classes (`gdal:polygonize`), fix geometries, then intersect with buildings (`native:intersection`) or count buildings per class (`native:joinattributesbylocation`).
8. Map: hillshade underneath, hazard classes semi-transparent, rivers, town boundary, legend with the method and the word "screening", data credits, scale bar.

### 4. Checks

- Hazard follows the valley floor on the hillshade, not hilltops. Hilltops in the high class mean the streams or the DEM are wrong.
- Compare with any official map or a known past flood: the overlap should be large along the main river.
- Report numbers: area per class in hectares, buildings per class, and the HAND thresholds used.
- Coastal and pluvial floods are not covered by HAND; for coastal, a bathtub on elevation connected to the sea is the crude screen (`elevation <= sea level + surge`, keeping only cells connected to the sea).

## Site suitability

Typical asks: best place for a solar farm, a school, a warehouse, a wind turbine, a shop.

### 1. Frame it

Ask for, or propose and state:
- **Constraints** (hard exclusions): protected areas, water, buildings, slope above X, distance to houses below Y.
- **Factors** (soft criteria) and their direction: closer to roads is better, flatter is better, south facing is better.
- **Weights** that sum to 1. When the user gives none, propose equal weights and say they should be adjusted; AHP pairwise comparison is an option when the user wants to justify weights.
- Minimum site size (a 2 ha site needs at least 2 ha of contiguous suitable cells).

### 2. Steps (raster weighted overlay)

1. One metric CRS, one study area. Pick one cell size suited to the smallest criterion (for example 25 m).
2. Build each factor as a raster on the **same grid**: `gdal:proximity` for distances (rasterize the source first with `gdal:rasterize`), `native:slope` for slope, `native:aspect` for aspect. Align every raster with `native:alignsingleraster` (REFERENCE_LAYER = the template grid) or `gdalwarp -te ... -tr ... -tap`.
3. Standardize each factor to 0 to 1, with direction: `native:fuzzifyrasterlinearmembership` (FUZZYLOWBOUND, FUZZYHIGHBOUND; swap the bounds to invert), or a raster calculator expression such as `max(0, min(1, 1 - "dist_road@1" / 5000))`.
4. Build the constraint mask as 0/1 rasters and multiply them together.
5. Combine: `score = mask * (w1*f1 + w2*f2 + ...)` with `native:rastercalc` or `gdal:rastercalculator`.
6. Keep cells above a score threshold, polygonize, dissolve, compute area, drop polygons below the minimum size, rank the rest by mean score (`native:zonalstatisticsfb`).
7. Sensitivity: rerun with one weight changed by 0.1; sites that stay in the top list are robust. Report it.

```python
import processing
f_road = processing.run("native:fuzzifyrasterlinearmembership", {
    "INPUT": "dist_road.tif", "BAND": 1, "FUZZYLOWBOUND": 5000, "FUZZYHIGHBOUND": 0,
    "OUTPUT": "f_road.tif"})["OUTPUT"]
score = processing.run("native:rastercalc", {
    "LAYERS": [f_road, "f_slope.tif", "mask.tif"],
    "EXPRESSION": '"mask@1" * (0.6 * "f_road@1" + 0.4 * "f_slope@1")',
    "OUTPUT": "score.tif"})["OUTPUT"]
```

Layer references in `native:rastercalc` expressions use the layer name plus `@band`; check the names QGIS gives the inputs (file base name) before writing the expression.

### 3. Checks

- Each factor raster: min 0, max 1, NoData where expected, same extent and pixel size (`gdalinfo`).
- Constraint mask: no candidate site inside a protected area or a lake (overlay and count).
- Top sites looked at on imagery: road access is real, the site is not a quarry or a cemetery.
- Return the weights, thresholds and the full list of commands.

Vector alternative for few criteria: buffer constraints, `native:difference` them from the study area, then score remaining parcels with `native:joinbynearest` distances and field calculator weights.
