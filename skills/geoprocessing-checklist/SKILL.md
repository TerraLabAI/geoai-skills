---
name: geoprocessing-checklist
description: Legacy entry point kept so existing links keep working. Its content now lives in the broader `spatial-analysis` and `qgis` skills, which cover ordering and checking geoprocessing steps (reproject, fix geometries, clip, buffer, dissolve, overlay). Use when a request names this skill directly.
license: MIT
metadata:
  author: TerraLab
  homepage: https://terra-lab.ai
  version: "1.1.0"
---

# geoprocessing-checklist (moved)

This skill was merged into a broader skill in version 1.1.0. Load and follow [spatial-analysis](../spatial-analysis/SKILL.md) and [qgis](../qgis/SKILL.md) instead.

If `spatial-analysis` and `qgis` are not installed, install the full set:

```bash
npx skills add TerraLabAI/geoai-skills
```

The scripts in `scripts/` still work and are also shipped in the new skills.
