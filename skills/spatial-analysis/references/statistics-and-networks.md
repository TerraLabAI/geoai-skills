# Spatial statistics, patterns and networks

## Density and heatmaps

`qgis:heatmapkerneldensityestimation` (INPUT points, RADIUS in layer units, PIXEL_SIZE, WEIGHT_FIELD, KERNEL 0 quartic default, OUTPUT_VALUE 0 raw or 1 scaled).

1. Points in a projected CRS, or RADIUS is in degrees.
2. Choose the radius from the question (walking distance, typical spacing), state it. The map changes a lot with the radius; show two radii if unsure.
3. Raw output is not a count per km2. For counts per area, use a grid: `native:creategrid` then `native:countpointsinpolygon`, and divide by cell area.
4. Normalize by population or exposure when comparing areas (crimes per 1000 inhabitants), or the map shows where people live.

For point styling only (no analysis), the Heatmap renderer in layer symbology is enough.

## Point pattern and clustering

| Question | Tool | Note |
| --- | --- | --- |
| Clustered, random or dispersed? | `native:nearestneighbouranalysis` | Outputs observed and expected mean distance, NN index (below 1 clustered), z-score. Sensitive to the study area extent used for the expected distance. |
| Group points by density | `native:dbscanclustering` (EPS distance, MIN_SIZE) | Noise points get no cluster id. EPS in layer units. |
| Group points into K groups | `native:kmeansclustering` (CLUSTERS) | Not spatially contiguous; set K deliberately. |
| Groups in space and time | `native:stdbscanclustering` | needs a date field |
| Statistically significant hotspots (Getis-Ord Gi*), Moran's I | PySAL `esda` (`esda.G_Local`, `esda.Moran`, `esda.Moran_Local`) with `libpysal.weights` | Not in QGIS core. Hotspot plugins exist; check what they implement. |

Hotspot workflow with PySAL:
1. Aggregate points to polygons or a grid first (counts or rates); Gi* runs on values per area.
2. Build weights: `libpysal.weights.Queen.from_dataframe(gdf)` for polygons, `KNN` or `DistanceBand` for points or a grid. Report the choice.
3. Run `esda.G_Local(y, w, star=True, permutations=999)`; keep units with p below 0.05 and say the result is not corrected for multiple tests unless you apply a correction.
4. Check: islands (units without neighbors) are reported by libpysal; remove or handle them.

```python
import geopandas as gpd
from libpysal.weights import Queen
from esda import G_Local
g = gpd.read_file("grid_counts.gpkg")
w = Queen.from_dataframe(g); w.transform = "r"
gi = G_Local(g["rate"].values, w, star=True, permutations=999, seed=1)
g["z"], g["p"] = gi.Zs, gi.p_sim
g["class"] = "ns"
g.loc[(g.p < 0.05) & (g.z > 0), "class"] = "hot"
g.loc[(g.p < 0.05) & (g.z < 0), "class"] = "cold"
```

## Interpolation

`qgis:idwinterpolation` and `qgis:tininterpolation` in QGIS, `gdal_grid` on the command line. State the method and parameters, keep a share of points out to measure the error (leave-one-out or a holdout), and never extrapolate far beyond the sample points. Kriging needs a variogram (GRASS `v.krige`, PyKrige, gstools).

## Network and accessibility

Straight-line buffers are not travel distance. Ask which the user means.

| Need | Tool |
| --- | --- |
| Area reachable within X m or X min along roads from one point | `native:serviceareafrompoint` (STRATEGY 0 shortest, 1 fastest; TRAVEL_COST2; SPEED_FIELD, DEFAULT_SPEED in km/h) |
| Same from many points | `native:serviceareafromlayer` |
| Route between points | `native:shortestpathpointtopoint`, `...pointtolayer`, `...layertopoint` |
| Isochrone polygons with real road speeds | OpenRouteService (QGIS plugin ORS Tools, API key needed), Valhalla, OSRM |

Workflow with QGIS network tools:
1. Road layer with topology: lines connected at nodes (OSM roads split at intersections). Clip roads to the area plus a margin.
2. Projected CRS, so TOLERANCE and distances are in meters.
3. Fastest strategy needs a speed field in km/h or a DEFAULT_SPEED; one-way streets need DIRECTION_FIELD and its values.
4. Service area outputs lines (or boundary points with INCLUDE_BOUNDS). For a polygon, buffer the reachable lines by a small distance (for example 50 m) and dissolve, or build a concave hull (`native:concavehull`); say which.
5. Check: snap distance of the start point to the network (a point far from any road is snapped silently); travel time to one known destination compared with a routing website.
