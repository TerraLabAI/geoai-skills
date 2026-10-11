# Recipes

## Flood or hazard map

Purpose sentence first: which hazard, which scenario (return period such as 1 in 100 years, or an observed event with its date), which area, for whom. A hazard map without its scenario and source is misleading.

1. **Inputs.** Hazard layer (water depth raster, flood extent polygons, or official hazard zones), a DEM for relief, context (roads, buildings, place names). Check the CRS, NoData value and units of the depth raster (m or cm).
2. **Classes.** Use fixed, meaningful thresholds, not natural breaks, so maps of different scenarios compare. A common depth scale: 0 to 0.5 m, 0.5 to 1 m, 1 to 2 m, over 2 m. Use the official classes when the map reproduces an official product.
3. **Colors.** Sequential blues, light to dark with depth. Hazard levels (low, medium, high): a sequential yellow, orange, red ramp. Set NoData and zero depth transparent.
4. **Context.** Hillshade at about 50 percent opacity under the hazard layer; buildings and roads in muted gray above it; place names on top.
5. **Layout.** Title with hazard, scenario and area; legend with units; source and date of the model or event; a sentence on what the map does not show (for example "Defences assumed intact" when the source says so); scale bar; CRS.
6. **Check.** Compare the flooded area sum with the source's published figure if one exists; spot-check that the water follows the valleys on the hillshade.

PyQGIS: depth classes on a raster.

```python
from qgis.core import Qgis, QgsColorRampShader, QgsRasterRange, QgsRasterShader, QgsSingleBandPseudoColorRenderer
from qgis.PyQt.QtGui import QColor

items = [QgsColorRampShader.ColorRampItem(0.5, QColor("#c6dbef"), "0 to 0.5 m"),
         QgsColorRampShader.ColorRampItem(1.0, QColor("#6baed6"), "0.5 to 1 m"),
         QgsColorRampShader.ColorRampItem(2.0, QColor("#2171b5"), "1 to 2 m"),
         QgsColorRampShader.ColorRampItem(1e9, QColor("#08306b"), "over 2 m")]
fn = QgsColorRampShader(); fn.setColorRampType(Qgis.ShaderInterpolationMethod.Discrete); fn.setColorRampItemList(items)
shader = QgsRasterShader(); shader.setRasterShaderFunction(fn)
r = QgsSingleBandPseudoColorRenderer(depth.dataProvider(), 1, shader)
depth.setRenderer(r)
depth.dataProvider().setUserNoDataValue(1, [QgsRasterRange(0, 0)])  # display only, file untouched
```

With `Discrete`, each item colors values up to and including its value.

## Land cover map

1. **Inputs.** A classified raster (for example ESA WorldCover 10 m, CC BY 4.0) or polygons with a class field. Check the class codes present (`gdalinfo -hist` or unique values) against the product's legend.
2. **Colors.** Use the product's official palette so readers recognize it; otherwise a qualitative palette with water in blue, forest in dark green, built-up in red or gray.
3. **Merge classes** the purpose does not need, and drop classes absent from the area from the legend.
4. **Layout.** Legend with class names (not codes), product name, version and year, resolution, credit line.
5. **Check.** Area per class (raster: count pixels times pixel area in a projected CRS) and a sanity look at a known place (a lake is water, a town is built-up).

ESA WorldCover palette (Product User Manual v2.0, Table 3; Verified on 2026-10-11):

| Code | Class | Color |
|---|---|---|
| 10 | Tree cover | #006400 |
| 20 | Shrubland | #ffbb22 |
| 30 | Grassland | #ffff4c |
| 40 | Cropland | #f096ff |
| 50 | Built-up | #fa0000 |
| 60 | Bare / sparse vegetation | #b4b4b4 |
| 70 | Snow and ice | #f0f0f0 |
| 80 | Permanent water bodies | #0064c8 |
| 90 | Herbaceous wetland | #0096a0 |
| 95 | Mangroves | #00cf75 |
| 100 | Moss and lichen | #fae6a0 |

Credit line: "ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium" (adapt the year to the version used).

PyQGIS: paletted renderer.

```python
from qgis.core import QgsPalettedRasterRenderer
from qgis.PyQt.QtGui import QColor

palette = {10: ("#006400", "Tree cover"), 20: ("#ffbb22", "Shrubland"), 30: ("#ffff4c", "Grassland"),
           40: ("#f096ff", "Cropland"), 50: ("#fa0000", "Built-up"), 60: ("#b4b4b4", "Bare / sparse vegetation"),
           70: ("#f0f0f0", "Snow and ice"), 80: ("#0064c8", "Permanent water bodies"),
           90: ("#0096a0", "Herbaceous wetland"), 95: ("#00cf75", "Mangroves"), 100: ("#fae6a0", "Moss and lichen")}
classes = [QgsPalettedRasterRenderer.Class(v, QColor(c), name) for v, (c, name) in palette.items()]
lc.setRenderer(QgsPalettedRasterRenderer(lc.dataProvider(), 1, classes))
```

Area per class, in a projected CRS: `native:rasterlayeruniquevaluesreport` (Processing) lists pixel count and area per value.
