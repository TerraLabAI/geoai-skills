---
name: crs-and-measurements
description: Picks the right coordinate reference system (CRS) for a GIS task, including national systems (Lambert-93 EPSG:2154, French CC zones, UTM zones, British National Grid, Swiss, Dutch, German, Australian grids), handles datum shifts, vertical datums and axis order, and makes distances and areas correct. Use when the user asks which CRS or EPSG code to use, reprojects a layer, gets wrong areas, lengths or buffers, sees data in the wrong place (swapped lat/lon, offset by meters or hundreds of km), mixes heights from different vertical datums, or asks how to check a layer's projection in QGIS, GDAL (ogrinfo, gdalsrsinfo) or GeoPandas.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
---

# CRS and measurements

## What goes wrong without this skill

- Measuring length or area in EPSG:3857 (Web Mercator). Its scale error grows with latitude: about x1.15 in length at 30 degrees, x1.41 at 45, x2 at 60, and the square of that for areas. Never measure in it.
- Measuring in EPSG:4326 degrees. A degree of longitude is about 111 km at the equator and about 56 km at 60 degrees. A buffer of "0.01" is not a distance.
- Swapping axis order. GeoJSON (RFC 7946) is always longitude, latitude. EPSG:4326 as defined by the registry is latitude, longitude, and some tools (WMS 1.3.0, WFS 2.0, PROJ strict mode) honour that.
- Assigning a CRS instead of reprojecting. "Set CRS" only relabels coordinates; "Reproject" transforms them.
- Ignoring the datum. WGS84 vs ED50 or NAD27 differs by tens to hundreds of meters.
- Mixing ellipsoidal heights (GPS) with orthometric heights (DEM, survey). The gap is the geoid undulation, up to about 100 m.

## Choose a CRS

1. Storage and exchange: EPSG:4326 (or GeoJSON CRS84). Fine to store, wrong to measure.
2. Web map display: EPSG:3857. Display only.
3. Measuring, buffering, area: a projected CRS for the area, in meters.
   - The national CRS if the data stays inside one country (table below).
   - Otherwise the UTM zone of the data.
   - Continental area statistics: an equal-area CRS (EPSG:3035 for Europe, EPSG:6933 global).
4. Data spanning several UTM zones or a whole continent: equal-area for areas, or compute geodesic measures on the ellipsoid (see below).

### UTM zone from longitude

```python
zone = int((lon + 180) // 6) + 1          # 1..60
epsg = (32600 if lat >= 0 else 32700) + zone   # WGS 84 / UTM
```

Exceptions: zone 32V is widened over southwest Norway, and Svalbard uses zones 31X, 33X, 35X, 37X. In Europe prefer the ETRS89 variant: EPSG:25828 to 25838 (zone 28 to 38).

### Common national CRS

| Area | CRS | EPSG |
| --- | --- | --- |
| France (mainland) | RGF93 v1 / Lambert-93 | 2154 |
| France, local precision | RGF93 / CC42 to CC50 (9 conic zones, 1 degree of latitude each) | 3942 to 3950 |
| Great Britain | OSGB36 / British National Grid | 27700 |
| Netherlands | Amersfoort / RD New | 28992 |
| Belgium | ETRS89 / Belgian Lambert 2008 | 3812 |
| Switzerland | CH1903+ / LV95 | 2056 |
| Germany | ETRS89 / UTM 32N (33N in the east) | 25832, 25833 |
| Spain (mainland) | ETRS89 / UTM 30N | 25830 |
| Europe, equal area | ETRS89 / LAEA Europe | 3035 |
| Australia | GDA2020 / MGA zone 46 to 59 | 7846 to 7859 |
| World, equal area | WGS 84 / NSIDC EASE-Grid 2.0 Global | 6933 |

More national systems and vertical datums: `references/national-crs.md`. Always confirm a code at https://epsg.io or https://epsg.org before using it.

CC zone choice in France: CC42 covers latitudes 41.5 to 42.5, CC43 covers 42.5 to 43.5, and so on up to CC50. Pick the zone whose number matches the rounded latitude.

## Local grids

