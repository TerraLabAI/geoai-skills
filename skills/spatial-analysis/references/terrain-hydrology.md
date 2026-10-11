# Terrain and hydrology from a DEM

## Pick and prepare the DEM

1. **Which DEM**: a national lidar DTM when one exists (bare earth, 1 to 5 m; for example IGN RGE ALTI in France, USGS 3DEP in the US). Otherwise Copernicus DEM GLO-30, which is a surface model (roofs and canopy included) with heights on EGM2008. Say which one you used: a surface model overstates slope at forest edges and blocks flow at buildings.
2. **Inspect**: `gdalinfo -stats dem.tif`. Note CRS, pixel size, NoData, min and max. Heights below -500 or above 9000 are NoData not set.
3. **Reproject to a metric CRS** before slope, aspect, hillshade or hydrology: `gdal:warpreproject` with RESAMPLING 1 (bilinear) or 2 (cubic), never nearest for elevation. Slope on a DEM in degrees gives wrong values unless a scale is set (`gdaldem slope -s 111120` is only a rough fix near the equator).
4. **Clip with a margin**: clip the DEM to the study area plus a buffer (at least a few kilometers for hydrology, or the whole catchment), or flow paths are cut at the edge.

## Slope, aspect, hillshade, contours

| Product | QGIS id | GDAL CLI | Check |
| --- | --- | --- | --- |
| Slope | `native:slope` (INPUT, Z_FACTOR) or `gdal:slope` (AS_PERCENT, SCALE) | `gdaldem slope dem.tif slope.tif [-p]` | degrees 0 to under 90; percent can exceed 100 |
| Aspect | `native:aspect`, `gdal:aspect` | `gdaldem aspect dem.tif aspect.tif` | 0 to 360 clockwise from north; flat cells -9999 (GDAL) or 0 |
| Hillshade | `native:hillshade` (AZIMUTH, V_ANGLE), `gdal:hillshade` | `gdaldem hillshade dem.tif hs.tif -z 1 -az 315 -alt 45` | 0 to 255 |
| Contours | `gdal:contour` (lines), `gdal:contour_polygon` | `gdal_contour -a elev -i 10 dem.tif contours.gpkg` | interval matches the relief |

- Z_FACTOR stays 1 when horizontal and vertical units are both meters.
- A slope map with a grid or terrace pattern comes from an integer DEM or a DEM resampled with nearest. Use a float DEM.
- Classify slope for suitability with `native:reclassifybytable` (TABLE is a flat list `min,max,value,...`; RANGE_BOUNDARIES 0 means min < value <= max).

## Viewshed

`gdal:viewshed` (INPUT, BAND, OBSERVER as `x,y [CRS]`, OBSERVER_HEIGHT, TARGET_HEIGHT, MAX_DISTANCE, OUTPUT). CLI: `gdal_viewshed -ox X -oy Y -oz 1.7 -tz 0 -md 5000 dem.tif vs.tif`.

1. Observer coordinates in the DEM's CRS.
2. Use a surface model if trees and buildings should block the view, a terrain model for a bare-earth view; say which.
3. Set MAX_DISTANCE; without it the run covers the whole raster.
4. **Check**: the observer cell is visible; visible area (count of 255 cells times pixel area) is plausible; overlay on the hillshade.

For several observers, run one viewshed each and sum them with `native:rastercalc`, or use the Visibility Analysis plugin.

## Hydrology

Order matters: condition the DEM, then flow direction, then accumulation, then streams and watersheds. Skipping conditioning gives broken, discontinuous streams.

1. **Condition**: breach or fill depressions.
   - QGIS native: `native:fillsinkswangliu` (INPUT, BAND, MIN_SLOPE; outputs OUTPUT_FILLED_DEM, OUTPUT_FLOW_DIRECTIONS, OUTPUT_WATERSHED_BASINS).
   - WhiteboxTools: `BreachDepressionsLeastCost` (recommended first, lower impact than filling), then `FillDepressions` for what remains.
   - GRASS: `r.fill.dir`, or skip it, since `r.watershed` handles depressions itself.
2. **Flow direction and accumulation**:
   - GRASS `r.watershed` (elevation, threshold; outputs accumulation, drainage, basin, stream). Accumulation is in cells; negative values mark cells that may get flow from outside the region.
   - WhiteboxTools `D8Pointer` then `D8FlowAccumulation` (`--out_type=cells` or `catchment area`).
3. **Streams**: threshold the accumulation. Threshold in cells = contributing area / pixel area. For 1 km2 on a 25 m DEM: 1 000 000 / 625 = 1600 cells. State the threshold you chose. WhiteboxTools `ExtractStreams`; GRASS `r.stream.extract`; or `native:rastercalc` with `"acc@1" >= 1600`.
4. **Watershed for an outlet**: snap the outlet point to the highest accumulation cell within a few pixels first (WhiteboxTools `JensonSnapPourPoints` or `SnapPourPoints`), then WhiteboxTools `Watershed` or GRASS `r.water.outlet`. An unsnapped outlet gives a watershed of a few cells.
5. **Polygonize** the basin: `gdal:polygonize`, then dissolve.
6. **Checks**: streams continuous and following valleys on the hillshade; streams line up with mapped rivers (OSM waterways or a national hydrography layer); watershed area compared with a published value for that gauge or river when one exists.

WhiteboxTools command line (the `whitebox_tools` binary; the `whitebox` Python package and the WhiteboxTools QGIS plugin wrap the same tools):

```bash
whitebox_tools -r=BreachDepressionsLeastCost --dem=dem.tif -o=dem_br.tif --dist=50 --fill
whitebox_tools -r=D8Pointer --dem=dem_br.tif -o=d8.tif
whitebox_tools -r=D8FlowAccumulation -i=d8.tif --pntr -o=acc.tif --out_type=cells
whitebox_tools -r=ExtractStreams --flow_accum=acc.tif -o=streams.tif --threshold=1600
whitebox_tools -r=JensonSnapPourPoints --pour_pts=outlet.shp --streams=streams.tif -o=outlet_snap.shp --snap_dist=50
whitebox_tools -r=Watershed --d8_pntr=d8.tif --pour_pts=outlet_snap.shp -o=basin.tif
```

Check flag names on your version: `whitebox_tools --toolhelp=Watershed`. WhiteboxTools reads vector points as Shapefile.

## Derived indices

- Topographic Wetness Index: ln(a / tan(b)), a = specific catchment area, b = slope in radians. WhiteboxTools `WetnessIndex` (`--sca`, `--slope` in degrees), GRASS `r.topidx`. Use it as a relative wetness indicator, not a flood extent.
- Height Above Nearest Drainage (HAND): elevation minus the elevation of the stream cell each cell drains to. WhiteboxTools `ElevationAboveStream` (`--dem`, `--streams`). Useful for low-lying areas along rivers; see the flood recipe.
