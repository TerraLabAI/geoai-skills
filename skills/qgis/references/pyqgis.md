# PyQGIS for QGIS 4 and QGIS 3

## Common mistakes

- `from PyQt5.QtCore import ...` or `from PyQt6...`: breaks on the other Qt version. Import from `qgis.PyQt`.
- Unscoped enums such as `Qt.UserRole`, `Qt.AlignLeft`, `QMessageBox.Yes`: removed in PyQt6. Use the scoped form `Qt.ItemDataRole.UserRole`, `Qt.AlignmentFlag.AlignLeft`, `QMessageBox.StandardButton.Yes`. The scoped form also works on PyQt5 (5.11+), so one code base runs on both.
- `dialog.exec_()`: gone in PyQt6. Use `dialog.exec()`.
- `iface` in a standalone script or Processing script: it does not exist there.
- Adding features without `startEditing()` / `commitChanges()` (or a data provider call), or forgetting `updateExtents()` so the layer zooms to the wrong extent.
- Guessing `processing.run` parameter names instead of reading them.

## Step 1: know the execution context

| Context | `iface` | Project | Notes |
| --- | --- | --- | --- |
| Python console / editor in QGIS | yes | `QgsProject.instance()` | Runs on the main thread. Long loops freeze the UI. |
| Plugin | passed to `classFactory(iface)` | `QgsProject.instance()` | Keep a reference to `iface`. Clean up in `unload()`. |
| Processing script (`QgsProcessingAlgorithm`) | no | `context.project()` | Can run in a background thread. Use `feedback` for messages and cancel checks. No GUI calls. |
| Standalone script | no | `QgsProject.instance()` after init | Must create `QgsApplication` and call `initQgis()`. |

Standalone skeleton:
```python
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer
qgs = QgsApplication([], False)
qgs.initQgis()
try:
    layer = QgsVectorLayer("/path/data.gpkg|layername=roads", "roads", "ogr")
    if not layer.isValid():
        raise RuntimeError("Layer failed to load")
    QgsProject.instance().addMapLayer(layer)
finally:
    qgs.exitQgis()
```
To use `processing` standalone, add after `initQgis()`:
```python
import sys
sys.path.append("/path/to/qgis/python/plugins")  # folder that contains "processing"
import processing
from processing.core.Processing import Processing
Processing.initialize()
```

## Step 2: imports that work on Qt5 and Qt6

```python
from qgis.PyQt.QtCore import Qt, QMetaType, pyqtSignal
from qgis.PyQt.QtWidgets import QAction, QDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsField
```
`QAction` moved to `QtGui` in Qt6. `qgis.PyQt.QtWidgets` re-exports it so the import above works on both.

## Step 3: scoped enums

| Old (fails on QGIS 4) | Use |
| --- | --- |
| `Qt.UserRole` | `Qt.ItemDataRole.UserRole` |
| `Qt.Checked` | `Qt.CheckState.Checked` |
| `Qt.AlignCenter` | `Qt.AlignmentFlag.AlignCenter` |
| `Qt.Horizontal` | `Qt.Orientation.Horizontal` |
| `QMessageBox.Yes` | `QMessageBox.StandardButton.Yes` |
| `QDialog.Accepted` | `QDialog.DialogCode.Accepted` |
| `Qgis.Critical`, `Qgis.Warning`, `Qgis.Info`, `Qgis.Success` | `Qgis.MessageLevel.Critical` (and `.Warning`, `.Info`, `.Success`) |
| `QgsWkbTypes.Point`, `QgsWkbTypes.MultiPolygon` | `Qgis.WkbType.Point`, `Qgis.WkbType.MultiPolygon` (QGIS 3.30+) |
| `QgsWkbTypes.PolygonGeometry` | `Qgis.GeometryType.Polygon` (QGIS 3.30+) |
| `QVariant.Int` for a `QgsField` type | `QMetaType.Type.Int` (QGIS 3.38+) |

