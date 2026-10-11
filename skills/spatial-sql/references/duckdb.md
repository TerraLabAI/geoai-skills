# DuckDB spatial

```sql
INSTALL spatial; LOAD spatial;
SET geometry_always_xy = true;   -- read every geometry as x = longitude, y = latitude
```

## Axis order trap

DuckDB 1.5 spatial still assumes the axis order of the CRS definition by default, so EPSG:4326 input is read as latitude, longitude, and it prints a warning that this default will change. Measured on DuckDB 1.5.5, 2026-10-11, two points in Paris given as `ST_Point(lon, lat)`:

| Call | Result |
| --- | --- |
| `ST_Distance_Sphere` without the setting | 1572 m (wrong) |
| `ST_Distance_Sphere` with `geometry_always_xy = true` | 1331 m |
| `ST_Distance` after `ST_Transform` to EPSG:2154 | 1332 m |

Set `geometry_always_xy = true` at the start of every session (or pass `always_xy := true` to `ST_Transform`), then cross-check one distance in a projected CRS.

## Read and write files

```sql
SELECT * FROM ST_Read('parcels.gpkg') LIMIT 5;              -- any GDAL vector format
SELECT * FROM ST_Read('data.gpkg', layer = 'roads');
SELECT * FROM 'buildings.parquet';                          -- GeoParquet geometry is read as GEOMETRY
COPY (SELECT * FROM t) TO 'out.parquet' (FORMAT parquet);
COPY (SELECT * FROM t) TO 'out.gpkg' WITH (FORMAT GDAL, DRIVER 'GPKG');
```

## Measure

```sql
SELECT ST_Area(ST_Transform(geom, 'EPSG:4326', 'EPSG:2154')) / 1e4 AS ha FROM parcels;
SELECT ST_Distance_Spheroid(a, b);   -- meters on WGS 84, points in EPSG:4326
```

`ST_Area` and `ST_Distance` work in the units of the coordinates: degrees for lon/lat data.

## Spatial index and filters

```sql
CREATE INDEX parcels_rtree ON parcels USING RTREE (geom);
SELECT count(*) FROM parcels WHERE ST_Intersects(geom, ST_MakeEnvelope(2.33, 48.85, 2.35, 48.86));
```

On GeoParquet files, filter on the `bbox` struct columns (`bbox.xmin`, `bbox.ymin`, ...) so DuckDB skips row groups.

## Overture with DuckDB

Releases are dated and old ones are removed: read the latest from the STAC catalog. DuckDB reads every file's metadata, so even a small area takes minutes; for a plain download the `overturemaps` CLI is faster.

```sql
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

Without the `bbox` filter the query scans the whole world. Check theme and type names on docs.overturemaps.org.

Local snippets in this file were run on DuckDB 1.5.5 on 2026-10-11; the Overture query was not rerun (remote, minutes long).
