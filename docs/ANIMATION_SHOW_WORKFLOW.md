# Original Animation Show Workflow

## Core rule

A new show is planned at the show and season level before episode implementation begins.

Do not create Episode 1 in isolation and improvise later episodes around it.

## Phase 1 — Research and creative exploration

Research may cover storytelling structure, pacing, genre expectations, audience behavior, subject matter, science/history/folklore/technology, and other creative inputs relevant to the concept.

Research is for synthesis and understanding. The resulting show must have original characters, names, world rules, dialogue, visual identity and story logic.

## Phase 2 — Show foundation

Create and review:

- `SHOW_BIBLE.md` — premise, identity, tone, format, rules;
- `WORLD.md` — world mechanics, locations, boundaries;
- `CHARACTERS.md` — recurring cast, motivations, flaws, relationships, voice patterns;
- `STYLE_GUIDE.md` — 2D/3D approach, proportions, palette, camera/audio language;
- long-term threads and forbidden contradictions.

No episode render starts until the foundation is coherent enough to support a season.

## Phase 3 — Season planning

Create:

- season theme and dramatic/comedic engine;
- beginning state;
- major turning points;
- finale/end state;
- ordered episode map;
- setup/payoff dependencies;
- dialogue/story foundation for all planned episodes;
- continuity expectations.

The season plan can be refined, but Episode 1 should know what future episodes need from it.

## Phase 4 — One episode per production turn

Once the season is approved, implementation becomes intentionally narrow:

1. select the next episode;
2. load current canon and unresolved threads;
3. finalize episode script/dialogue;
4. build detailed scene plan;
5. render scenes independently;
6. assemble master;
7. assistant reviews technical + visual + continuity quality;
8. user reviews;
9. if either review finds important defects, refine and re-render;
10. only after both pass, mark episode `DONE ✅` and update canon.

Do not start the next episode while the current episode remains `REFINEMENT_REQUIRED`.

## Episode state model

Recommended statuses:

- `PLANNED`
- `IN_PRODUCTION`
- `ASSISTANT_REVIEW`
- `USER_REVIEW`
- `REFINEMENT_REQUIRED`
- `DONE`

`DONE` requires:

```json
{
  "assistant_review": "PASS",
  "user_review": "PASS",
  "continuity_updated": true
}
```

## Episode package

```text
episode-01/
├── status.json
├── episode-plan.md
├── script.md
├── scene-plan.json
├── continuity-in.json
├── assets/
├── renders/scenes/
├── qa/
├── final/
└── continuity-out.json
```

## Season completion

After the final episode passes:

- reconcile the entire season canon;
- verify episode ordering/titles/runtime metadata;
- create season-level release/publishing package;
- preserve unresolved threads intended for the next season;
- do not silently retcon accepted episodes during packaging.
