# GeoAI Skills

Agent Skills for GIS and geospatial work, by [TerraLab](https://terra-lab.ai). They make coding
agents (Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot and others) work like a careful GIS
analyst: inspect the data first, run the steps in the right order, check every result, and hand
back the code that was run.

Built from the failure modes measured in GIS agent benchmarks (most failures are a skipped or
misordered step, not a bad command), from what GIS users ask AI to do, and tested on QGIS 3.44,
GDAL and DuckDB. Each skill works on its own: no account, server or plugin is needed.

## Install

```bash
npx skills add TerraLabAI/geoai-skills
```

One skill only:

```bash
npx skills add TerraLabAI/geoai-skills --skill qgis
```

Claude Code plugin:

```text
/plugin marketplace add TerraLabAI/geoai-skills
/plugin install geoai-skills@terralab-geoai
```

## Skills

| Skill | Use it when |
| --- | --- |
| [qgis](skills/qgis/SKILL.md) | Working in QGIS: PyQGIS scripts for QGIS 3 and 4, Processing and `qgis_process`, layers, projects, plugins, errors |
| [gis-data](skills/gis-data/SKILL.md) | Finding, downloading, converting and citing data: OpenStreetMap, Overture, national sources, formats, CRS and EPSG |
| [spatial-analysis](skills/spatial-analysis/SKILL.md) | Joins, overlays, buffers, site suitability, terrain and hydrology, zonal statistics, hotspots |
| [remote-sensing](skills/remote-sensing/SKILL.md) | Sentinel-2, Landsat, Sentinel-1, Earth Engine, indices such as NDVI, cloud masks, change detection, land cover |
| [cartography](skills/cartography/SKILL.md) | Making a map: symbology, labels, print layouts, export, web maps with MapLibre or Leaflet |
| [object-detection](skills/object-detection/SKILL.md) | Detecting, segmenting or counting buildings, trees, cars or solar panels in imagery, and checking the results |
| [spatial-sql](skills/spatial-sql/SKILL.md) | PostGIS and DuckDB spatial queries, GeoParquet, indexes and query checks |

The eight focused skills of version 1.0 (`crs-and-measurements`, `pyqgis-qgis4`, `sentinel2-indices`,
`open-imagery-finder`, `open-map-data`, `geoprocessing-checklist`, `imagery-for-object-detection`,
`map-export-qa`) were merged into these. Their folders stay as short pointers so existing links keep
working. See [CHANGELOG.md](CHANGELOG.md).

## Scripts

Skills ship small Python 3.9+ scripts in `skills/<name>/scripts/` for steps that are easy to get
wrong: UTM EPSG lookup, measurement CRS check, layer report, Sentinel-2 offset check, index formulas,
attribution lines, accuracy assessment, choropleth layout, detection cleanup and scoring. Each runs
with `--help`.

## Evaluations

Each skill has 5 test prompts in `skills/<name>/evals/evals.json`. [EVALS.md](EVALS.md) explains how
to run them with and without the skill.

## Related

- [TerraLab MCP server](https://terra-lab.ai/mcp?utm_source=github&utm_medium=geoai-skills): open map data, coordinates, elevation and GIS files inside AI assistants.
- [AI Agent for QGIS](https://terra-lab.ai/ai-agent?utm_source=github&utm_medium=geoai-skills), [AI Segmentation](https://terra-lab.ai/ai-segmentation?utm_source=github&utm_medium=geoai-skills) and [AI Edit](https://terra-lab.ai/ai-edit?utm_source=github&utm_medium=geoai-skills): TerraLab's QGIS plugins.

Issues and pull requests are welcome, see [CONTRIBUTING.md](CONTRIBUTING.md). Contact: yvann.barbot@terra-lab.ai.

## License

MIT
