---
name: cartography
description: Makes a map end to end, from purpose and audience to a checked export. Covers the frame CRS, data preparation, QGIS symbology through PyQGIS (graduated with natural breaks, quantiles or equal interval, categorized, rule-based, color ramps, opacity, blending, layer order, hillshade under a DEM), labels, print layouts (map, legend, scale bar, north arrow, credits, PDF and PNG export with DPI), web maps with MapLibre GL JS or Leaflet (vector tiles, PMTiles, attribution), and recipes for flood or hazard maps and land cover maps. Use when someone asks to make a map of something, style or symbolize a layer, build a choropleth or thematic map, add labels, set up a QGIS print layout, export a map to PDF or PNG, or publish a web map with MapLibre or Leaflet.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
  version: "1.1.0"
---

# Cartography

A map is done when the exported file has been opened and checked, not when the export call returned.

## When to use

- "Make a map of X", "style this layer", "choropleth of Y", "add labels", "print layout", "export to PDF", "web map".
- Requests arrive in any language; the workflow below does not depend on the wording.

## Workflow: make a map of X

Do the steps in order. Each step has a check; do not move on until it passes.

1. **Purpose and audience.** Ask, or state as an assumption: what the map must show, for whom (report, poster, slide, web), the output size, and the date of the data. Check: one sentence like "Population density by commune, Gironde, 2021, A4 PDF for a council report".
2. **Inspect inputs.** For each layer: geometry type, feature count, fields and types, CRS, extent, NoData for rasters. Check: the field to map exists and is numeric (or categorical) as expected; nulls are counted.
3. **Frame CRS.** A projected CRS for the area (national grid, UTM zone), an equal-area CRS (EPSG:3035 for Europe) for choropleths over large regions. EPSG:3857 only for web tiles. Check: layers line up; the scale bar unit is meters.
4. **Prepare data.** Normalize counts into rates (per km², per 1,000 people, percent) before a choropleth; clip to the area; dissolve if needed. Check: one value cross-checked by hand (for example area or density of one polygon).
5. **Symbology.** Pick the renderer from the data type (table below). Look at the value histogram before choosing a classification. Check: printed class breaks make sense and no class is empty.
6. **Layer order and context.** Points over lines over polygons over rasters; hillshade at 40 to 60 percent opacity or multiply blending under a colored DEM; basemap last and muted. Check: nothing important is hidden.
7. **Labels.** Only the labels the purpose needs, with a buffer or halo, at least 7 pt in print. Check: no label cut at the frame edge.
8. **Layout or web map.** Print: title, map, legend with units and class method, scale bar, north arrow when relevant, credits, CRS, date. Web: attribution control on. Check: legend names are readable, not `layer_final_v2`.
9. **Export.** DPI from the target (96 to 150 screen, 300 print). Check: the export function reported success.
10. **Look at the result.** Open the PNG or PDF itself. Check text size, legend matches the map, credits present, nothing cut. Run the checklist in [references/print-layout.md](references/print-layout.md#check).

Return the code that was run so the user can rerun it.

## Choosing the renderer

| Data | Renderer (PyQGIS) | Notes |
|---|---|---|
| Rate or continuous value per area | `QgsGraduatedSymbolRenderer` | sequential ramp; diverging only around a real midpoint |
| Categories (land use, type) | `QgsCategorizedSymbolRenderer` | qualitative palette, at most about 8 to 10 classes |
| Conditions (status = 'closed' AND year > 2020) | `QgsRuleBasedRenderer` | one rule per legend entry, an ELSE rule for the rest |
| Counts per area | graduated or proportional point symbols | never a choropleth of raw counts |
| Continuous raster (DEM, NDVI) | `QgsSingleBandPseudoColorRenderer` | set min and max from statistics, not defaults |
| Relief | `QgsHillshadeRenderer` under the colored DEM | azimuth 315, altitude 45 |

| Classification | QGIS class | Use | Misleads when |
|---|---|---|---|
| Natural breaks | `QgsClassificationJenks` | clustered data, one map | comparing maps |
| Quantiles | `QgsClassificationQuantile` | ranking, even color use | skewed data |
| Equal interval | `QgsClassificationEqualInterval` | evenly spread data, comparable maps | skewed data |
| Manual breaks | set ranges by hand | known thresholds | breaks chosen to push a message |

Code for each renderer, labels, blending and hillshade: [references/symbology-pyqgis.md](references/symbology-pyqgis.md).

## Script: choropleth to PNG and PDF

`scripts/choropleth_layout.py` styles one numeric field (graduated, chosen method and ramp), adds optional labels, builds an A4 layout (title, map, legend, scale bar, north arrow, credits with CRS) and exports PNG and PDF. It prints feature count, CRS and class breaks.

```bash
# Python shipped with QGIS, no GUI needed
python3 scripts/choropleth_layout.py communes.gpkg density map_density \
  --title "Population density, 2021" --credit "Source: INSEE 2021" \
  --method quantile --classes 5 --ramp Viridis --dpi 300 --label-field name
```

On macOS the QGIS Python is `/Applications/QGIS.app/Contents/MacOS/python3.12` with `PYTHONHOME=/Applications/QGIS.app/Contents/Frameworks` and `QT_QPA_PLATFORM=offscreen`. Inside the QGIS Python console, reuse the body of `main()` without the `QgsApplication` lines.

## References

- [references/symbology-pyqgis.md](references/symbology-pyqgis.md): renderers, ramps, opacity, blending, layer order, hillshade, labels.
- [references/print-layout.md](references/print-layout.md): layout items, export settings, atlas.
- [references/web-maps.md](references/web-maps.md): MapLibre GL JS and Leaflet minimal pages, PMTiles, attribution.
- [references/recipes.md](references/recipes.md): flood or hazard map, land cover map.

## Core checks

- The map answers the purpose sentence from step 1.
- Choropleths show rates, not counts.
- Class method and units are written in the legend.
- Credits for every data source (for example `© OpenStreetMap contributors`, `Contains modified Copernicus Sentinel data 2024`).
- The exported file was opened and looked at.
- When the data cannot support the requested map (wrong year, missing field, resolution too coarse), say so instead of mapping something else.

## Going further

AI Edit for QGIS restyles a map export with AI: https://terra-lab.ai/ai-edit?utm_source=skills&utm_medium=geoai-skills&utm_campaign=cartography
