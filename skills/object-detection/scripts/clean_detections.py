"""Clean raw detection polygons merged from tiles and write a GeoPackage.

Steps, in order: reproject to a metric CRS, fix geometries, drop tiny polygons,
remove tile-edge duplicates (overlap IoU above a threshold, keep the higher score),
simplify, optionally make building outlines rectangular, then report counts.

    python clean_detections.py raw.gpkg clean.gpkg --crs EPSG:32631 \
        --min-area 10 --iou 0.5 --score-field score --simplify 0.5 --rectangles

Needs geopandas 1.x and shapely 2.x (both ship with the QGIS Python).
"""
import argparse
import sys

import geopandas as gpd
import numpy as np
from shapely import make_valid


def iou(a, b):
    inter = a.intersection(b).area
    union = a.area + b.area - inter
    return inter / union if union else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--crs", help="metric CRS, e.g. EPSG:32631; default: keep a projected input, else the UTM zone estimated from the data")
    ap.add_argument("--min-area", type=float, default=0.0, help="square meters")
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--score-field", default=None)
    ap.add_argument("--simplify", type=float, default=0.0, help="meters, about the pixel size")
    ap.add_argument("--rectangles", action="store_true", help="replace each polygon by its minimum rotated rectangle")
    ap.add_argument("--layer", default="detections")
    a = ap.parse_args()

    gdf = gpd.read_file(a.input)
    n0 = len(gdf)
    if gdf.crs is None:
        sys.exit("input has no CRS; set it before cleaning")
    target = a.crs or (gdf.estimate_utm_crs() if gdf.crs.is_geographic else gdf.crs)
    gdf = gdf.to_crs(target)
    print(f"read {n0} polygons, CRS now {gdf.crs.to_string()}")

    gdf["geometry"] = make_valid(gdf.geometry.values)
    gdf = gdf.explode(index_parts=False)
    gdf = gdf[gdf.geom_type == "Polygon"].copy()
    gdf = gdf[gdf.area >= a.min_area].copy()
    n1 = len(gdf)
    print(f"after fix and min area {a.min_area} m2: {n1}")

    # Tile-edge duplicates: greedy suppression, highest score (or largest area) first
    key = gdf[a.score_field] if a.score_field else gdf.area
    gdf = gdf.assign(_key=np.asarray(key)).sort_values("_key", ascending=False).reset_index(drop=True)
    sindex = gdf.sindex
    removed = np.zeros(len(gdf), dtype=bool)
    geoms = gdf.geometry.values
    for i in range(len(gdf)):
        if removed[i]:
            continue
        for j in sindex.query(geoms[i], predicate="intersects"):
            if j > i and not removed[j] and iou(geoms[i], geoms[j]) >= a.iou:
                removed[j] = True
    gdf = gdf[~removed].drop(columns="_key")
    print(f"duplicates removed (IoU >= {a.iou}): {int(removed.sum())}, left {len(gdf)}")

    if a.rectangles:
        gdf["geometry"] = gdf.geometry.minimum_rotated_rectangle()
    if a.simplify > 0:
        gdf["geometry"] = gdf.geometry.simplify(a.simplify, preserve_topology=True)
    gdf = gdf[gdf.is_valid & ~gdf.is_empty]

    gdf["area_m2"] = gdf.area.round(2)
    gdf.to_file(a.output, layer=a.layer, driver="GPKG")
    print(f"wrote {len(gdf)} polygons to {a.output} (layer {a.layer}); "
          f"total area {gdf.area.sum():.1f} m2, median {gdf.area.median():.1f} m2")


if __name__ == "__main__":
    main()
