# Cleaning and validating detections

## Cleaning steps, in order

| Step | Why | Script option | QGIS Processing |
|---|---|---|---|
| Reproject to a metric CRS | areas and tolerances in meters | `--crs` (default: keep projected input, else UTM) | `native:reprojectlayer` |
| Fix geometries | vectorized masks often self-intersect | always | `native:fixgeometries` |
| Minimum area | drop noise and slivers | `--min-area` (m²) | `native:extractbyexpression` with `$area >= 10` |
| Tile-edge duplicates | overlapping tiles detect an object twice | `--iou 0.5`, `--score-field` | no single tool; use the script |
| Simplify | jagged pixel edges | `--simplify` about the pixel size | `native:simplifygeometries` |
| Regularize buildings | rectangular outlines | `--rectangles` (minimum rotated rectangle) | `native:orientedminimumboundingbox`, or `native:orthogonalize` for L shapes |
| Merge split objects | an object cut by a seam into two touching parts | after dedupe, dissolve only parts that touch across a seam | `native:dissolve` on a seam-flag field |

Typical minimum areas: buildings 10 m², pools 4 m², solar panel arrays 2 m², tree crowns 2 m². Adjust to the place.

`--rectangles` suits simple houses; for complex buildings use `native:orthogonalize`, which keeps L and U shapes.

Print the count after each step. A step that removes more than about 20 percent deserves a look.

## Labeled sample

1. Pick 3 to 5 small areas (for example 200 x 200 m each) spread across the image and its land types, not the areas used to tune thresholds.
2. In QGIS, draw every object inside those areas as polygons (a reference layer), and draw the areas themselves (labeled area layer). Aim for 100 to 200 objects in total.
3. Run `scripts/score_detections.py detections.gpkg reference.gpkg labeled_area.gpkg --iou 0.5`.
4. Report precision, recall, F1, the IoU threshold, the imagery date and the area. For counts only (trees, cars), an IoU of 0.3 or a center-in-polygon match is acceptable; say which was used.

## Second check on the total

Cross-check the final count a second way: count by hand on one random 100 x 100 m cell and compare with detections in that cell, or compare total building area with an official footprint layer when one exists.

## Export

GeoPackage, one layer, with fields: `area_m2`, model score, model name and version, imagery source and date. `gdf.to_file("out.gpkg", layer="buildings", driver="GPKG")`.