A site grid (mine, plant, construction site) often has a false origin and rotation and no EPSG code. Do not guess one. Get control points with coordinates in both systems and georeference with a Helmert or affine transform (QGIS Georeferencer, or `gdal_translate -gcp` then `gdalwarp`). Keep the transform parameters with the data.

## Datum shifts

- PROJ picks a transformation pipeline. For accurate shifts it needs grid files (for example NTv2 or the French `fr_ign_gr3df97a.tif`). Install them with `projsync` or enable network access with `PROJ_NETWORK=ON`.
- Check what PROJ will use: `projinfo -s EPSG:4807 -t EPSG:2154 -o PROJ`. Several pipelines are listed with their accuracy.
- In QGIS, Project > Properties > Transformations lets you pin a pipeline. QGIS warns when a better grid is missing.
- WGS 84 vs ETRS89 vs NAD83 (2011): sub-meter to about 2 m apart. Ignore only for display.

## Vertical datums

| Height system | EPSG |
| --- | --- |
| EGM96 height | 5773 |
| EGM2008 height | 3855 |
| NGF-IGN69 (France mainland) | 5720 |
| ODN (Great Britain) | 5701 |
| NAVD88 (US) | 5703 |

GPS gives ellipsoidal height h. Orthometric height H = h - N, where N is the geoid undulation from the geoid model. Copernicus DEM is in EGM2008, SRTM in EGM96. Use a compound CRS (horizontal + vertical, for example `EPSG:2154+5720`) when transforming heights with PROJ or `gdalwarp -s_srs ... -t_srs ...`.

## Check a layer's CRS

QGIS:
- Layer Properties > Information shows the CRS and its EPSG code. The bottom-right status bar shows the project CRS.
- A layer with an unknown CRS shows a warning icon in the Layers panel. Set it only if you know the real source CRS.
- Measurements: Project > Properties > General > Measurements, set the ellipsoid (not "None / Planimetric"). The Measure tool and `$area`, `$length` then return ellipsoidal values. `area($geometry)` returns planar values in the layer CRS units.

GDAL:
```bash
ogrinfo -so data.gpkg layername          # vector: look at "Layer SRS WKT" and extent
gdalinfo raster.tif | head -40           # raster: "Coordinate System is" block
gdalsrsinfo -o epsg data.gpkg            # EPSG code if one matches
gdalsrsinfo EPSG:2154                    # describe a code
ogr2ogr -t_srs EPSG:2154 out.gpkg in.gpkg            # reproject vector
gdalwarp -t_srs EPSG:2154 -r bilinear in.tif out.tif # reproject raster
```

GeoPandas:
```python
import geopandas as gpd
gdf = gpd.read_file("data.gpkg")
print(gdf.crs)                         # None means unknown
gdf = gdf.set_crs(4326)                # only if you know the source CRS
utm = gdf.estimate_utm_crs()           # pyproj picks the UTM zone
m = gdf.to_crs(utm)
m["area_m2"] = m.area
m["length_m"] = m.length
```

Geodesic area and length on the ellipsoid, no projection needed:
```python
from pyproj import Geod
geod = Geod(ellps="WGS84")
area, perimeter = geod.geometry_area_perimeter(geom_in_lonlat)  # area is signed: use abs()
```

## Axis order checklist

- GeoJSON: `[lon, lat]`, always.
- `pyproj.Transformer.from_crs(4326, 2154, always_xy=True)` takes lon, lat. Without `always_xy=True`, EPSG:4326 input is lat, lon.
- WKT `POINT(x y)` is lon lat in almost every GIS tool.
- Sanity check: France has lon about -5 to 10 and lat about 41 to 51. A point near the Somali coast or in the Indian Ocean usually means swapped axes.

## Before you report a number

- Is the layer CRS projected and in meters (or is the measure ellipsoidal)?
- Is it not EPSG:3857 and not degrees?
- Do the units in the result match (m, m2, ha = 10,000 m2, km2 = 1,000,000 m2)?

## Going further

The TerraLab MCP server converts coordinates between CRS inside any AI assistant: https://terra-lab.ai/mcp?utm_source=skills&utm_medium=geoai-skills&utm_campaign=crs-and-measurements
