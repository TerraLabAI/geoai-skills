# Running open models

Package names, classes and licenses checked on 2026-10-11 (opengeoai.org, samgeo.gishub.org, GitHub). APIs move between versions: check the installed version's docs if a call fails. A GPU helps; on CPU, start with a small extract.

## geoai pretrained detectors

```python
import geoai

detector = geoai.BuildingFootprintExtractor()   # or CarDetector(), ShipDetector(), SolarPanelDetector()
masks = detector.generate_masks(
    raster_path="ortho.tif", output_path="masks.tif",
    confidence_threshold=0.5, mask_threshold=0.5, overlap=0.25, chip_size=(512, 512))
gdf = detector.vectorize_masks(masks_path="masks.tif", output_path="detections.geojson",
                               min_object_area=100)  # area in pixels
```

The pretrained models were trained on specific imagery (for example US aerial imagery for buildings); expect lower recall elsewhere and score it.

## samgeo text prompts

```python
from samgeo.text_sam import LangSAM

sam = LangSAM()
sam.predict("ortho.tif", "swimming pool", box_threshold=0.24, text_threshold=0.24,
            output="pools_mask.tif")          # georeferenced mask raster
sam.raster_to_vector("pools_mask.tif", "pools.gpkg")
```

Text prompts work for visually distinct objects (pools, trees, solar arrays); they confuse similar things (pools versus blue tarps). Tune the thresholds on a small extract and keep the values.

## Train your own (YOLO, Detectron2, torchgeo)

1. Label 200 or more objects across varied places (QGIS polygons on the imagery), plus areas with none.
2. Export image chips and labels in the tool's format; keep 20 percent of areas aside for validation, split by area, not by chip, or neighboring chips leak.
3. Train, predict on the held-out areas, clean, then score with `scripts/score_detections.py`.

Ultralytics YOLO is AGPL-3.0: a service or product that uses it must publish its source or buy the enterprise license. Detectron2 is Apache-2.0, torchgeo MIT.

## When not to use a model

- Few objects (under about 50): digitize by hand in QGIS, faster and exact.
- Official footprints already exist (national cadastre, OpenStreetMap, Overture buildings): download them, then detect only what changed.
