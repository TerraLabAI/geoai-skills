# Land cover classification

Before classifying, check whether an existing map answers the question: ESA WorldCover 10 m (2020, 2021), Dynamic World (Earth Engine `GOOGLE/DYNAMICWORLD/V1`), national maps (for example OSO and OCS GE in France, NLCD in the US). Say which you checked. Classify only when the classes, the date or the resolution of those maps do not fit.

## Workflow

1. **Classes**: agree on a short list (for example water, built-up, cropland, grassland, forest, bare). Each class must be visible in the imagery at that resolution.
2. **Imagery**: one cloud-free composite for the date or season (see the composites section of the skill). Add features that separate the classes: NDVI, NDWI, NDBI, SWIR bands, a second season for crops, elevation and slope when relevant.
3. **Training samples**: polygons or points per class drawn on high-resolution imagery of the same period.
   - Spread them over the whole area, not one cluster per class.
   - Aim for at least 50 samples per class for accuracy assessment (Congalton's rule of thumb), more for training, and more for rare classes.
   - Keep a class code field (integer) and a class name field.
4. **Split before training**: hold out about 30 % of the samples for validation. Split by polygon, not by pixel: pixels from one polygon in both sets inflate accuracy. Better still, separate them in space (blocks).
5. **Train and predict**: Random Forest is the usual default (100 to 500 trees).
   - QGIS: the Semi-Automatic Classification Plugin or the Orfeo ToolBox provider (`TrainImagesClassifier`, `ImageClassifier`); check the tool names on the installed version.
   - Python: scikit-learn `RandomForestClassifier` on pixel values sampled under the training polygons (`rasterstats`, or `rasterio.mask`), then predict per block.
   - Earth Engine: `image.sampleRegions(collection=samples, properties=["class"], scale=10)`, `ee.Classifier.smileRandomForest(200).train(...)`, `image.classify(clf)`.
6. **Post-process**: majority filter or sieve (`gdal:sieve`) to remove isolated pixels; keep the minimum mapping unit stated.
7. **Accuracy assessment** on the held-out samples, never on the training ones:
   - Confusion matrix with reference in columns or rows (say which), overall accuracy, producer's accuracy (omission side) and user's accuracy (commission side) per class, kappa if the user asks for it (overall accuracy and per-class accuracies are more informative).
   - `python3 scripts/accuracy.py matrix.csv` or `--pairs ref_pred.csv` computes them.
   - Earth Engine: `validated.errorMatrix("class", "classification")` with `.accuracy()`, `.producersAccuracy()`, `.consumersAccuracy()`, `.kappa()`.
8. **Area by class**: count pixels per class times pixel area in a projected CRS (`native:rasterlayeruniquevaluesreport` in QGIS). Pixel counting is biased by classification errors; for reported area statistics, use the error-adjusted estimator of Olofsson et al. (2014) with a stratified random sample.
9. **Check the map**: look at it over imagery in five places, especially class borders, shadows and water versus dark roofs.

## Common traps

- Training and validation pixels from the same polygons: accuracy above 95 % that collapses on new samples.
- Classes too fine for the pixel size (single houses on 10 m Sentinel-2).
- Clouds or shadows left in the composite, classified as water or built-up.
- A composite from a different year than the training imagery.
- Reporting kappa alone without per-class accuracies.
