# Loading data into PostGIS

Enable the extension once: `CREATE EXTENSION IF NOT EXISTS postgis;`

## ogr2ogr (any GDAL format)

```bash
ogr2ogr -f PostgreSQL "PG:host=localhost dbname=gis user=me" parcels.gpkg parcels \
  -nln public.parcels -lco GEOMETRY_NAME=geom -lco SPATIAL_INDEX=GIST \
  -nlt PROMOTE_TO_MULTI -t_srs EPSG:2154 -makevalid
```

- `-nlt PROMOTE_TO_MULTI` avoids failures when a layer mixes Polygon and MultiPolygon.
- `-t_srs` reprojects on the way in; omit it to keep the source CRS.
- `-append` adds to an existing table, `-overwrite` replaces it.
- Pass the password through `PGPASSWORD` or `~/.pgpass`, never in the command line of a shared log.

## shp2pgsql (Shapefile only)

```bash
shp2pgsql -s 2154 -I -D parcels.shp public.parcels | psql -d gis
```

`-s` sets the SRID (it does not reproject; use `-s 4326:2154` to transform), `-I` creates a GiST index, `-D` uses the faster dump format.

## After loading

```sql
SELECT count(*), ST_SRID(geom), GeometryType(geom) FROM parcels GROUP BY 2, 3;
SELECT ST_Extent(geom) FROM parcels;
ANALYZE parcels;
```

Compare the row count with `ogrinfo -so source.gpkg layer`.
