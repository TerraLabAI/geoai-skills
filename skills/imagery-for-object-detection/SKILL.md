---
name: imagery-for-object-detection
description: Prepares aerial, drone or satellite imagery before running an object detection or segmentation model, then checks the polygons it returns. Covers the ground sampling distance each object needs (buildings, cars, trees, solar panels, swimming pools), why Sentinel-2 at 10 m cannot find cars or small buildings, tile size and overlap, RGB versus multispectral, reprojection and resampling pitfalls, and result QA (tile-edge duplicates, minimum area, simplify, merge, spot checks, precision and recall). Use when someone wants to detect, count, segment or extract buildings, cars, trees, solar panels or pools from imagery, asks which imagery or resolution to use, or gets bad or duplicated detections.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
---

# Imagery for object detection

This skill is about the imagery and the results, not the model.

## What goes wrong without this skill

- Running detection on imagery too coarse for the object (cars on Sentinel-2).
- Reprojecting or resampling the image before inference and blurring the objects.
- Tiling without overlap, so objects cut by tile edges are missed or split.
- Delivering raw output: duplicates on tile edges, slivers, jagged polygons.
- Reporting "it worked" without counting errors on a labelled sample.

## 1. Check the resolution fits the object

Ground sampling distance (GSD) is the ground size of one pixel. An object should cover several pixels across, ideally 10 or more, for reliable outlines.

| Object | Typical size | GSD needed | Usable sources |
|---|---|---|---|
| Buildings (houses) | 8 to 20 m | 0.5 m or finer; 1 m for large buildings only | aerial orthophotos, very high resolution satellite |
| Cars | 4.5 x 1.8 m | 0.3 m or finer | aerial orthophotos, drone |
| Trees (crowns) | 3 to 15 m | 0.5 m or finer | aerial, drone |
| Solar panels (rooftop) | about 1 x 1.7 m per module | 0.3 m or finer | aerial orthophotos, drone |
| Swimming pools | 4 to 12 m | 0.5 m or finer | aerial orthophotos |
| Fields, forest stands, water bodies | 100 m and up | 10 m works | Sentinel-2 |

Sentinel-2 is 10 m at best (bands B2, B3, B4, B8). A car is less than one pixel and a house is one or two pixels: it can map built-up areas and fields, not individual cars, panels or small buildings. Upsampling it does not add detail.

Read the real GSD before anything else: `gdalinfo image.tif` (Pixel Size), in a projected CRS so the unit is metres.

## 2. Bands

- Most detection and segmentation models are trained on 3-band RGB, 8-bit. Feed them RGB in that order.
- Multispectral (with near infrared) helps vegetation and water, but only with a model trained on those bands.
- Convert 16-bit imagery to 8-bit with a percentile stretch (for example 2 to 98 %), not a plain divide, or the image comes out dark.
- Drop the alpha band and keep nodata areas out of tiles.

## 3. Reprojection and resampling

- Keep the native CRS and pixel grid when possible. Reproject the vector results afterwards, not the image.
- If you must warp, use bilinear or cubic for imagery, never nearest (blocky edges), and keep the original pixel size (`gdalwarp -tr`).
- Do not detect on Web Mercator tiles at a zoom coarser than the GSD you need. At zoom 18 a web tile pixel is about 0.6 m at the equator and gets smaller toward the poles.
- Check the warped image still lines up with a reference layer.

## 4. Tile size and overlap

| Setting | Rule |
|---|---|
| Tile size | the model's input size, often 512 or 1024 pixels |
| Overlap | at least the largest object size in pixels, commonly 10 to 25 % |
| Edges | pad the last row and column instead of dropping them |
| Empty tiles | skip tiles that are all nodata |

```bash
# 1024 px tiles with 128 px overlap, each tile keeps its georeference
gdal_retile.py -ps 1024 1024 -overlap 128 -targetDir tiles/ image.tif
```

## 5. Check the results

Run these in order on the merged output.

1. **Reproject** the polygons to a projected CRS in metres.
2. **Fix geometries** (QGIS `native:fixgeometries`, `ST_MakeValid`, shapely `make_valid`).
3. **Remove tile-edge duplicates**: where two polygons overlap by more than about 50 % (intersection over union), keep the higher score. Then dissolve touching pieces of the same object split by a tile edge.
4. **Minimum area filter**: drop polygons below a plausible size (for example 10 m² for buildings, 2 m² for panels).
5. **Simplify** with a tolerance near the GSD (`native:simplifygeometries`, `ST_SimplifyPreserveTopology`), and for buildings optionally orthogonalize (`native:orthogonalize`).
6. **Spot-check**: open 20 to 50 random locations over the imagery and look.
7. **Measure** on a small hand-labelled set (for example 100 to 200 objects in a few areas not used for tuning):

| Metric | Formula | Says |
|---|---|---|
| Precision | TP / (TP + FP) | how many detections are real |
| Recall | TP / (TP + FN) | how many real objects were found |
| F1 | 2PR / (P + R) | one number for both |

Count a match when a detection overlaps a labelled object with IoU of 0.5 or more. Report the numbers with the area and imagery date.

## Going further

AI Segmentation for QGIS detects objects in imagery and returns polygons: https://terra-lab.ai/ai-segmentation?utm_source=skills&utm_medium=geoai-skills&utm_campaign=imagery-for-object-detection
