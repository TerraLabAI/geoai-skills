---
name: object-detection
description: Detects, segments and counts objects such as buildings, trees, cars, solar panels, swimming pools and ships in aerial, drone or satellite imagery, then cleans and validates the polygons. Covers the ground resolution each object needs (Sentinel-2 at 10 m cannot find cars or houses), tiling with overlap, open model options (geoai, samgeo text prompts, YOLO, Detectron2, torchgeo) with their licenses, the limits of vision-language models for counting, cleaning outputs (tile seams, minimum area, regularized building outlines, merging), precision and recall on a hand-labeled sample, and export to GeoPackage. Use when someone wants to detect, segment, extract, count or map buildings, trees, cars, solar panels, pools or ships from imagery, an orthophoto or a GeoTIFF, asks which model or resolution to use, or gets duplicated, missing or jagged detections.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
  version: "1.1.0"
---

# Object detection in imagery

A detection run is done when the cleaned polygons are counted, spot-checked and scored on a labeled sample, not when the model returned output.

## When to use

- "Count the trees", "extract building footprints", "find solar panels / pools / cars / ships", "segment this orthophoto".
- Requests arrive in any language; the workflow does not depend on the wording.

## Workflow

Do the steps in order. Each has a check; stop and tell the user when a check fails instead of quietly changing the task.

1. **Define the object and the output.** Which objects, which area, which date, and what the user needs: a count, footprints (polygons), boxes or points. Check: one sentence like "Building footprints in this 2 km² orthophoto, as polygons in a GeoPackage".
2. **Inspect the imagery.** `gdalinfo image.tif`: CRS, pixel size, band count and data type, NoData, extent. Check: the pixel size is in meters (projected CRS) and the bands are what the model expects.
3. **Check resolution against the object.** Rule: the object needs at least 3 to 5 pixels across its smallest side to be detected, 10 or more for clean outlines. Use the table below. If the imagery is too coarse, say so and propose suitable imagery; never upsample to fake detail. Check: smallest object size / pixel size is at least 3 to 5.
4. **Prepare.** Keep the native CRS and pixel grid; RGB in R, G, B order, 8-bit for most models (16-bit: percentile stretch, for example 2 to 98 percent, not a plain divide); drop alpha. Check: a tile looks like a normal photo.
5. **Tile with overlap.** Tile size = model input (often 512 or 1024 px), overlap at least the largest object in pixels, commonly 10 to 25 percent. Many packages tile for you; set their overlap. Check: tile count times tile area covers the image.
6. **Pick and run a model.** See the model table and [references/models.md](references/models.md). Run first on a small extract and look at it before the whole image. Check: detections line up with the objects on the imagery.
7. **Clean.** `scripts/clean_detections.py`: metric CRS, fix geometries, minimum area, remove tile-edge duplicates, simplify, optional rectangles for buildings. Check: printed counts at each step make sense.
8. **Validate.** Spot-check 20 to 50 random places, then score on a hand-labeled sample with `scripts/score_detections.py` (precision, recall, F1 at IoU 0.5). Check: numbers reported with area and imagery date.
9. **Deliver.** GeoPackage with area and score fields, the count, the scores, and the code that was run.

## Resolution needed per object

Ground sampling distance (GSD) is the ground size of one pixel.

| Object | Typical size | GSD needed | Usable sources |
|---|---|---|---|
| Buildings (houses) | 8 to 20 m | 0.5 m or finer; 1 m for large buildings only | aerial orthophotos, very high resolution satellite |
| Cars | 4.5 x 1.8 m | 0.3 m or finer | aerial orthophotos, drone |
| Trees (crowns) | 3 to 15 m | 0.5 m or finer | aerial, drone |
| Solar panels (rooftop) | about 1 x 1.7 m per module | 0.3 m or finer | aerial orthophotos, drone |
| Swimming pools | 4 to 12 m | 0.5 m or finer | aerial orthophotos |
| Ships | 10 to 300 m | 1 to 3 m for large ships; 10 m Sentinel-2 or Sentinel-1 radar only for large vessels | satellite |
| Fields, forest stands, water bodies | 100 m and up | 10 m works | Sentinel-2 |

Sentinel-2 is 10 m at best (B2, B3, B4, B8): a car is less than one pixel, a house one or two.

Do not detect on basemap tiles (Google, Bing): their terms forbid analysis and the capture date is unknown. Use an orthophoto or drone GeoTIFF with a stated license.

## Open model options

Licenses checked on GitHub on 2026-10-11. Pretrained weights can carry a license different from the code: check both before commercial use.

| Option | Install | Good for | Code license |
|---|---|---|---|
| geoai (opengeos) | `pip install geoai-py` | pretrained detectors on RGB imagery: `BuildingFootprintExtractor`, `CarDetector`, `ShipDetector`, `SolarPanelDetector`; writes georeferenced vectors | MIT |
| samgeo (segment-geospatial) | `pip install segment-geospatial` | segmentation with Segment Anything, text prompts ("tree", "swimming pool") via `LangSAM` | MIT |
| Ultralytics YOLO | `pip install ultralytics` | fast boxes or masks after fine-tuning on your own labels | AGPL-3.0 (enterprise license for closed products) |
| Detectron2 | from GitHub (facebookresearch/detectron2) | Mask R-CNN style instance segmentation, custom training | Apache-2.0 |
| torchgeo | `pip install torchgeo` | geospatial datasets, samplers and pretrained backbones (multispectral) for training your own model | MIT |

Choose by need: a supported object on RGB imagery, try a pretrained geoai detector; an object with no pretrained model, text-prompted segmentation then fine-tuning; many images of the same kind, train a detector on 200 or more labeled examples.

## Vision-language models

Chat models that look at an image (GPT-4o, open VLMs) are not reliable counters or detectors on overhead imagery. On GEOBench-VLM (ICCV 2025, over 10,000 questions on counting, detection, segmentation and change), the best model, LLaVA-OneVision, reached 41.7 percent accuracy on multiple-choice questions, about twice random guessing, with GPT-4o close behind. Use them to describe a scene or triage tiles, never as the count delivered to a user.

## Clean and validate

```bash
# QGIS Python or any env with geopandas 1.x and shapely 2.x
python scripts/clean_detections.py raw.gpkg buildings.gpkg --min-area 10 --iou 0.5 \
    --score-field score --simplify 0.5 --rectangles
python scripts/score_detections.py buildings.gpkg labels.gpkg labeled_area.gpkg --iou 0.5
```

Details, QGIS Processing equivalents, and how to build the labeled sample: [references/cleaning-validation.md](references/cleaning-validation.md).

| Metric | Formula | Says |
|---|---|---|
| Precision | TP / (TP + FP) | how many detections are real |
| Recall | TP / (TP + FN) | how many real objects were found |
| F1 | 2PR / (P + R) | one number for both |

## Core checks

- Resolution fits the object before any model runs.
- A small extract was run and looked at first.
- Counts printed after each cleaning step; the final count is stated with area and date.
- Precision and recall measured on a labeled sample not used for tuning.
- When the imagery cannot answer (too coarse, clouds, wrong date), the answer says so.

## Going further

AI Segmentation for QGIS detects and segments objects in imagery with its own models and returns polygons: https://terra-lab.ai/ai-segmentation?utm_source=skills&utm_medium=geoai-skills&utm_campaign=object-detection
