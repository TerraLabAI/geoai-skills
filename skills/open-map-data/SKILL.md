---
name: open-map-data
description: Chooses and downloads open vector map data for anywhere in the world, and states the license and attribution it needs. Covers OpenStreetMap (Overpass API, Geofabrik extracts), Overture Maps (buildings, places, transportation, divisions, addresses, base) as GeoParquet queried with DuckDB, national sources such as IGN BD TOPO in France and OS OpenMap Local in Great Britain, open building datasets from Microsoft and Google, licenses (ODbL, CDLA Permissive 2.0, CC BY 4.0), bbox queries, size limits and output formats. Use when someone needs building footprints, roads, points of interest, addresses, boundaries or land use for an area, asks where to get GIS data, how to download OSM or Overture data, or whether they may use it commercially.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
---

# Open map data

## What goes wrong without this skill

- Downloading a whole country (or the planet) when a bounding box was enough.
- Hardcoding an old Overture release path that has been removed.
- Missing the ODbL share-alike duty when a derived database is shared.
- No attribution on the published map or dataset.
- Saving to Shapefile and losing long field names, UTF-8 text or files over 2 GB.

## Pick a source

| Need | First choice | Also |
|---|---|---|
| Buildings | Overture buildings | OSM, national cadastre or topographic data |
| Roads, paths | OSM or Overture transportation | national road data |
| Shops, POIs | Overture places | OSM |
| Addresses | national address file | Overture addresses (coverage varies by country) |
| Admin boundaries | Overture divisions | national boundaries |
| Land use, water | OSM | Overture base |
| France, detailed | IGN BD TOPO | OSM |
| Great Britain | OS OpenMap Local | OSM |

Compare two sources on a small area before committing: coverage differs a lot by country.

## OpenStreetMap

Small area, specific features: Overpass API.

```bash
curl -s https://overpass-api.de/api/interpreter --data-urlencode 'data=
[out:json][timeout:60];
(way["building"](48.85,2.33,48.86,2.35);relation["building"](48.85,2.33,48.86,2.35););
out geom;' > buildings.json
```

The bbox order in Overpass is south, west, north, east. Keep queries small: the public server limits time and memory; use `[timeout:]` and split big areas.

Region or country: download a `.osm.pbf` extract from Geofabrik (download.geofabrik.de), then convert with GDAL:

```bash
ogr2ogr -f GPKG buildings.gpkg region-latest.osm.pbf multipolygons -where "building IS NOT NULL"
```

## Overture Maps

Themes: `addresses`, `base`, `buildings`, `divisions`, `places`, `transportation`. Files are GeoParquet on Amazon S3 (`s3://overturemaps-us-west-2/release/<release>/theme=<theme>/type=<type>/*`) and Azure Blob Storage. Releases are dated (for example `2026-09-23.1`) and old ones are removed, so read the latest from the STAC catalog.

First choice, the official CLI (`pip install overturemaps`), which fetches the latest release:

```bash
overturemaps download --bbox=2.33,48.85,2.35,48.86 -f geoparquet --type=building -o out.parquet
```

Second choice, DuckDB, when you need SQL filters or columns. DuckDB still reads every file's metadata: expect minutes, even for a small bbox.

```sql
INSTALL spatial; LOAD spatial;
INSTALL httpfs; LOAD httpfs;
SET s3_region = 'us-west-2';
SET VARIABLE latest = (SELECT latest FROM 'https://stac.overturemaps.org/catalog.json');

COPY (
  SELECT id, height, geometry
  FROM read_parquet('s3://overturemaps-us-west-2/release/' || getvariable('latest')
                    || '/theme=buildings/type=building/*', hive_partitioning = 1)
  WHERE bbox.xmin BETWEEN 2.33 AND 2.35
    AND bbox.ymin BETWEEN 48.85 AND 48.86
) TO 'buildings.gpkg' WITH (FORMAT GDAL, DRIVER 'GPKG');
```

Always filter on the `bbox` columns: DuckDB then reads only the matching row groups. Without that filter the query scans the whole world. Check theme and type names on docs.overturemaps.org before use.

## National and other sources

- France: IGN BD TOPO (buildings, roads, hydrography, land use), on geoservices.ign.fr, Licence Ouverte Etalab 2.0.
- Great Britain: OS OpenMap Local, Open Government License.
- Microsoft Global ML Building Footprints (CDLA Permissive 2.0 from Microsoft; ODbL once merged into Overture) and Google Open Buildings (CC BY 4.0 or ODbL 1.0, your choice). Parts are already merged into Overture buildings.

## Licenses

| License | Used by | You must |
|---|---|---|
| ODbL 1.0 | OSM; Overture buildings, transportation, divisions, base | credit the source; share a publicly used derived database under ODbL; a rendered map (produced work) needs the credit; if it was made from a derived database, you must also offer that database or the method to rebuild it |
| CDLA Permissive 2.0 | Overture places | keep the license text with redistributed data; results of analysis carry no duty |
| CC BY 4.0 | some Overture sources, many national datasets | credit the source, link the license, say if you changed it |
| Etalab 2.0, OGL | France, UK public data | credit the source and date |

Verified on 2026-10-11 against opendatacommons.org, cdla.dev, creativecommons.org and docs.overturemaps.org/attribution.

Overture addresses mix licenses per source country: read the attribution page. Attribution lines: `© OpenStreetMap contributors`, `© OpenStreetMap contributors, Overture Maps Foundation`. Overture lists per-theme credits at docs.overturemaps.org/attribution.

Commercial use is allowed under all of these, within their conditions.

## Output format

Prefer GeoPackage (one file, no 10-character field names, UTF-8, no 2 GB limit, several layers). Use GeoParquet for large analytic data, GeoJSON for small web exchange in EPSG:4326. Shapefile only when a tool demands it.

## Before delivering

- Feature count and extent look right for the area.
- CRS stated (sources come in EPSG:4326; reproject for measures).
- Source, release or download date, and license written next to the file.

## Scripts and references

- Attribution text, license and duty per source: [references/attribution.md](references/attribution.md).
- `python3 scripts/attribution.py osm overture:buildings --year 2026` prints the lines and a combined credit line; `--list` shows the keys.

## Going further

TerraLab MCP server extracts buildings, roads and other open data as files from any AI assistant: https://terra-lab.ai/mcp?utm_source=skills&utm_medium=geoai-skills&utm_campaign=open-map-data
