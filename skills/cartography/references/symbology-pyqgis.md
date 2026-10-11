# Symbology with PyQGIS

Tested with QGIS 3.44 (Verified on 2026-10-11). In the QGIS Python console `layer = iface.activeLayer()`; headless, load it with `QgsVectorLayer(path, name, "ogr")`. Call `layer.triggerRepaint()` after a change in the GUI.

## Graduated (choropleth)

```python
from qgis.core import QgsGraduatedSymbolRenderer, QgsClassificationQuantile, QgsStyle

r = QgsGraduatedSymbolRenderer("density")
r.setClassificationMethod(QgsClassificationQuantile())  # or QgsClassificationJenks(), QgsClassificationEqualInterval()
r.updateClasses(layer, 5)
r.updateColorRamp(QgsStyle.defaultStyle().colorRamp("Viridis"))
layer.setRenderer(r)
for c in r.ranges():
    print(c.lowerValue(), c.upperValue(), c.label())  # check the breaks
```

Manual breaks: build `QgsRendererRange(lower, upper, symbol, label)` objects and pass the list to `QgsGraduatedSymbolRenderer("field", ranges)`.

Ramps saved in the user style: `QgsStyle.defaultStyle().colorRampNames()` (a headless run may list only a couple, such as `Blues` and `Viridis`). ColorBrewer schemes are always available by name: `QgsColorBrewerColorRamp("YlOrRd", 5)`, list them with `QgsColorBrewerColorRamp.listSchemeNames()`. Invert with `ramp.invert()` before `updateColorRamp`.

## Categorized

```python
from qgis.core import (QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol,
                       QgsColorBrewerColorRamp)

idx = layer.fields().indexOf("landuse")
values = sorted(layer.uniqueValues(idx), key=str)
ramp = QgsColorBrewerColorRamp("Set2", 8)  # qualitative, 8 colors
cats = []
for i, v in enumerate(values):
    sym = QgsSymbol.defaultSymbol(layer.geometryType())
    sym.setColor(ramp.color(i / max(len(values) - 1, 1)))
    cats.append(QgsRendererCategory(v, sym, str(v)))
layer.setRenderer(QgsCategorizedSymbolRenderer("landuse", cats))
```

More than about 10 categories: group them first (field calculator `CASE WHEN ... END`), or the legend becomes unreadable.

## Rule-based

```python
from qgis.core import QgsRuleBasedRenderer, QgsSymbol

root = QgsRuleBasedRenderer.Rule(None)
for label, expr, color in [
    ("Closed after 2020", "\"status\" = 'closed' AND \"year\" > 2020", "#d7301f"),
    ("Other", "ELSE", "#bdbdbd"),
]:
    sym = QgsSymbol.defaultSymbol(layer.geometryType())
    sym.setColor(QColor(color))
    rule = QgsRuleBasedRenderer.Rule(sym, 0, 0, expr if expr != "ELSE" else "", label)
    if expr == "ELSE":
        rule.setIsElse(True)
    root.appendChild(rule)
layer.setRenderer(QgsRuleBasedRenderer(root))
```

(`from qgis.PyQt.QtGui import QColor`.)

## Opacity, blending, layer order

```python
from qgis.PyQt.QtGui import QPainter

layer.setOpacity(0.6)                                          # whole layer
layer.setBlendMode(QPainter.CompositionMode.CompositionMode_Multiply)         # e.g. hillshade over a colored DEM

root = QgsProject.instance().layerTreeRoot()
node = root.findLayer(layer.id())
root.insertChildNode(0, node.clone())                          # 0 = top of the list = drawn last
root.removeChildNode(node)
```

Draw order from top: labels, points, lines, polygons, rasters, basemap.

## Raster: colored DEM with hillshade

```python
from qgis.core import (QgsRasterLayer, QgsHillshadeRenderer, QgsSingleBandPseudoColorRenderer,
                       QgsRasterShader, QgsColorRampShader, QgsRasterBandStats,
                       QgsColorBrewerColorRamp)

dem = QgsRasterLayer("dem.tif", "Elevation")
st = dem.dataProvider().bandStatistics(1, Qgis.RasterBandStatistic.Min | Qgis.RasterBandStatistic.Max)
crs = QgsColorRampShader(st.minimumValue, st.maximumValue)
ramp = QgsColorBrewerColorRamp("Spectral", 7); ramp.invert()  # low = blue, high = red
crs.setSourceColorRamp(ramp)
crs.classifyColorRamp(7)
shader = QgsRasterShader(); shader.setRasterShaderFunction(crs)
dem.setRenderer(QgsSingleBandPseudoColorRenderer(dem.dataProvider(), 1, shader))

hs = QgsRasterLayer("dem.tif", "Hillshade")
hs.setRenderer(QgsHillshadeRenderer(hs.dataProvider(), 1, 315, 45))  # band, azimuth, altitude
hs.setOpacity(0.5)
QgsProject.instance().addMapLayers([dem, hs])  # hs added last, so it sits on top
```

Set min and max from statistics or from known thresholds; the default cumulative cut hides the extremes. For a DEM in a geographic CRS, reproject first or the hillshade is distorted (degrees versus meters).

## Labels

```python
from qgis.core import (QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat,
                       QgsTextBufferSettings)
from qgis.PyQt.QtGui import QColor

s = QgsPalLayerSettings()
s.fieldName = "name"                  # or an expression: s.isExpression = True
fmt = QgsTextFormat(); fmt.setSize(8)
buf = QgsTextBufferSettings(); buf.setEnabled(True); buf.setSize(0.8); buf.setColor(QColor("white"))
fmt.setBuffer(buf)
s.setFormat(fmt)
layer.setLabeling(QgsVectorLayerSimpleLabeling(s))
layer.setLabelsEnabled(True)
```

Show labels only where they fit: scale-based visibility (`s.scaleVisibility = True`, `s.minimumScale`, `s.maximumScale`) or a rule-based labeling (`QgsRuleBasedLabeling`) for main features only.

## Save and reuse a style

```python
layer.saveNamedStyle("style.qml")   # QGIS style file
layer.loadNamedStyle("style.qml"); layer.triggerRepaint()
```

`layer.saveSldStyle("style.sld")` writes SLD for GeoServer, with fewer features than QML.
