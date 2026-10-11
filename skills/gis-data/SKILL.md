---
name: gis-data
description: Finds, downloads, loads, converts, reprojects, cleans and cites geospatial data, and checks it before use. Covers OpenStreetMap (Overpass, Geofabrik), Overture Maps (buildings, places, roads, divisions, addresses) with DuckDB or the overturemaps CLI, national sources (IGN BD TOPO, OS OpenMap Local), elevation (DEM) and imagery pointers, formats (GeoPackage, GeoParquet, Shapefile limits, GeoJSON, KML, CSV with lat/lon columns), CRS and EPSG choice, axis order, datum and vertical datum, GDAL/OGR commands (ogr2ogr, ogrinfo, gdalwarp, gdalinfo), licenses (ODbL, CDLA, CC BY, Etalab) and attribution lines. Use when someone needs building footprints, roads, POIs, boundaries or addresses for an area, asks where to get GIS data, wants to convert shapefile, GeoJSON, KML, CSV or GeoParquet, reproject vector data to another CRS, fix data in the wrong place (swapped lat/lon), pick an EPSG code, clean invalid geometries, or know whether they may use the data commercially and how to credit it.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
  version: "1.1.0"
---

# GIS data

Get the right data for the area, in a format and CRS that will not break later steps, with its license written next to it. Inspect every file before using it and check it after every conversion.

## Core rules

1. Ask, or state as an assumption, the area, the year or release, and what "boundary" or "building" means for the user.
2. Download a bounding box, not a country, unless the country is needed.
3. Inspect what arrived: feature count, geometry type, CRS, extent, fields, encoding.
4. Store in EPSG:4326 or a national CRS; measure only in a projected CRS in meters ([references/crs.md](references/crs.md)).
5. Write source, release or download date and license next to the file. Credit it on any map.
6. Say so when no open source covers the need, instead of substituting another dataset silently.

## Workflow index

| Task | Workflow |
| --- | --- |
| Get vector data for an area | A. Find and download |
| Elevation or imagery | B. Rasters |
| Open, convert, reproject | C. Convert ([references/formats.md](references/formats.md)) |
| Data in the wrong place, which EPSG | D. CRS ([references/crs.md](references/crs.md), [references/national-crs.md](references/national-crs.md)) |
| Broken geometries, duplicates, encoding | E. Clean |
| License and credit line | F. Cite ([references/attribution.md](references/attribution.md)) |

## A. Find and download

| Need | First choice | Also |
| --- | --- | --- |
| Buildings | Overture buildings | OSM, national cadastre or topographic data |
| Roads, paths | OSM or Overture transportation | national road data |
| Shops, POIs | Overture places | OSM |
| Addresses | national address file | Overture addresses (coverage varies by country) |
| Admin boundaries | Overture divisions | national boundaries |
| Land use, water | OSM | Overture base |
| France, detailed | IGN BD TOPO (Licence Ouverte Etalab 2.0) | OSM |
| Great Britain | OS OpenMap Local (Open Government Licence) | OSM |

Compare two sources on a small area before committing: coverage differs a lot by country.

OSM, small area, through Overpass (bbox order is south, west, north, east):

```bash
curl -s https://overpass-api.de/api/interpreter --data-urlencode 'data=
[out:json][timeout:60];
(way["building"](48.85,2.33,48.86,2.35);relation["building"](48.85,2.33,48.86,2.35););
out geom;' > buildings.json
```

OSM, region: a `.osm.pbf` extract from download.geofabrik.de, then
`ogr2ogr -f GPKG buildings.gpkg region-latest.osm.pbf multipolygons -where "building IS NOT NULL"`.

Overture: releases are dated and old ones are removed, so never hardcode a release path. First choice, the official CLI, which reads the latest release (bbox is west, south, east, north):

```bash
pip install overturemaps
overturemaps download --bbox=2.33,48.85,2.35,48.86 -f geoparquet --type=building -o buildings.parquet
```

SQL filters with DuckDB (latest release read from the STAC catalog, filter on `bbox` columns or the whole world is scanned): see the `spatial-sql` skill. Expect minutes even for a small area.

Check: feature count is plausible for the area (a city block has tens of buildings, not zero or millions), the extent matches the requested bbox.

## B. Rasters

