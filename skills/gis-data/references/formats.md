# Vector formats

| Format | Use for | Limits and traps |
| --- | --- | --- |
| GeoPackage (`.gpkg`) | Default for exchange and QGIS work | One SQLite file, several layers, UTF-8, long field names, spatial index |
| GeoParquet (`.parquet`) | Large analytic data, DuckDB, cloud | Columnar; read with GDAL 3.5+ (Parquet driver), DuckDB, GeoPandas |
| Shapefile (`.shp` + `.shx` + `.dbf` + `.prj`, often `.cpg`) | Only when a tool demands it | Field names cut to 10 characters, 2 GB per file, one geometry type per file, no NULL vs empty distinction in many fields, encoding in `.cpg`; a missing `.prj` means unknown CRS |
| GeoJSON | Small web exchange | RFC 7946: always WGS 84 lon/lat, no other CRS; large files are slow |
| KML / KMZ | Google Earth exchange | WGS 84 lon/lat; styles and folders do not map well to attributes |
| CSV with coordinates | Tables from spreadsheets, GPS logs | No CRS stored: ask or state it; check which column is lat and which is lon |
| FlatGeobuf (`.fgb`) | Fast streaming of one layer | One layer per file |

Truncation example (GDAL 3.13): writing a field `a_very_long_field_name` to Shapefile gives `a_very_lon` with the warning "Normalized/laundered field name". Two long names that share their first 10 characters get renamed further, so map fields explicitly before export or avoid Shapefile.

## Reading CSV coordinates

```bash
ogr2ogr -f GPKG pts.gpkg pts.csv -oo X_POSSIBLE_NAMES=lon,longitude,x -oo Y_POSSIBLE_NAMES=lat,latitude,y \
        -oo KEEP_GEOM_COLUMNS=NO -a_srs EPSG:4326
```

GeoPandas:

```python
import geopandas as gpd, pandas as pd
df = pd.read_csv("pts.csv")
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs=4326)
```

Sanity check: plot or print the extent. Latitudes must stay within -90 to 90; a "latitude" column with values like 2.35 and "longitude" like 48.85 in France means the columns are swapped.

## Raster formats

GeoTIFF for exchange; Cloud Optimized GeoTIFF (`gdal_translate -of COG in.tif out.tif`) for files read over HTTP. Always check nodata, data type and pixel size with `gdalinfo`.

Verified by running GDAL 3.13 `ogr2ogr` on 2026-10-11 (CSV, KML, Parquet, Shapefile truncation).