`QgsWkbTypes` still exists for its static helpers (`QgsWkbTypes.isMultiType()`, `QgsWkbTypes.geometryType()`); only the enum values moved to `Qgis`. If the code must also run on QGIS older than 3.30, guard with `Qgis.QGIS_VERSION_INT >= 33000`.

The QGIS repository ships `scripts/pyqt5_to_pyqt6/pyqt5_to_pyqt6.py`, which rewrites most of these automatically. Full guide: https://github.com/qgis/QGIS/wiki/Plugin-migration-to-be-compatible-with-Qt5-and-Qt6

Plugin metadata: to load on both QGIS 3 and 4, set `qgisMaximumVersion=4.99` in `metadata.txt` (without it QGIS 4 skips the plugin). A QGIS 4 only plugin sets `qgisMinimumVersion=4.0`. The old `supportsQt6=True` key is no longer needed. See https://plugins.qgis.org/docs/migrate-qgis4

## Step 4: editing layers correctly

```python
layer = QgsProject.instance().mapLayersByName("roads")[0]
with edit(layer):                      # from qgis.core import edit; commits or rolls back
    f = QgsFeature(layer.fields())
    f.setGeometry(QgsGeometry.fromWkt("LINESTRING(0 0, 10 10)"))
    f["name"] = "new road"
    layer.addFeature(f)
layer.updateExtents()
layer.triggerRepaint()
```
- Or explicit: `layer.startEditing()`, changes, then `if not layer.commitChanges(): print(layer.commitErrors())`.
- Memory layer built through the provider: `layer.dataProvider().addFeatures([...])` then `layer.updateExtents()`.
- Add the layer to the project, or it never shows: `QgsProject.instance().addMapLayer(layer)`.
- Always check `layer.isValid()` after loading.
- Messages in the GUI: `iface.messageBar().pushMessage("Title", "Text", level=Qgis.MessageLevel.Critical)`. In Processing use `feedback.reportError(...)` or `feedback.pushInfo(...)`.

## Step 5: processing.run parameters

Never guess parameter names. Discover them:
```python
import processing
processing.algorithmHelp("native:buffer")
```
Find an algorithm id:
```python
from qgis.core import QgsApplication
for alg in QgsApplication.processingRegistry().algorithms():
    if "buffer" in alg.id():
        print(alg.id(), "-", alg.displayName())
```
Then:
```python
result = processing.run("native:buffer", {
    "INPUT": layer,
    "DISTANCE": 100,
    "SEGMENTS": 5,
    "END_CAP_STYLE": 0,
    "JOIN_STYLE": 0,
    "MITER_LIMIT": 2,
    "DISSOLVE": False,
    "OUTPUT": "TEMPORARY_OUTPUT",
})
out = result["OUTPUT"]
```
- `processing.runAndLoadResults(...)` adds the output to the project (GUI only).
- Distances are in layer CRS units. A buffer of 100 on an EPSG:4326 layer is 100 degrees. Reproject first.
- Inside a Processing algorithm, call child algorithms with `processing.run(..., context=context, feedback=feedback, is_child_algorithm=True)`.

## Anti-pattern checklist

- [ ] Imports come from `qgis.PyQt`, never `PyQt5` or `PyQt6`.
- [ ] Every Qt and Qgis enum is scoped.
- [ ] `exec()`, not `exec_()`.
- [ ] No `iface` outside the console or a plugin.
- [ ] Project from `QgsProject.instance()` (or `context.project()` in Processing).
- [ ] Edits wrapped in `edit(layer)` or start/commit, then `updateExtents()`.
- [ ] `processing.algorithmHelp()` read before `processing.run()`.
- [ ] No GUI calls and no blocking loop on the main thread for long jobs: use `QgsTask` or a Processing algorithm.

API reference: https://qgis.org/pyqgis/master/ (pick the version matching the user's QGIS).