- Elevation: Copernicus DEM GLO-30 (30 m, global, heights in EGM2008), SRTM (heights in EGM96), national lidar DEMs where available (for example IGN RGE ALTI in France). Check the vertical datum before mixing with GPS heights ([references/crs.md](references/crs.md)).
- Imagery (Sentinel-2, Landsat, aerial): find and analyse it with the `remote-sensing` skill.
- Inspect: `gdalinfo -stats dem.tif` (CRS, pixel size, nodata, min and max). A DEM with min -32768 has an undeclared nodata value: set it with `gdal_translate -a_nodata -32768`.
- Reproject: `gdalwarp -t_srs EPSG:2154 -r bilinear dem.tif dem_2154.tif` (nearest for classes, bilinear or cubic for continuous values).
- Clip: `gdalwarp -cutline area.gpkg -crop_to_cutline dem.tif dem_clip.tif`.

## C. Convert

```bash
ogrinfo -so -al in.gpkg                                   # inspect: count, extent, CRS, fields
ogr2ogr -f GPKG out.gpkg in.shp                           # Shapefile to GeoPackage
ogr2ogr -f GeoJSON -t_srs EPSG:4326 out.geojson in.gpkg   # GeoJSON must be lon/lat WGS 84
ogr2ogr -f Parquet out.parquet in.gpkg                    # GeoParquet
ogr2ogr -f GPKG out.gpkg in.kml                           # KML to GeoPackage
ogr2ogr -f GPKG pts.gpkg pts.csv -oo X_POSSIBLE_NAMES=lon -oo Y_POSSIBLE_NAMES=lat \
        -oo KEEP_GEOM_COLUMNS=NO -a_srs EPSG:4326        # CSV with coordinate columns
ogr2ogr -f GPKG clip.gpkg in.gpkg -spat 2.33 48.85 2.35 48.86   # bbox filter (layer CRS units)
```

Format choice and limits (Shapefile cuts field names to 10 characters, 2 GB per file, no mixed geometries): [references/formats.md](references/formats.md).

Check after each conversion: same feature count as the input, same geometry type, the expected CRS, the extent in the expected place.

## D. CRS

- "Set CRS" or `-a_srs` only relabels; `-t_srs` or Reproject transforms. Relabel only when the declared CRS is wrong or missing and the true one is known.
- Points near 0,0, in the ocean, or in a mirror location usually mean swapped lat/lon or a missing CRS.
- Pick the measuring CRS: national grid inside one country, else UTM. `python3 scripts/utm_epsg.py LON LAT` prints the UTM EPSG; `python3 scripts/check_measurement_crs.py --file data.gpkg` (or `--epsg 4326 --lonlat LON LAT`) says whether measuring is safe, exit code 1 when not.
- Details, datum shifts, vertical datums, axis order: [references/crs.md](references/crs.md).

## E. Clean

| Problem | Check | Fix |
| --- | --- | --- |
| Invalid geometries | QGIS Check validity, `ST_IsValid` | `ogr2ogr -makevalid`, QGIS `native:fixgeometries`, `shapely.make_valid` (keep only polygon parts afterwards) |
| Null or empty geometries | count `geometry IS NULL` | drop or report them |
| Duplicates | count distinct ids or geometries | QGIS `native:deleteduplicategeometries` |
| Mojibake in text fields | look at accented names | Shapefile: set the `.cpg` file or `-oo ENCODING=...`; prefer GeoPackage |
| Mixed geometry types | `ogrinfo` geometry type | `-nlt PROMOTE_TO_MULTI` or split by type |

Report counts before and after cleaning.

## F. Cite

`python3 scripts/attribution.py osm overture:buildings --year 2026` prints each source's credit, license and duty plus one combined line; `--list` shows the keys. License table and duties (ODbL share-alike for derived databases, CDLA, CC BY, Etalab, OGL): [references/attribution.md](references/attribution.md). Commercial use is allowed under all of these, within their conditions.

## Optional fast path

When the TerraLab MCP server is connected (tools such as `extract_open_data`, `find_places`, `convert_coordinates`, `get_elevation`, `open_gis_file`; prefixes vary by client), it can extract open data for an area, convert coordinates, return elevation or open a GIS file in one call. Everything above works without it.

## Before delivering

- [ ] Feature count and extent fit the area.
- [ ] CRS stated, and a projected CRS used for any measure.
- [ ] Format is GeoPackage or GeoParquet unless the user asked otherwise.
- [ ] Source, release or date, license and credit line written next to the file.
- [ ] Commands that produced the file returned to the user.

## Going further

The TerraLab MCP server extracts buildings, roads and other open data as files from any AI assistant: https://terra-lab.ai/mcp?utm_source=skills&utm_medium=geoai-skills&utm_campaign=gis-data
