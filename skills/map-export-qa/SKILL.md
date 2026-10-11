---
name: map-export-qa
description: Checklist to run before exporting, printing or sharing a map. Covers the map frame CRS for the area, classification methods (natural breaks, quantiles, equal interval) and when each misleads, sequential versus diverging colour ramps, colour-blind safe palettes and ColorBrewer, normalising counts by area or population, scale bar correctness (not in Web Mercator at high latitudes), north arrow, legend, source and licence credits, DPI for print and screen, and QGIS print layout tips. Use when someone asks to export, print, publish or review a map, make a choropleth or thematic map, pick colours or classes, add a legend or scale bar, or set up a QGIS print layout.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
---

# Map export QA

## What goes wrong without this skill

- Choropleth of raw counts, so big areas look important.
- Scale bar drawn in Web Mercator (EPSG:3857), wrong away from the equator.
- Rainbow ramp, or red and green as the only contrast.
- Missing data credits (OpenStreetMap and others require them).
- Export at screen DPI, blurry on paper.

## 1. Frame CRS

- Use a projected CRS made for the area: national grid or UTM zone for local maps, an equal-area CRS (for example EPSG:3035 for Europe) for choropleths over large regions.
- EPSG:3857 is fine for web tiles, not for measured maps: scale grows as 1 / cos(latitude), about 1.4x at 45 degrees and 2x at 60 degrees.
- Check that data layers line up after on-the-fly reprojection.

## 2. Normalise first

Map rates, not totals, on a choropleth: per km², per 1,000 people, per household, a percentage. Show raw counts with proportional symbols instead.

## 3. Classification

| Method | Good for | Misleads when |
|---|---|---|
| Natural breaks (Jenks) | clustered data, one map | comparing maps; breaks change with each dataset |
| Quantiles | ranking, even colour use | skewed data: very different values share a class, close values split |
| Equal interval | evenly spread data, comparable maps | skewed data: most features fall in one class |
| Manual or round breaks | known thresholds, readability | chosen to push a message |

Use 4 to 7 classes. State the method in the legend or note. Check the histogram before choosing.

## 4. Colour

- Sequential ramp (light to dark) for low to high values.
- Diverging ramp only around a meaningful midpoint (0, average, target).
- Qualitative palette for categories, at most about 8 to 10.
- Use colour-blind safe palettes: ColorBrewer (colorbrewer2.org) marks them; viridis-type ramps also work. Avoid rainbow and red-versus-green alone.
- Check in grayscale if the map may be printed in black and white.

## 5. Map elements

- [ ] Title that says what, where and when.
- [ ] Legend with units, class method, no layer names like `layer_final_v2`.
- [ ] Scale bar in metres or kilometres, from a projected frame CRS; for small-scale maps of large areas, drop it or note it is valid only at a given latitude.
- [ ] North arrow when north is not up or for print maps; skip on small-scale world maps where north varies.
- [ ] Source and licence credits, for example `© OpenStreetMap contributors`, imagery provider and date.
- [ ] Author, date, CRS (EPSG code) in small text.
- [ ] Inset or locator map if the area is not obvious.

## 6. Resolution and format

| Use | DPI | Format |
|---|---|---|
| Screen, slides, web | 96 to 150 | PNG (or JPEG for imagery) |
| Office print | 300 | PDF |
| Professional print | 300 or more, vector kept | PDF, keep vectors |
| Large poster | 150 to 300 at final size | PDF |

Set the page to the final paper size before placing elements; do not scale an export afterwards.

## 7. QGIS print layout tips

- Project > New Print Layout; set page size first (Layout > Page Properties).
- Item Properties of the map: set a fixed scale and lock layers and styles if the canvas will change.
- Scale bar: link it to the map item; units in km or m; "Fit segment width" for round numbers.
- Legend: untick Auto update, then rename and remove entries; enable "Only show items inside linked map".
- Dynamic text: insert expressions like `[% @project_crs %]` or `[% format_date(now(), 'yyyy-MM-dd') %]`.
- Export: Layout > Export as PDF (vector) or Image with the DPI from the table; tick "Always export as vectors" if a renderer rasterises.
- Atlas for one page per area.

## 8. Final look

Open the exported file itself at 100 % and on paper size: text readable (at least 7 pt in print), no cut labels, legend matches the map, credits present.

## Going further

AI Edit for QGIS restyles a map export with AI: https://terra-lab.ai/ai-edit?utm_source=skills&utm_medium=geoai-skills&utm_campaign=map-export-qa
