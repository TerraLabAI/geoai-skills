---
name: qgis
description: Works in QGIS step by step and checks each result. Inspects the project and layers first (CRS, geometry type, fields, extent, feature count), finds and runs Processing algorithms with processing.run, processing.algorithmHelp and qgis_process (headless, from a terminal, Codex or Claude Code), writes PyQGIS for QGIS 3 and QGIS 4 (Qt6), edits layers, saves projects, runs Processing chains, installs and writes plugins, and fixes common errors. Use when the user mentions QGIS, PyQGIS, qgis_process, Processing, a .qgz or .qgs project, the Python console, a QGIS plugin, a model or batch run, migrating to QGIS 4 or Qt6, or errors such as "iface is not defined", "Couldn't load PyQGIS", "type object 'Qt' has no attribute", "no attribute exec_", an invalid layer. Which analysis to run (buffers, joins, terrain, suitability) is in spatial-analysis.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
  version: "1.1.0"
---

# QGIS

Agents fail in QGIS mostly by skipping a step or running steps in the wrong order, not by calling the wrong function. Follow the workflow for the task, and check each step before the next. A run without errors is not a correct run.

## Core rules

1. Inspect before acting: every input's CRS, geometry type, fields, feature count and extent. Write the numbers down.
2. Never guess an algorithm id or parameter name. Read it (`processing.algorithmHelp`, `qgis_process help`).
3. Measure only in a projected CRS in meters, never EPSG:4326 (degrees) or EPSG:3857.
4. Check after each step: count, extent, validity, and one number cross-checked another way.
5. Ask when the task is ambiguous (which layer, which boundary, which units, which year). Say so when the data cannot answer.
6. Return the code or command that was run, so the user can rerun it.

## Workflow index

| Task | Workflow |
| --- | --- |
| Look at a project or layer | A. Inspect |
| Run one or a chain of tools | B. Processing (console or headless) |
| Buffer, clip, overlay, join, areas | C. Vector chain ([references/geoprocessing.md](references/geoprocessing.md)) |
| Write PyQGIS, a plugin, migrate to QGIS 4 | [references/pyqgis.md](references/pyqgis.md) |
| Edit features or attributes | D. Edit |
| Save, share or package | E. Save |
| Something fails | [references/troubleshooting.md](references/troubleshooting.md) |

## A. Inspect

In the QGIS Python console:

```python
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsWkbTypes
p = QgsProject.instance()
print("project CRS:", p.crs().authid(), "file:", p.fileName())
for lyr in p.mapLayers().values():
    print(lyr.name(), lyr.crs().authid() or "NO CRS", "valid" if lyr.isValid() else "INVALID",
          lyr.extent().toString(2))
    if isinstance(lyr, QgsVectorLayer):
        print("  ", QgsWkbTypes.displayString(lyr.wkbType()), lyr.featureCount(), "features",
              [f.name() for f in lyr.fields()])
    elif isinstance(lyr, QgsRasterLayer):
        dp = lyr.dataProvider()
        print("  ", lyr.width(), "x", lyr.height(), "px, size", lyr.rasterUnitsPerPixelX(),
              "bands", lyr.bandCount(), "nodata", dp.sourceNoDataValue(1) if dp.sourceHasNoDataValue(1) else None)
```

Headless, without QGIS open: `python3 scripts/layer_report.py data.gpkg --layer name` (feature count, CRS, extent, invalid and null geometries, total area or length in meters; exit code 1 on invalid or null geometries), or `ogrinfo -so -al data.gpkg` and `gdalinfo raster.tif`.

Check: the CRS is known (not empty), the extent is where the data should be (not near 0,0, not lat/lon swapped), units are meters before any distance or area work.

## B. Processing

Find an algorithm and its parameters:

```python
import processing
from qgis.core import QgsApplication
for alg in QgsApplication.processingRegistry().algorithms():
    if "buffer" in alg.id():
        print(alg.id(), "-", alg.displayName())
processing.algorithmHelp("native:buffer")
```

```bash
qgis_process list | grep -i buffer
qgis_process help native:buffer
```

