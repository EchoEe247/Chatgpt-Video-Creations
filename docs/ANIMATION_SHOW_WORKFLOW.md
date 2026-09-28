# Original Animation Show Workflow

## Core rule

For a new show, I want the show and season to exist as a coherent idea before Episode 1 becomes a production commitment.

The point is not to over-plan every future detail. The point is to avoid making Episode 1 in isolation and then discovering afterward that the season has no direction, the characters do not have stable rules, or later episodes need setups that the first episode never knew about.

## Phase 1 — Research and creative exploration

Research can cover storytelling structure, pacing, genre expectations, audience behavior, subject matter, science, history, folklore, technology, production techniques, and reusable asset options that help us understand how to build the show efficiently.

For production technique, use practitioner tutorials/transcripts, official documentation, breakdowns, and open-source examples when they can prevent repeated blind experimentation. For assets, prefer legitimately reusable free resources and record provenance/usage terms when they enter the production.

That research is input, not identity. The result should still have original characters, names, world rules, dialogue, visual identity, and story logic. External online video generators are not the default episode renderer.

See `docs/RESOURCE_SOURCING.md`.

## Phase 2 — Build the show foundation

Create and review:

- `SHOW_BIBLE.md` — premise, identity, tone, format, and core rules;
- `WORLD.md` — world mechanics, important locations, and boundaries;
- `CHARACTERS.md` — recurring cast, motivations, flaws, relationships, and voice patterns;
- `STYLE_GUIDE.md` — 2D/3D approach, proportions, palette, camera language, and audio identity;
- long-term story threads and contradictions that are not allowed.

Episode rendering should not start until this foundation is coherent enough to support a season. It does not need to be permanently frozen, but it should be strong enough that the production knows what it is trying to preserve.

## Phase 3 — Plan the season

Establish:

- the season theme and dramatic/comedic engine;
- beginning state;
- major turning points;
- finale and end state;
- ordered episode map;
- setup/payoff dependencies;
- story/dialogue foundation for the planned episodes;
- continuity expectations.

The season plan can still evolve. I just want Episode 1 to know what future episodes may need from it instead of treating every episode as a separate generation problem.

## Phase 4 — Produce one episode at a time

Once the season foundation is approved, implementation becomes intentionally narrow:

1. select the next episode;
2. load current accepted canon and unresolved threads;
3. finalize that episode's script/dialogue;
4. build and validate the detailed scene plan, including important review points;
5. resolve the episode's high-impact asset strategy and, for serious 3D work, complete the required visual-development gates: moving previs for timing/blocking/camera/screen geography, representative look-dev for materials/lighting/integration, and a deliberate Blender compositing strategy;
6. prove any multipass/hybrid path on a representative frame or short range before committing to an expensive sequence render;
7. render scenes independently;
8. assemble the master;
9. run deterministic technical/audio QA and build the review pack;
10. run assistant visual, acting, continuity, scene-boundary, and story review on the actual final candidate;
11. when assistant review finds a defect, repair and re-QA internally without handing that intermediate candidate to the user;
12. repeat within the configured autonomous repair budget until the assistant gate passes;
13. present the final candidate for user acceptance;
14. if the user requests refinement, return to the autonomous repair/re-QA loop;
15. only after technical, assistant, and user gates pass, mark the episode `DONE ✅` and update canon.

Previs/look-dev approval is development evidence, not episode acceptance. It only proves that specific upstream decisions are ready for production. Final creative QA still binds to the encoded episode candidate.

See `docs/VISUAL_DEVELOPMENT.md` for the visual-development contract and `docs/CHARACTER_PRODUCTION.md` for character/rig/action sourcing and performance assembly.

Do not start the next episode while the current one is still `REFINEMENT_REQUIRED`. Finishing one accepted episode is more useful than spreading unresolved defects across several unfinished episodes.

## Episode state model

Recommended statuses:

- `PLANNED`
- `RENDERING`
- `CANDIDATE`
- `ASSISTANT_REVIEW`
- `REFINEMENT_REQUIRED`
- `USER_REVIEW`
- `BLOCKED`
- `DONE`

Use `scripts/productionctl.py` as the state authority for new production packages. `USER_REVIEW` is reachable only after technical and assistant gates pass.

`DONE` requires:

```json
{
  "assistant_review": "PASS",
  "user_review": "PASS",
  "continuity_updated": true
}
```

A successful render alone does not satisfy this state.

## Episode package

```text
episode-01/
├── status.json
├── episode-plan.md
├── script.md
├── scene-plan.json
├── continuity-in.json
├── assets/
├── development/
│   ├── previs/
│   ├── lookdev/
│   └── compositing-proof/
├── renders/scenes/
├── qa/
├── final/
└── continuity-out.json
```

## Season completion

After the final episode passes:

- reconcile the full season canon;
- verify episode order, titles, and runtime metadata;
- build the season-level release/publishing package;
- preserve unresolved threads that are intentionally continuing into the next season;
- do not silently retcon accepted episodes while packaging the season.

Accepted episodes are production history. If something needs to change later, treat that change deliberately instead of pretending the previous accepted state never existed.
