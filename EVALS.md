# Evaluations

Each skill has `skills/<name>/evals/evals.json`: three realistic prompts, each aimed at a trap the skill fixes, with the behavior we expect and what must not happen.

## Run them by hand

1. Open a fresh agent session without the skill installed. Paste each prompt. Note the answer.
2. Install the skill (`npx skills add TerraLabAI/geoai-skills --skill <name>`), open a fresh session, paste the same prompts.
3. For each prompt, mark pass when every `expected_behavior` item is met and no `must_not` item appears.

The skill earns its place when the run with it passes and the run without it misses at least one item. A run with the skill that fails points to a gap to fix in `SKILL.md`.

## Before each release

All evals are run with the skill, on at least one agent, before each release. Every `evals.json` must parse:

```bash
for f in skills/*/evals/evals.json; do python3 -m json.tool "$f" > /dev/null || echo "bad: $f"; done
```
