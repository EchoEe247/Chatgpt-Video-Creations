# Operating Model

This repository should become easier to work with as we understand it better.

The working philosophy is:

**think freely → clarify carefully → plan deliberately → build precisely → validate → establish a trusted baseline → automate what is understood → keep checking alignment**

The maturity progression underneath that is:

**experiment → understand → formalize → validate → baseline → operate**

This is not a reason to turn creative video work into a rigid engineering exercise. The point is narrower: keep judgment where judgment is useful, and remove repeated guesswork from relationships we have already learned well enough to preserve.

The order matters. Do not jump from **experiment** to **formalize**, or from **technically reproducible** to **baseline**. A creative production method earns operating-mode status only when the relevant behavior is understood and its output quality has actually survived review. Tests, hashes, deterministic rendering and reproducibility can prove control of a process; they cannot by themselves prove that the resulting film is good.

For user quality language, **respectful** is a useful intermediate milestone: preserve the candidate and continue investing in it because it is worth working on and could become releasable. It does not mean finished, accepted canon, release-ready, or baseline-worthy.

## Discovery mode and operating mode

### Discovery mode

Use interactive work when an important part of the problem is still unresolved.

Examples:

- visual composition still needs user judgment;
- the right character scale is not established;
- a set's real floor line has not been measured from an accepted render;
- a camera style is still being explored;
- a show premise, character decision, or season direction is still open;
- a business video's strongest story or hook is still being chosen.

In discovery mode, provisional coordinates, timing, poses, and experiments are allowed. They should be treated as provisional rather than silently becoming project truth.

The loop is:

**inspect → experiment → render → review → diagnose → adjust**

### Operating mode

Move a problem into operating mode only after the relevant behavior is understood well enough to encode and validate.

Examples:

- character feet use a defined local foot anchor and land on a set floor anchor;
- portal energy inherits the physical portal opening instead of maintaining a second guessed center/radius;
- an exact release/version snapshot controls a business video's claims;
- accepted episode canon controls the next episode's continuity;
- known-good render settings are reused rather than rediscovered;
- a validated previs, look-dev artifact, or compositing proof is reused as an upstream comparison point without being mistaken for final-candidate acceptance.

The loop becomes:

**inspect → implement within the established contract → validate → diagnose failures → fix → revalidate → review → record receipt**

Operating mode is where longer local-agent work becomes reasonable.

## What should become formal

Do not formalize something merely because it can be represented in JSON or code.

Promote a relationship into repository structure when most of these are true:

1. it has shown up more than once or is clearly reusable;
2. the relationship is understood rather than guessed;
3. future scenes or agents would otherwise have to rediscover it;
4. it can be stated precisely enough to test, inspect, or compare;
5. making it explicit will not erase useful creative freedom.

Appropriate representations include dimensions, coordinates, formulas, anchors, geometry, schemas, timing rules, safe regions, scaling rules, templates, examples, tests, and documentation.

The representation should be as small as the problem allows.

## Current realistic/cinematic maturity state

The realistic/cinematic lane is **not yet at a trusted visual baseline**. Keep the engineering controls that have been validated, but keep the creative production method in discovery/validation until repeated user-reviewed results justify promotion.

Current exact user-evaluated examples:

- **RIDGELINE — A Descent** — latest mountain-bike candidate: **respectful**; keep and continue, but not finished.
- **VELOCITY — A Highway Study** — latest reviewed `velocity-recreation` highway-driving candidate: **respectful**; keep and continue, but not finished.
- **LAX — Final Approach** — below respectful but potentially salvageable after major environment, landing-mechanics, motion-direction, aviation-audio and visual-quality improvements.
- **AETHERFALL — THE LAST LIGHT** — medium-bad; concept/character/audio result not promoted.
- **THE EIGHTH HOUR** — trash/failed; failure evidence only.

The two respectful candidates are evidence that parts of the process are becoming useful. They are **not** permission to declare the entire cinematic method solved. The weak/rejected candidates are evidence about what still needs to be discovered or gated earlier.

## Current maturity map

### Established and reusable

The following ideas are established enough to treat as project rules:

