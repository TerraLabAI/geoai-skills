# PostGIS recipes

## Clustering

```sql
-- density based: points within 200 m, at least 5 per cluster (projected SRID in meters)
SELECT id, ST_ClusterDBSCAN(geom, eps := 200, minpoints := 5) OVER () AS cluster_id
FROM incidents;

-- fixed number of clusters
SELECT id, ST_ClusterKMeans(geom, 8) OVER () AS cluster_id FROM stores;
```

`ST_ClusterDBSCAN` returns NULL for noise points. Report the number of clusters and of noise points.

## Dissolve by attribute

```sql
SELECT owner, ST_Multi(ST_Union(geom)) AS geom, sum(ST_Area(geom)) AS area_before
FROM parcels GROUP BY owner;
```

Compare `ST_Area` of the union with `area_before`: the union is smaller only where parcels overlapped.

## Clip to a study area

```sql
SELECT p.id, ST_Intersection(p.geom, a.geom) AS geom
FROM parcels p JOIN area a ON ST_Intersects(p.geom, a.geom);
```

`ST_Intersection` can return lower-dimension parts (lines where polygons only touch): keep polygons with `ST_CollectionExtract(..., 3)`.

## Buffer in meters from 4326 data

```sql
SELECT id, ST_Buffer(geom::geography, 500)::geometry AS geom FROM wells;
```

## Line length per zone

```sql
SELECT z.id, sum(ST_Length(ST_Intersection(r.geom, z.geom))) AS road_m
FROM zones z JOIN roads r ON ST_Intersects(r.geom, z.geom)
GROUP BY z.id;
```

Run in a projected SRID; check the sum against the total road length inside the study area.
