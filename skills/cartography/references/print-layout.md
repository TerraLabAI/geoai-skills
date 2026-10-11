# Print layouts with PyQGIS

Class names checked against QGIS 3.44 (Verified on 2026-10-11). A complete, tested example is `scripts/choropleth_layout.py`.

## Order of work

1. Page size first: `layout.initializeDefaults()` gives one A4 landscape page; for another size, `layout.pageCollection().page(0).setPageSize("A3", QgsLayoutItemPage.Orientation.Landscape)`.
2. Map item, then fix its extent and, for a printed scale, `map_item.setScale(25000)`.
3. Legend, scale bar, north arrow, title, credits, linked to the map item.
4. Export, then open the file.

## Items

| Item | Class | Key calls |
|---|---|---|
| Map | `QgsLayoutItemMap` | `setExtent`, `setScale`, `setCrs`, `setKeepLayerSet(True)` + `setLayers([...])` to freeze layers, `setFrameEnabled(True)` |
| Legend | `QgsLayoutItemLegend` | `setLinkedMap(map)`, `setTitle`, `setAutoUpdateModel(False)` before renaming or removing entries, `setLegendFilterByMapEnabled(True)` to show only what is in the map |
| Scale bar | `QgsLayoutItemScaleBar` | `setStyle("Single Box")`, `setLinkedMap(map)`, `applyDefaultSize()`, `setUnits(...)`, `setNumberOfSegments` |
| North arrow | `QgsLayoutItemPicture` | `setPicturePath(svg)`, `setLinkedMap(map)`, `setNorthMode(QgsLayoutItemPicture.NorthMode.GridNorth)` or `TrueNorth` |
| Text | `QgsLayoutItemLabel` | `setText`, `setTextFormat(QgsTextFormat)`; expressions inside `[% %]`, for example `[% @project_crs %]`, `[% format_date(now(), 'yyyy-MM-dd') %]` |
| Inset map | second `QgsLayoutItemMap` | an overview: `inset.overview().setLinkedMap(main_map)` |

Positions and sizes: `item.attemptMove(QgsLayoutPoint(x, y, Qgis.LayoutUnit.Millimeters))` and `item.attemptResize(QgsLayoutSize(w, h, Qgis.LayoutUnit.Millimeters))`.

North arrow SVGs ship with QGIS under `QgsApplication.svgPaths()`, folder `arrows/` (for example `NorthArrow_02.svg`).

## Export

```python
exp = QgsLayoutExporter(layout)
img = QgsLayoutExporter.ImageExportSettings(); img.dpi = 300
pdf = QgsLayoutExporter.PdfExportSettings(); pdf.dpi = 300
assert exp.exportToImage("map.png", img) == QgsLayoutExporter.ExportResult.Success
assert exp.exportToPdf("map.pdf", pdf) == QgsLayoutExporter.ExportResult.Success
```

- `pdf.rasterizeWholeImage = False` (default) keeps vectors; `pdf.forceVectorOutput = True` if a blend mode makes QGIS rasterize.
- Layouts saved in a project: `QgsProject.instance().layoutManager().addLayout(layout)` after `layout.setName("Main")`.
- From the command line on a saved project: `qgis_process run native:printlayouttopdf --PROJECT_PATH=project.qgz --LAYOUT=Main --DPI=300 --OUTPUT=map.pdf` (check the parameters with `qgis_process help native:printlayouttopdf`).

## Atlas (one page per feature)

```python
atlas = layout.atlas()
atlas.setCoverageLayer(communes); atlas.setPageNameExpression('"name"'); atlas.setEnabled(True)
map_item.setAtlasDriven(True); map_item.setAtlasMargin(0.1)
QgsLayoutExporter.exportToPdf(atlas, "atlas.pdf", QgsLayoutExporter.PdfExportSettings())
```

## Check

Open the export at 100 percent: text at least 7 pt, legend entries match visible classes, scale bar round numbers in m or km, credits present, nothing outside the page. Then run this checklist:

- [ ] Colors: sequential ramp for low to high, diverging only around a meaningful midpoint, qualitative for categories (8 to 10 at most).
- [ ] Color-blind safe palette (ColorBrewer marks them, viridis-type ramps work); no rainbow, no red versus green alone; readable in grayscale if it may be printed in black and white.
- [ ] Author, date and CRS (EPSG code) in small print.
- [ ] Scale bar from a projected frame CRS; on small-scale maps of large areas, drop it or note the latitude where it is valid.
- [ ] Inset or locator map when the area is not obvious.
