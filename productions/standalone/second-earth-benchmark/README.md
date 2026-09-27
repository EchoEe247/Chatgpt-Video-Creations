# SECOND EARTH benchmark

This is the fresh integrated benchmark planned after the Mercy Engine workflow upgrades.

## Target

A 2:30 cinematic speculative AI story that is harder than Mercy Engine in shot density, scale changes, renderer diversity, and synchronization while remaining practical on the Pixel-local production stack.

The benchmark is intentionally split across three 25-minute runs:

- **Run 7 / Phase 7A:** story, directing, assets, storyboard, execution plan and shared A/V plan.
- **Run 8 / Phase 7B:** implement renderer sources, render shots, build narration/score/effects, assemble candidate.
- **Run 9 / Phase 7C:** technical + creative QA, targeted repairs, final candidate and user-review handoff.

## Current checkpoint

Phase 7A is complete when all of these pass:

    python scripts/directorctl.py validate-plan productions/standalone/second-earth-benchmark/source/execution-plan.json
    python scripts/timelinectl.py validate productions/standalone/second-earth-benchmark/source/av-timeline.json
    python scripts/validate-production-v2.py productions/standalone/second-earth-benchmark/production.json
    python -m pytest tests/test_second_earth_benchmark.py -q

The compiled director plan has:

- 150-second runtime;
- 21 purposeful shots, all 8 seconds or shorter;
- 7 hero shots;
- Python, Canvas2D, Blender and FFmpeg lanes;
- zero unresolved assets;
- zero blocked shots;
- zero director warnings;
- 134 shared A/V events;
- creative QA required before assistant PASS.

No online video-generation model is part of the production.

## Local-first assets

The first pass requires no new download.

It reuses:

- the integrated hand-drawn Canvas runtime;
- the existing Quaternius CC0 spaceship already present locally;
- the deterministic Core Audio Commons.

Optional Poly Haven / ambientCG CC0 additions remain non-blocking and are allowed only after a preview proves a specific quality improvement.

## Source of truth

Read these in order:

1. `source/story.md`
2. `source/director-brief.json`
3. `source/storyboard.md`
4. `source/asset-resolution.json`
5. `source/execution-plan.json`
6. `source/implementation-map.json`
7. `source/av-events.json`
8. `source/av-timeline.json`
9. `source/layout-qa.json`
10. `source/benchmark-acceptance.json`
11. `production.json`

Run 8 should not reopen story direction unless implementation proves a concrete shot impossible or materially weaker than its fallback.