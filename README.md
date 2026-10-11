# GeoAI Skills

Agent Skills for geospatial work, by [TerraLab](https://terra-lab.ai). They teach coding agents
(Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot and others) the GIS steps they most often
get wrong: wrong coordinate systems, measurements in degrees, QGIS 3 code that breaks in QGIS 4,
Sentinel-2 values off by an offset, processing steps skipped or run in the wrong order.

Each skill works on its own. No account, server or plugin is needed.

## Install

```bash
npx skills add TerraLabAI/geoai-skills
```

One skill only:

```bash
npx skills add TerraLabAI/geoai-skills --skill sentinel2-indices
```

Claude Code plugin:

```text
/plugin marketplace add TerraLabAI/geoai-skills
/plugin install geoai-skills@terralab-geoai
```

## Skills

| Skill | Use it when |
| --- | --- |
| [crs-and-measurements](skills/crs-and-measurements/SKILL.md) | Choosing a coordinate system, reprojecting, measuring distances or areas |
| [pyqgis-qgis4](skills/pyqgis-qgis4/SKILL.md) | Writing PyQGIS scripts or plugins that run on QGIS 4 and QGIS 3 |
| [sentinel2-indices](skills/sentinel2-indices/SKILL.md) | Computing NDVI, NDWI, NBR and other indices from Sentinel-2 |
| [open-imagery-finder](skills/open-imagery-finder/SKILL.md) | Finding open satellite imagery or elevation data for an area |
| [open-map-data](skills/open-map-data/SKILL.md) | Getting buildings, roads, places or boundaries from OpenStreetMap, Overture or national sources |
| [geoprocessing-checklist](skills/geoprocessing-checklist/SKILL.md) | Running clip, buffer, dissolve, overlay or raster calculations |
| [imagery-for-object-detection](skills/imagery-for-object-detection/SKILL.md) | Preparing imagery for detection or segmentation, and checking the results |
| [map-export-qa](skills/map-export-qa/SKILL.md) | Checking a map before export, print or publication |

## Scripts

Some skills ship small Python 3.9+ scripts in `skills/<name>/scripts/` for steps that are easy to get wrong: UTM EPSG lookup, measurement CRS check, Sentinel-2 offset check, index formulas, attribution lines and a vector layer report. Each runs with `--help`. They use the standard library; the file readers use GDAL or geopandas when installed.

## Evaluations

Each skill has three test prompts in `skills/<name>/evals/evals.json`. [EVALS.md](EVALS.md) explains how to run them with and without the skill; they are checked before each release.

## Related

- [TerraLab MCP server](https://terra-lab.ai/mcp?utm_source=github&utm_medium=geoai-skills): open map data, coordinates, elevation and GIS files inside AI assistants.
- [AI Agent for QGIS](https://terra-lab.ai/ai-agent?utm_source=github&utm_medium=geoai-skills), [AI Segmentation](https://terra-lab.ai/ai-segmentation?utm_source=github&utm_medium=geoai-skills) and [AI Edit](https://terra-lab.ai/ai-edit?utm_source=github&utm_medium=geoai-skills): TerraLab's QGIS plugins.

Issues and pull requests are welcome. Contact: yvann.barbot@terra-lab.ai.

## License

MIT
