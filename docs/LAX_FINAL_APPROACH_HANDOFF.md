# LAX — Final Approach: paused handoff

Status: **paused / resumable, not promoted**

Production: `productions/standalone/lax-arrival`

Current preserved review candidate: `final/lax-final-v11.mp4`

Current candidate SHA-256: `8515f639e98453b2438c32ef038f186c439df2755c64aa5206a8c811e9aa840d`

Saved continuation scene: `source/lax-arrival-v11-reviewfix-scene.blend`

## Why this is paused

Further work is intentionally stopped. This production is worth resuming when the user is specifically asking for an airplane flight, approach, landing, rollout, or closely related aviation film. Do **not** keep iterating on it merely because it exists.

That does not promote the current film to the repo's **respectful** quality status or to a cinematic baseline. The current user quality state remains `below_respectful_salvageable`.

## What v11 already established

Keep these fixes. Do not restart from the original scene or silently regress them:

- the imported widebody asset's forward-axis error was diagnosed and corrected at the scene hierarchy level;
- LAX-specific environment structure was expanded with CTA/Tom Bradley/West Gates-inspired massing, Theme Building cues, ramp/airfield detail, parked aircraft and service activity;
- the exposed blue-world “ground” failure was diagnosed as missing continuous terrain beneath city/road geometry and repaired with LA-basin/airport ground surfaces;
- the delivery player supports seeking and HTTP byte ranges;
- native temporal sampling was raised from the earlier 2 fps salvage source to a 6 fps / 720-frame source for the later production path;
- v11 replaces the externally criticized 22–65 s region with a 43 s / 258-frame native-6-fps Blender segment using closer/moving cameras, stabilized close shots, procedural ground variation and held lighting continuity;
- the current v11 master is exactly 120.0 s, 1280×720, 24 fps / 2880 frames, AAC stereo and decode-clean.

## Known unresolved work

These are the reasons the production remains paused below respectful:

1. **Native motion cadence is still the largest technical/visual ceiling.** The user still judged the result insufficiently smooth after the 2→6 fps improvement. Interpolation is finishing, not a substitute for adequate native Blender sampling. A resumed final-quality pass should render the important motion natively at materially higher cadence—prefer native 24 fps when practical, or at least a genuinely higher intermediate cadence before 24 fps delivery.
2. **Review v11's 22–65 s repair before spending on another full render.** External review had identified the old 36–64 s distant-plane hold and 28–32 s smeared close-up as major pacing/image defects. v11 specifically rebuilt that region, but it has not received a new final user quality judgment after the repair.
3. **The early 0–22 s ground pass still needs deliberate review/repair.** External review reported streaky/banded ground artifacts consistent with overlapping surfaces/z-fighting. A planned v11 rerender of this range did not complete and is not included in the final v11 master.
4. **Touchdown mechanics remain unfinished.** A planned 95–104 s rerender with visible oleo/gear compression, stronger touchdown smoke and control-surface changes did not complete and is not included in v11. Finish and verify landing-gear compression/rebound, wheel behavior, tire smoke, spoiler deployment, reverse-thrust phase and aircraft body response.
5. **Control surfaces need physically motivated animation.** Ailerons, rudder/elevator, flaps/spoilers should react to the actual approach/flare/rollout phases rather than remain visually static.
6. **Environment realism still has headroom.** Replace obvious box-primitive reads with stronger terminal/ramp silhouettes, runway/taxiway markings and lighting, pavement material breakup, atmospheric depth/haze and controlled object LOD/pop-in.
7. **Lighting continuity needs a deliberate grade.** The prior review called out an abrupt daylight-to-blue shift near the mid-film transition. v11 holds the world state through its repaired segment; a resumed pass should review the complete film for exposure/color continuity instead of applying an unmotivated time-of-day jump.
8. **Audio is technically valid but not finished creatively.** Last measured mix was about -15.1 LUFS integrated with -1.2 dBTP and ~4.5 LU range. Add more physical phase contrast—air/wind, touchdown transient, reverse thrust and rollout ambience—and leave safer peak headroom (about -2 dBTP or below) if remastering.
9. **Context/presentation can improve.** Add a deliberate opening title and ending card/identity treatment if the next brief calls for a finished short rather than a pure flight study.
10. **Do not upscale as a substitute for scene quality.** 1080p / 30–60 fps delivery is appropriate only after geometry, materials, motion and lighting hold up; first solve the scene and native cadence.

## Resume order

When the user asks for this kind of aviation work again:

1. bootstrap the **cinematic** workflow and verify the current Local Workspace compatibility contract;
2. open this handoff, `production.json`, `final/qa-summary.json`, and `source/lax-arrival-v11-reviewfix-scene.blend`;
3. review the exact v11 candidate first, especially 0–22 s, 22–65 s, the ~64 s lighting transition and 95–104 s touchdown;
4. render only the shots that still fail—do not repeat already-good shots;
5. prioritize **native smoothness + ground/material correctness + touchdown physics** before more cosmetic post work;
6. perform encoded-candidate visual review, audio review, seekability/decode QA and user review before calling it ready.

## Scope lesson

Use LAX as **aviation-production learning evidence**, not as a general cinematic baseline. Its durable lessons are useful for future flying/landing films: prove semantic direction early, prove the environment from final cameras, use adequate native temporal sampling, and validate flight-to-contact physics before expensive finishing.
