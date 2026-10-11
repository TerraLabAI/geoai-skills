# QGIS troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NameError: name 'iface' is not defined` | Code runs in a standalone script, Processing script or `qgis_process` | Use `QgsProject.instance()` (or `context.project()` in Processing); no GUI calls there |
| `layer.isValid()` is False | Wrong path, wrong layer name in `path.gpkg\|layername=x`, wrong provider (`ogr` for vector files, `gdal` for rasters) | Check the path exists; list layers with `ogrinfo path.gpkg` |
| `Couldn't load PyQGIS` with a numpy or other import error | A package from the user site (`~/.local/lib/python3.x/site-packages`) shadows the one bundled with QGIS | Run with `PYTHONNOUSERSITE=1`, or remove the conflicting user package |
| `qgis_process` loads the user's plugins or settings | It uses the default profile | Set `QGIS_CUSTOM_CONFIG_PATH` to an empty folder |
| `qgis_process` crashes with no display | No GUI platform on a server | `QT_QPA_PLATFORM=offscreen` |
| `Cannot find proj.db` in a standalone script | PROJ data path not set outside the QGIS launcher | Set `PROJ_DATA` (older PROJ: `PROJ_LIB`) to the QGIS `proj` folder |
| `type object 'Qt' has no attribute 'UserRole'`, `no attribute exec_` | Qt6 (QGIS 4) dropped unscoped enums and `exec_` | Scoped enums and `exec()`: [pyqgis.md](pyqgis.md) |
| Unknown parameter or wrong result from `processing.run` | Guessed parameter name or enum index | `processing.algorithmHelp("id")` or `qgis_process help id` |
| Buffer is huge or tiny, area in the billions | Layer is in EPSG:4326 (degrees) or EPSG:3857 | Reproject to a projected CRS in meters first |
| Layers do not overlap on the map | CRS assigned instead of reprojected, or wrong CRS declared | Check the real source CRS; reproject with `native:reprojectlayer`; use `native:assignprojection` only to fix a wrong label |
| Overlay or dissolve fails or drops features | Invalid geometries | `native:checkvalidity`, then `native:fixgeometries` |
| Join leaves many NULL attributes | Layers in different CRS, or predicate too strict | Same CRS; try `intersects` before `within` |
| Added features not visible, zoom goes to the wrong place | Not committed or extent not updated | `with edit(layer):`, then `layer.updateExtents()` and `layer.triggerRepaint()` |
| Results gone after reopening the project | Outputs were memory layers | Save with `native:savefeatures` before closing |
| Field names cut to 10 characters | Saved to Shapefile | Save to GeoPackage |
| QGIS freezes during a long loop | Work on the main thread | Use a Processing algorithm or `QgsTask` |

Environment variables verified by running `qgis_process` and QGIS Python 3.44 headless on macOS on 2026-10-11.
