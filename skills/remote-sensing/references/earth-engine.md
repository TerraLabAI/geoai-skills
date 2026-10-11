# Google Earth Engine

Earth Engine needs a Google Cloud project registered for Earth Engine (`ee.Initialize(project="my-project")`). Code below is Python (`earthengine-api`); the JavaScript Code Editor uses the same method names.

## Collections and scaling

| Collection id | Content | To physical values | Display range after scaling |
| --- | --- | --- | --- |
| `COPERNICUS/S2_SR_HARMONIZED` | Sentinel-2 L2A, offset already removed for all dates | `B* / 10000` | 0 to 0.3 (RGB B4, B3, B2); on raw DN 0 to 3000 |
| `COPERNICUS/S2_HARMONIZED` | Sentinel-2 L1C, harmonized | `B* / 10000` | same |
| `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` | Cloud Score+ `cs`, `cs_cdf`, 0 to 1 | none | |
| `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2` | Landsat 8, 9 Level-2 | `SR_B* * 0.0000275 - 0.2`; `ST_B10 * 0.00341802 + 149.0` (K) | 0 to 0.3 |
| `LANDSAT/LE07/C02/T1_L2`, `LANDSAT/LT05/C02/T1_L2` | Landsat 7, 5 Level-2 | same scale; thermal is `ST_B6` | 0 to 0.3 |
| `COPERNICUS/S1_GRD` | Sentinel-1 GRD, already in dB (10 log10) | none; use `COPERNICUS/S1_GRD_FLOAT` for linear power | VV about -25 to 0 dB |
| `COPERNICUS/DEM/GLO30` | Copernicus DEM GLO-30, band `DEM` | none (meters) | |
| `ESA/WorldCover/v200` | ESA WorldCover 2021, band `Map` (classes 10 to 100) | none | |

Verified on 2026-10-11 against the Earth Engine Data Catalog pages for the Landsat 9 L2, Cloud Score+ and Sentinel-1 GRD collections; check the others' catalog pages before relying on a band name.

- `COPERNICUS/S2_SR` (not harmonized) is deprecated. Do not mix it with the harmonized one.
- Copernicus DEM GLO30 is an image collection of tiles: `ee.ImageCollection("COPERNICUS/DEM/GLO30").select("DEM").mosaic()`. A mosaic loses the native projection; pass `scale=30` (and a CRS) to every reduction and export.

## Sentinel-2 composite with Cloud Score+ and NDVI

```python
import ee
ee.Initialize(project="my-project")
aoi = ee.Geometry.Rectangle([2.25, 48.80, 2.42, 48.91])
cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
      .filterBounds(aoi)
      .filterDate("2025-06-01", "2025-09-01")
      .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
      .linkCollection(cs, ["cs_cdf"])
      .map(lambda img: img.updateMask(img.select("cs_cdf").gte(0.6))
                          .select(["B2", "B3", "B4", "B8", "B11", "B12"])
                          .divide(10000)
                          .copyProperties(img, ["system:time_start"])))
comp = s2.median().clip(aoi)
ndvi = comp.normalizedDifference(["B8", "B4"]).rename("NDVI")
nobs = s2.select("B4").count().rename("n_obs")
stats = ndvi.reduceRegion(reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True),
                          geometry=aoi, scale=10, maxPixels=1e9)
print(s2.size().getInfo(), stats.getInfo())
```

Checks: number of images used; `n_obs` minimum over the area (pixels with 0 have no data); NDVI mean within the expected range for the land cover.

## Landsat 8/9 mask and scale

```python
def prep_l89(img):
    qa = img.select("QA_PIXEL")
    mask = qa.bitwiseAnd(0b11111).eq(0)            # bits 0-4: fill, dilated cloud, cirrus, cloud, shadow
    sr = img.select("SR_B.").multiply(0.0000275).add(-0.2)
    st = img.select("ST_B10").multiply(0.00341802).add(149.0)
    return img.addBands(sr, None, True).addBands(st, None, True).updateMask(mask)

l89 = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
       .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
       .filterBounds(aoi).filterDate("2024-06-01", "2024-09-01").map(prep_l89))
```

## reduceRegion and exports: scale is not optional

- Always pass `scale` (meters) equal to the native pixel: 10 for Sentinel-2 10 m bands, 20 for B11/B12, 30 for Landsat, 10 for Sentinel-1. Without it Earth Engine uses the image's default projection, which for a composite is EPSG:4326 at 1 degree per pixel (about 111 km), and statistics come out wrong silently.
- `maxPixels=1e9` (or `1e13` for large exports). `bestEffort=True` changes the scale silently; avoid it for reported numbers.
- Areas: `ee.Image.pixelArea()` (m2) times a mask, summed with `ee.Reducer.sum()` at the native scale. Do not count pixels times a nominal size when the CRS is geographic.
- Per-polygon statistics: `image.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=10)`.
- Export: `ee.batch.Export.image.toDrive(image=..., region=aoi, scale=10, crs="EPSG:32631", maxPixels=1e9)`; set `crs` to a projected CRS for analysis outputs.
- `getInfo()` on large objects times out; export instead.

## Time series

Map a function that returns an `ee.Feature` with the date and the regional mean at native scale, then export the table. Keep the same mask and scaling for every date, and drop dates with too few valid pixels (compute the valid count with `ee.Reducer.count()` alongside the mean).