- business marketing is grounded in an exact user-facing release;
- long-form animation uses independently rendered scenes rather than one giant degraded render;
- high-impact production assets use an explicit make-vs-source decision: **source nouns, author verbs**;
- serious 3D work separates moving previs, representative look development, compositing proof, final rendering, and final-candidate QA instead of asking one render to prove all of them;
- required previs/look-dev gates must be explicitly approved before expensive final cinematic execution is considered ready; `not_required` is only valid where the applicable quality floor genuinely permits it (for example a prototype or non-applicable lane);
- Blender compositing strategy is intentional per shot: `beauty_only`, `multipass`, or `hybrid`, with multipass/hybrid justified by concrete finishing goals;
- episode acceptance requires assistant QA and user review before canon advances;
- one physical 2D set uses one shared geometry source;
- standing characters place a local foot/contact anchor onto a set floor anchor;
- portal energy inherits the physical portal opening's center and radius;
- camera transforms move related set geometry together;
- final MP4 review is required; successful code execution is not acceptance.

### Structurally implemented, still awaiting visual promotion

The shared 2D geometry layer under `src/core/geometry.py` and `src/animation_2d/layout.py` has regression tests for the relationships above.

Those tests prove structural consistency. They do **not** prove that the current example lab numbers are visually correct.

The next visual step is to connect the actual scene renderer to this geometry layer, render a corrected reference scene, review it, and only then preserve the exact set/rig values that pass.

### Intentionally still provisional

Do not manufacture canonical values yet for:

- the accepted lab set's exact `floor_y`;
- the accepted portal frame's exact center/radii in the production renderer;
- character bounding boxes and preferred per-shot scales;
- action-safe and text-safe margins;
- canonical z-order for every type of shot;
- reusable camera presets;
- pose-specific contact anchors beyond the rigs we have actually measured;
- animation timing that has not been reviewed in rendered output.

These are good candidates for formalization after we have evidence. They are not solved merely because we can invent plausible numbers.

## Validated baselines

A project release and a validated baseline are different.

A release such as `v0.2.0` identifies a version of software or content.

A validated baseline such as `B1` means:

> At an exact repository state, these named capabilities were tested under these conditions and are known-good to the level claimed.

Formal baseline rules live in `baselines/README.md`.

The important discipline is that a baseline is earned by evidence. A code commit, a green unit test, or an MP4 that merely decodes is not enough for a visual baseline.

## Working from a baseline

When a baseline exists and a later change causes a regression:

1. reproduce the newer failure;
2. compare against the last relevant known-good baseline;
3. identify what changed in implementation, geometry, assets, timing, or render conditions;
4. make the narrowest correct repair;
5. revalidate the affected capability;
6. promote a new baseline only if the newer state is genuinely known-good.

Do not start over from zero while a trustworthy comparison point exists.

## Agent autonomy gate

Longer autonomous work is appropriate when the repository gives the agent enough constraints to stay aligned.

Before a long local-agent loop, confirm that the task has:

- a clear project goal and lane;
- explicit scope and non-goals;
- established architecture for the area being changed;
- useful acceptance criteria;
- validation that can catch meaningful failures;
- a known-good example or baseline when regression risk is material;
- a rollback/comparison point;
- rules for what may be changed;
- clear stop or escalation conditions.

When those conditions are present, the agent may use a longer loop:

**inspect → implement → validate → diagnose → fix → revalidate → review → document receipt → continue within scope**

## Stop and escalate

Keep the work interactive instead of inventing a decision when:

- a product or architecture choice is genuinely unresolved;
- a visual tradeoff requires user taste rather than a known rule;
- a story, character, season, or marketing decision changes creative direction;
- a change would invalidate an accepted baseline and the regression cannot be explained;
- the agent would need to invent canonical coordinates, safe zones, scales, timing, or limits without evidence;
- repository sources disagree about project truth;
- the required validation cannot actually test the claimed result.

The goal is not maximum autonomy. The goal is trustworthy autonomy without drift.

## Alignment is continuous

Formalization is not the end of judgment.

Known-good rules should keep being checked against real output. If the production changes enough that an old rule no longer fits, update it deliberately with new evidence rather than keeping it forever because it was once encoded.