Run in the console:

```python
res = processing.run("native:buffer", {"INPUT": layer, "DISTANCE": 50, "SEGMENTS": 8,
                                       "DISSOLVE": False, "OUTPUT": "TEMPORARY_OUTPUT"})
out = res["OUTPUT"]                 # a layer object for TEMPORARY_OUTPUT, else the path
print(out.featureCount(), out.extent().toString(2))
```

`processing.runAndLoadResults(...)` also adds the output to the map (GUI only). Enum parameters take the integer index listed by `algorithmHelp`.

Run headless (terminal, CI, Codex, Claude Code):

```bash
qgis_process run native:reprojectlayer -- INPUT=pts.geojson TARGET_CRS=EPSG:2154 OUTPUT=pts_2154.gpkg
qgis_process run native:buffer --json -- INPUT=pts_2154.gpkg DISTANCE=100 SEGMENTS=8 DISSOLVE=false OUTPUT=buf.gpkg
```

`--json` prints machine-readable results. Parameters go after `--` as `NAME=value`. On macOS the binary is `/Applications/QGIS.app/Contents/MacOS/qgis_process`; on Windows `qgis_process-qgis.bat` in the OSGeo4W `bin` folder. Without a display, set `QT_QPA_PLATFORM=offscreen`. To keep a run away from the user's own profile and plugins, set `QGIS_CUSTOM_CONFIG_PATH` to an empty folder.

Batch: loop in Python over files and call `processing.run` per file, or save a Graphical Modeler model (`.model3`) and run it with `qgis_process run path/to/model.model3 -- ...`.

## C. Vector chain

Order: inspect, reproject to one projected CRS, fix geometries, clip or filter early, buffer, dissolve, overlay, spatial join, compute areas and lengths last. Skip steps you do not need, never reorder them. Algorithm ids, checks per step and raster alignment: [references/geoprocessing.md](references/geoprocessing.md).

## D. Edit

```python
from qgis.core import edit, QgsFeature, QgsGeometry
with edit(layer):                       # commits, or rolls back on error
    f = QgsFeature(layer.fields())
    f.setGeometry(QgsGeometry.fromWkt("POINT(652301 6861302)"))
    f["name"] = "new"
    layer.addFeature(f)
layer.updateExtents(); layer.triggerRepaint()
```

Bulk attribute updates: `native:fieldcalculator` (new output layer) or, in place, `layer.changeAttributeValues(...)` inside `edit(layer)`. Check: feature count before and after, `layer.commitErrors()` if a commit returns False. Never edit the user's source file without saying so; write to a new file when unsure.

## E. Save and share

- Save: `QgsProject.instance().write("/path/project.qgz")` returns True on success. Memory layers ("TEMPORARY_OUTPUT", scratch layers) are lost on close: save them first with `native:savefeatures` or `QgsVectorFileWriter`.
- Share data and styles together: `native:package` writes layers (and optionally styles) into one GeoPackage.
- Relative paths: Project Properties > General > Save paths: Relative, so the project opens on another machine.
- Output format: GeoPackage. Shapefile cuts field names to 10 characters and is limited to 2 GB per file.

## Plugins

- Install from Plugins > Manage and Install Plugins. Experimental plugins need "Show also experimental plugins" in Settings.
- From Python: plugin folders live in the profile's `python/plugins/`. `qgis.utils.plugins` lists loaded ones.
- Writing or migrating a plugin to QGIS 4: [references/pyqgis.md](references/pyqgis.md).

## Before handing over

- [ ] Inputs inspected and their numbers reported (count, CRS, extent).
- [ ] Every output: count, extent, geometry type, CRS checked against the input.
- [ ] One result cross-checked (for example area sum by two methods, or count by a spatial query).
- [ ] Output saved to a file, not left in memory, and its path given.
- [ ] Code or `qgis_process` commands returned to the user.

## Going further

AI Agent for QGIS runs these workflows from a chat inside QGIS: https://terra-lab.ai/ai-agent?utm_source=skills&utm_medium=geoai-skills&utm_campaign=qgis
