# Change detection and Sentinel-1 SAR

## Rules for any before and after comparison

1. **Same season** (anniversary dates) for vegetation, or phenology looks like change. For a sudden event (fire, flood), take the last clear image before and the first clear image after, as close in time as possible.
2. **Same sensor and same processing**: both harmonized or both offset-corrected; do not compare Landsat 7 with Sentinel-2 values directly.
3. **Same grid**: align both dates to one CRS, pixel size and origin (`native:alignsingleraster` or `gdalwarp -tap`).
4. **Same mask**: apply the union of both cloud masks to both dates.
5. **Threshold with a reason**: published classes (dNBR below) or a threshold chosen from the histogram of a known no-change area (mean plus or minus 2 standard deviations of the difference). State it.
6. **Check**: look at three changed spots on the before and after true color images; report changed area in hectares.

## Burn severity: dNBR

NBR = (NIR - SWIR2) / (NIR + SWIR2): Sentinel-2 (B8A - B12) / (B8A + B12), Landsat 8/9 (B5 - B7) / (B5 + B7).
dNBR = NBR_pre - NBR_post (positive means burned). Some products scale it by 1000.

USGS FIREMON severity classes (Key and Benson), for dNBR not scaled:

| dNBR | Class |
| --- | --- |
| below -0.25 | high enhanced regrowth |
| -0.25 to -0.1 | low enhanced regrowth |
| -0.1 to 0.1 | unburned |
| 0.1 to 0.27 | low severity |
| 0.27 to 0.44 | moderate-low severity |
| 0.44 to 0.66 | moderate-high severity |
| above 0.66 | high severity |

These thresholds were calibrated on North American forests; say so, and field-check or adapt elsewhere. RdNBR or RBR normalize for low pre-fire vegetation.

```
QGIS native:rastercalc expression (NBR rasters already computed):
"nbr_pre@1" - "nbr_post@1"
```

Burned area: threshold dNBR (for example above 0.1), sieve small patches (`gdal:sieve`), polygonize, report area. Compare with an official perimeter (EFFIS in Europe, national services) when one exists.

## NDVI difference

dNDVI = NDVI_after - NDVI_before on same-season, cloud-masked, aligned images. Loss is negative. Use it for clearing, crop failure, construction. Do not compare a June image with a September one. For long series, prefer a trend over yearly composites to a two-date difference.

## Sentinel-1 SAR basics

- C-band radar, sees through cloud, day and night. IW mode, dual polarization VV and VH over most land.
- Values are backscatter: linear power (sigma0 or gamma0) or decibels (10 log10). Average, filter and resample in **linear** units, then convert to dB for display and thresholds.
- Products: GRD (detected, needs calibration and terrain correction; Earth Engine `COPERNICUS/S1_GRD` is already calibrated, terrain corrected and in dB), RTC (radiometrically terrain corrected gamma0, Planetary Computer `sentinel-1-rtc`).
- Speckle: apply a filter (Lee, Refined Lee, or a temporal mean of several dates) before thresholding single pixels.
- Geometry: compare only images from the same relative orbit and pass direction (ascending or descending), or the viewing angle changes the values. Steep terrain has layover and shadow; mask it with the DEM.

Flood mapping with SAR:
1. Pick a post-event image and a reference image from the same orbit and season (dry conditions).
2. Calibrate, terrain correct, speckle filter; work in VV.
3. Open water is dark: VV roughly below -15 to -18 dB, but derive the threshold from the histogram (Otsu) of the scene and state it.
4. Flood = water after and not water before (removes permanent water). Mask slopes above about 5 degrees and HAND above about 15 to 20 m to remove radar shadows.
5. Known misses: flooded vegetation and flooded towns can be bright, not dark. Say so.
6. Check against optical imagery of the same days if any is clear, or the Copernicus Emergency Management Service rapid mapping product for the event when one exists.

Sentinel-1B stopped working in December 2021, so from 2022 the revisit was 12 days until Sentinel-1C (launched December 2024) joined Sentinel-1A.
