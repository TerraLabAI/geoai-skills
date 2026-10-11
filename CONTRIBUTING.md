# Contributing: rules for anyone (and any agent) changing this repo

Public repo TerraLabAI/geoai-skills, already submitted to several directories (list below).
Every push to `main` reaches them, so a change here is a release. Done means: the change is on
`main`, the version is raised, CHANGELOG.md has a line, `claude plugin validate --strict .`
passes, and no submitted path broke.

## Where it is listed (2026-10-11)

| Place | How it follows the repo | Tied to |
| --- | --- | --- |
| Claude plugin directory | Tracks `main`; each new commit is scanned again and, if held, reviewed; the last published version stays live meanwhile (claude.com/docs/connectors/building/after-publishing) | `.claude-plugin/plugin.json` |
| Cursor marketplace | Every update is manually reviewed before it is published (cursor.com/docs/plugins) | `.cursor-plugin/plugin.json` |
| cursor.directory | https://cursor.directory/plugins/terralab-geoai-skills | repo |
| MCPMarket | skill `crs-and-measurements` submitted alone | `skills/crs-and-measurements/` |
| MCP.Directory | skill `open-map-data` submitted alone | `skills/open-map-data/` |
| isaaccorley/geospatial-skills | issue #8 | repo URL |
| sshuair/awesome-gis | PR #290 | repo URL |
| skills.sh, Gemini gallery, SkillsMP, claude-plugins.dev | auto-indexed from GitHub | repo, topics, `gemini-extension.json` |

Full listing record: `../terralab-mcp/docs/codex-geoai-skills-wide-listings-2026-10-11.md`.

## Rules

- Never rename or move the repo, the plugin name `geoai-skills`, the marketplace name
  `terralab-geoai`, or any folder under `skills/`. Directories and links point at them.
- Never delete a skill folder. To retire a skill, keep its folder with a short SKILL.md that
  sends the agent to the skill that replaces it, and note it in CHANGELOG.md.
- Raise `version` in `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json` and
  `gemini-extension.json` together on every release (installed copies compare it). Patch for
  fixes, minor for new skills or content, major only if a skill stops working the old way.
- Group changes into one release instead of many small pushes: each push to `main` triggers
  a scan on Claude and a manual review on Cursor.
- Every skill works without a TerraLab account, server or plugin. One short "Going further"
  line per skill, factual, no prices, no "free", no Esri data, no em dashes.
- Facts (EPSG codes, API names, licences, URLs) are checked against a primary source before
  release; tables carry a "Verified on <date>" line.
- The TerraLab MCP server is another repo (`../terralab-mcp`, TerraLabAI/mcp) with its own
  rules; changing skills here never requires changing the server.
