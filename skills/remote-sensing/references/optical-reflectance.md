# Optical reflectance, cloud masks and band grids

Facts reviewed 2026-10-11.

## Common mistakes

- Dividing DN by 10000 on scenes from processing baseline 04.00 or later without the -1000 offset. Reflectance is biased by +0.1, NDVI is pulled toward 0, and time series show a jump on 25 January 2022.
- Applying the offset twice, on data that is already harmonized (Earth Engine `S2_SR_HARMONIZED`, Sentinel Hub with `harmonizeValues=true`, STAC assets whose metadata already declares it).
- Computing integer division or index math on uint16 arrays, so the result is 0 or overflows. Cast to float first.
- Using all SCL classes as valid, so clouds and shadows enter the index.
- Treating DN 0 as a dark pixel. 0 is NO_DATA.

## Step 1: L1C or L2A

| Level | Content | Use for |
| --- | --- | --- |
| L1C | Top-of-atmosphere reflectance | Atmospheric work, or where L2A is missing |
| L2A | Bottom-of-atmosphere (surface) reflectance + SCL, AOT, WVP | Indices, time series, land cover. Default choice. |

B10 (cirrus) exists only in L1C. Only L2A has the SCL band.

## Step 2: convert DN to reflectance, once

ESA formula for L2A (baseline 04.00 and later):

```
reflectance = (DN + BOA_ADD_OFFSET) / QUANTIFICATION_VALUE
            = (DN - 1000) / 10000
```
For baselines before 04.00 there is no offset: `reflectance = DN / 10000`. L1C uses `RADIO_ADD_OFFSET = -1000` in the same way. DN 0 stays NO_DATA.

Decide which case applies:

1. Read the product's processing baseline: `PROCESSING_BASELINE` in Earth Engine, `s2:processing_baseline` in STAC, or `<PROCESSING_BASELINE>` in `MTD_MSIL2A.xml`. 04.00 or higher means the raw DN carry the offset.
2. Check whether the provider already removed it:
   - Earth Engine `COPERNICUS/S2_SR_HARMONIZED` and `COPERNICUS/S2_HARMONIZED`: already shifted. Use `DN / 10000` for every date. The non-harmonized `COPERNICUS/S2_SR` is deprecated.
   - Microsoft Planetary Computer `sentinel-2-l2a`: raw DN, not harmonized. Apply the offset yourself on baseline 04.00+.
   - STAC `raster:bands` with `scale` and `offset`: apply `DN * scale + offset`, except on Earth Search `sentinel-2-l2a` items where `earthsearch:boa_offset_applied` is true: their DN are already shifted, so use `DN / 10000`. Prefer Earth Search `sentinel-2-c1-l2a`, whose metadata is correct.
   - Sentinel Hub / Copernicus Data Space process API: `harmonizeValues` defaults to true: DN are shifted to match old baselines (DN = 10000 x reflectance) and negatives are clamped to 0.
   - SAFE products from Copernicus Data Space: raw. Read `BOA_ADD_OFFSET` from the metadata.
   - CDSE now serves only processing baseline 05.xx before December 2023 (reprocessed), so old scenes there carry the offset too.
3. Sanity check after conversion: clear water in NIR is near 0 to 0.05, dense vegetation NIR about 0.3 to 0.5. A median above 0.1 over water means the offset was missed.

```python
import numpy as np
dn = band.astype("float32")
nodata = dn == 0
refl = (dn - 1000.0) / 10000.0 if baseline >= 4.0 else dn / 10000.0
refl[nodata] = np.nan
```
Small negative reflectance after the offset is real noise over dark surfaces. Keep it or clip to 0, but do not drop the pixel silently.

## Step 3: mask clouds with SCL (L2A)

