# Productions

Real production packages live here.

## Business

`productions/business/<repo>/<release>/`

Preserve each release package historically. A newer release gets a new directory rather than rewriting the old video's provenance.

## Shows

`productions/shows/<show>/`

Recommended structure:

```text
<show>/
├── SHOW_BIBLE.md
├── WORLD.md
├── CHARACTERS.md
├── STYLE_GUIDE.md
├── continuity/
└── seasons/
    └── season-01/
        ├── SEASON_PLAN.md
        ├── SEASON_ARC.md
        ├── DIALOGUE_MASTER.md
        └── episodes/
            └── episode-01/
```

Use `templates/` when starting a production.

## Local Workspace-era production package

New serious productions should include a `production.json` created from `templates/production-v2.json`. That manifest is the restart-safe state authority for render configuration, QA gates, artifacts, repair history, blockers, and final acceptance.

For episode packages, keep `production.json` beside the episode plan/scene plan and store generated QA evidence under `qa/`.

Use `scripts/productionctl.py status <production.json>` after any interruption instead of reconstructing state from chat history.
