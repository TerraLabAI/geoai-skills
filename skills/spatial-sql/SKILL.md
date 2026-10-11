---
name: spatial-sql
description: Writes and checks spatial SQL in PostGIS and DuckDB spatial. Covers SRID and ST_Transform before measuring, geometry vs geography, spatial indexes (GiST, R-tree) and the && operator, ST_DWithin instead of ST_Distance in WHERE, ST_Intersects vs ST_Contains vs ST_Within, nearest neighbor with <->, ST_MakeValid, ST_Subdivide, clustering (ST_ClusterDBSCAN, ST_ClusterKMeans), DuckDB ST_Read, GeoParquet and bbox filters on Overture data, axis order in DuckDB, loading data with ogr2ogr or shp2pgsql, and checking a query with EXPLAIN and counts. Use when the user writes SQL with ST_ functions, asks about PostGIS, PostgreSQL, Supabase or DuckDB spatial, a spatial join, points in polygons, distance or buffer queries, nearest neighbor, a slow spatial query, loading a shapefile or GeoPackage into a database, querying GeoParquet or Overture with SQL, or gets wrong distances or areas from SQL.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
  version: "1.1.0"
---

# Spatial SQL

Most wrong answers from spatial SQL run without error: a distance in degrees, a join that drops boundary features, a query that scans every row. Inspect the tables first, write the query in the order below, and check the result with counts.

## Core rules

1. Inspect first: SRID, geometry type, row count, extent, validity, and whether an index exists.
2. Every geometry in one predicate shares one SRID. Measure in meters: `ST_Transform` to a projected SRID, or cast to `geography`.
3. Filter with index-friendly predicates (`ST_Intersects`, `ST_DWithin`, `&&`), never `ST_Distance(...) < x` in a WHERE.
4. Choose the predicate on purpose: `ST_Intersects` includes boundary touches, `ST_Contains` and `ST_Within` exclude points on the boundary.
5. Check: row counts before and after, unmatched rows in a join, one number recomputed another way. Read `EXPLAIN` when a query is slow.
6. Return the full SQL that was run.

## Workflow index

| Task | Where |
| --- | --- |
| Inspect a table | A |
| Points in polygons, spatial join | B |
| Within a distance, nearest neighbor | C |
| Areas, lengths | D |
| Invalid or huge geometries | E |
| Slow query | F |
| Load data | [references/loading.md](references/loading.md) |
| DuckDB, GeoParquet, Overture | [references/duckdb.md](references/duckdb.md) |
| Clustering | [references/postgis-recipes.md](references/postgis-recipes.md) |

## A. Inspect (PostGIS)

```sql
SELECT f_table_name, f_geometry_column, srid, type FROM geometry_columns;
SELECT count(*) AS n, count(*) FILTER (WHERE NOT ST_IsValid(geom)) AS invalid,
       count(*) FILTER (WHERE geom IS NULL) AS null_geom,
       ST_Extent(geom) AS extent, min(ST_SRID(geom)) AS srid_min, max(ST_SRID(geom)) AS srid_max
FROM parcels;
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'parcels';
```

Red flags: SRID 0 (unknown), extent in degrees for a "meters" table, mixed SRIDs, no GiST index on a large table.

## B. Points in polygons

```sql
SELECT z.id, count(p.id) AS n_points
FROM zones z
LEFT JOIN points p ON ST_Intersects(z.geom, p.geom)
GROUP BY z.id;
```

- `LEFT JOIN` keeps zones with zero points; an inner join hides them.
- Check: `SELECT sum(n_points)` against `count(*)` of points. More means overlapping zones count a point twice; fewer means points outside all zones (report how many).
- If the two tables have different SRIDs, transform the smaller side, ideally once into a new table, not inside the join.

## C. Distance and nearest

```sql
-- within 500 m, table in a projected SRID in meters (here 2154)
SELECT a.id, b.id FROM wells a JOIN schools b ON ST_DWithin(a.geom, b.geom, 500);

-- table in 4326: geography gives meters on the spheroid
SELECT a.id, b.id FROM wells a JOIN schools b
  ON ST_DWithin(a.geom::geography, b.geom::geography, 500);

-- k nearest neighbors; the GiST index is used because the probe geometry is constant per lateral row
SELECT n.id, n.name, n.d
FROM (SELECT geom FROM wells WHERE id = 42) w
CROSS JOIN LATERAL (
  SELECT s.id, s.name, ST_Distance(s.geom, w.geom) AS d
  FROM schools s ORDER BY s.geom <-> w.geom LIMIT 5) n;

-- nearest school for every well
SELECT w.id, n.id AS school_id, n.d
FROM wells w
CROSS JOIN LATERAL (
  SELECT s.id, ST_Distance(w.geom, s.geom) AS d FROM schools s
  ORDER BY w.geom <-> s.geom LIMIT 1) n;
```

`<->` on SRID 4326 geometry orders by degrees; use a projected copy or `geography`. `ST_DWithin(geom_4326, geom_4326, 500)` means 500 degrees: always wrong. A geography cast without a matching index is slow on large tables; prefer a projected copy with its own GiST index.

## D. Areas and lengths

```sql
SELECT id, ST_Area(ST_Transform(geom, 2154)) / 10000 AS area_ha FROM parcels;   -- projected
SELECT id, ST_Area(geom::geography) AS area_m2 FROM parcels;                    -- 4326, spheroid
```

Never `ST_Area(geom)` on SRID 4326 (square degrees) or 3857 (inflated away from the equator). Cross-check a total both ways; the two should agree within about 1 percent for a national CRS.

## E. Invalid and heavy geometries

```sql
UPDATE parcels SET geom = ST_Multi(ST_CollectionExtract(ST_MakeValid(geom), 3))
WHERE NOT ST_IsValid(geom);
```

`ST_MakeValid` can return a GeometryCollection; `ST_CollectionExtract(..., 3)` keeps polygons (1 points, 2 lines). Very large polygons (countries, coastlines) make every intersect slow: split them once with `ST_Subdivide(geom, 256)` into a new indexed table and query that.

## F. Performance

```sql
CREATE INDEX ON parcels USING GIST (geom);
ANALYZE parcels;
EXPLAIN ANALYZE SELECT ... ;
```

Look for "Index Scan" or "Bitmap Index Scan" on the GiST index. A "Seq Scan" on a large table usually means: no index, a function wrapped around the indexed column (`ST_Transform(geom, ...)` in the WHERE), a geography cast, or `ST_Distance` in the WHERE. Index the expression you filter on, or store the transformed geometry.

## Before handing over

- [ ] SRIDs checked and stated; measures in meters.
- [ ] Predicate chosen on purpose (boundary cases).
- [ ] Row counts: inputs, output, unmatched.
- [ ] One number cross-checked.
- [ ] SQL returned to the user.

## Going further

The TerraLab MCP server extracts open data (buildings, roads, places) for an area from any AI assistant, ready to load into PostGIS or DuckDB: https://terra-lab.ai/mcp?utm_source=skills&utm_medium=geoai-skills&utm_campaign=spatial-sql