| SCL | Class | Action |
| --- | --- | --- |
| 0 | No data | mask |
| 1 | Saturated or defective | mask |
| 2 | Dark area pixels / topographic shadows | usually keep, mask in steep terrain if needed |
| 3 | Cloud shadows | mask |
| 4 | Vegetation | keep |
| 5 | Not vegetated | keep |
| 6 | Water | keep |
| 7 | Unclassified / cloud low probability | keep, or mask for strict analyses |
| 8 | Cloud medium probability | mask |
| 9 | Cloud high probability | mask |
| 10 | Thin cirrus | mask |
| 11 | Snow or ice | mask unless you study snow |

```python
valid = ~np.isin(scl, [0, 1, 3, 8, 9, 10, 11])
```
SCL is 20 m. Resample it to 10 m with nearest neighbor only, never bilinear. SCL misses thin cloud edges: buffer the mask by a pixel or two, or add `MSK_CLDPRB` / s2cloudless probabilities for stricter work.

## Step 4: bands and resampling

| Band | Name | Central wavelength, S2A (nm) | Resolution |
| --- | --- | --- | --- |
| B1 | Coastal aerosol | 443 | 60 m |
| B2 | Blue | 492 | 10 m |
| B3 | Green | 560 | 10 m |
| B4 | Red | 665 | 10 m |
| B5 | Red edge 1 | 704 | 20 m |
| B6 | Red edge 2 | 740 | 20 m |
| B7 | Red edge 3 | 783 | 20 m |
| B8 | NIR | 833 | 10 m |
| B8A | Narrow NIR | 865 | 20 m |
| B9 | Water vapor | 945 | 60 m |
| B10 | SWIR cirrus (L1C only) | 1374 | 60 m |
| B11 | SWIR 1 | 1614 | 20 m |
| B12 | SWIR 2 | 2202 | 20 m |

Verified on 2026-10-11 against https://sentiwiki.copernicus.eu/web/s2-products.

- Mixing 10 m and 20 m bands: resample the 20 m band to 10 m (bilinear for reflectance) on the exact same grid, or aggregate the 10 m band to 20 m (average). Both rasters must share CRS, origin and pixel size.
- Pair B8A with B11 or B12 when you want matching 20 m footprints; B8 with B4 for 10 m NDVI.

## Landsat Collection 2 Level-2

| Band group | Scale | Offset | Result |
| --- | --- | --- | --- |
| `SR_B1` to `SR_B7` | 0.0000275 | -0.2 | surface reflectance |
| `ST_B10` (Landsat 8, 9), `ST_B6` (Landsat 4, 5, 7) | 0.00341802 | 149.0 | surface temperature in kelvin |

Verified on 2026-10-11 against the Earth Engine catalog page `LANDSAT/LC09/C02/T1_L2` (USGS Collection 2 Level-2 values).

- Valid SR DN range is 1 to 65455; 0 is fill. Reflectance can come out slightly negative or above 1; clip to 0 to 1 for indices, but count those pixels.
- Landsat 8 and 9 bands: B2 blue, B3 green, B4 red, B5 NIR, B6 SWIR1, B7 SWIR2. Landsat 4, 5, 7: B1 blue, B2 green, B3 red, B4 NIR, B5 SWIR1, B7 SWIR2.
- Landsat 7 after 31 May 2003 has scan-line gaps (SLC-off): stripes of NoData, not a sensor glitch to fill silently.

`QA_PIXEL` bits (1 means the condition is set): 0 fill, 1 dilated cloud, 2 cirrus (Landsat 8 and 9), 3 cloud, 4 cloud shadow, 5 snow, 6 clear, 7 water.

```python
import numpy as np
qa = qa_pixel.astype(np.uint16)
bad = (qa & 0b11111) != 0          # fill, dilated cloud, cirrus, cloud, shadow
refl = sr.astype("float32") * 0.0000275 - 0.2
refl[bad | (sr == 0)] = np.nan
```

## Sentinel-2 in Earth Engine: Cloud Score+

`GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`, bands `cs` and `cs_cdf` (0 not clear to 1 clear), linked to Sentinel-2 by `system:index`. Mask with `cs_cdf >= 0.6`; the catalog says thresholds between 0.50 and 0.65 generally work, higher removes more haze and thin cloud. Example in [earth-engine.md](earth-engine.md).
