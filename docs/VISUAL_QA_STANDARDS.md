# Visual QA Standards

These are hard production gates for serious renders.

The reason they are strict is practical: several of these rules came directly from defects that were visible in otherwise successful renders. If the MP4 technically works but a character floats above the floor or an effect is visibly detached from the object producing it, the production is still wrong.

## Validation levels

Match the validation method to the claim.

- **Structural validation** can prove relationships such as shared anchors, inherited portal geometry, legal canvas metadata, or deterministic camera transforms.
- **Technical render validation** can prove codec, dimensions, FPS, duration, audio stream, decode, and other file properties.
- **Visual validation** can prove whether the chosen geometry, composition, acting, safe regions, and effects actually look correct in the rendered output.
- **User review** is required when a formal visual baseline claims user-accepted appearance.

Do not treat a structural test as proof that an example coordinate is visually correct.

## 1. One coordinate system for one physical set

Elements that belong to the same set should derive from the same canonical geometry.

Do not separately guess values such as:

- character floor Y;
- portal frame center;
- portal energy center;
- held-prop location;
- camera crop offsets.

Define named anchors and transform related elements together.

The main rule is that physical relationships should come from shared scene data, not from two coordinate tables that merely look close enough in one shot.

See `docs/SCENE_GEOMETRY.md` for the currently formalized 2D contract.

## 2. Character grounding

Every standing character should have a foot/ground anchor.

Check that:

- the feet contact the intended floor plane;
- contact shadow or ground cue agrees with the feet;
- changing sprite or pose bounds does not make the character float;
- different poses preserve the same ground anchor unless the character intentionally jumps or falls;
- camera cuts preserve world height and scale relationships.

A practical 2D rule is:

`character_screen_y = project(set.floor_anchor(character_position))`

not:

`character_screen_y = guessed_sprite_top + height`

The visible feet-to-floor relationship is the authority.

## 3. Portal and effect alignment

A portal set object should define at minimum:

```json
{
  "center": [x, y],
  "outer_radius": 120,
  "inner_radius": 94,
  "orientation_degrees": 0
}
```

The green or energy effect inherits the **inner center, radius, and orientation** of the gray/black physical portal frame.

Do not maintain a second unrelated `PORTAL_POS` table for the effect when the frame already owns the canonical geometry.

Check that:

- the glow is concentric with the physical frame;
- energy does not visibly spill outside the frame except for intentional bloom;
- camera crops transform the frame and effect together;
- portal size remains physically consistent across shots.

The relationship can be unit-tested. The actual center/radius values still need visual validation in the production render.

## 4. Prop attachment

Held objects inherit hand anchors. Screen content inherits monitor or display bounds. Effects inherit their emitters.

When the parent moves, the child should move through the same transform hierarchy rather than being repositioned independently by eye.

## 5. Depth and layering

Define intentional depth order for background set, portal interior/energy, characters, creatures/props, foreground architecture, subtitles, and UI when the shot needs those relationships.

Reject accidental overlaps that make an object look pasted onto a character or allow a character to cover foreground architecture that should physically be in front.

Do not freeze one universal z-order schema until the production has enough repeated evidence to justify it.

## 6. Composition

For each shot:

- the main speaker or action should read first;
- effects should not dominate unless they are the actual story beat;
- close-ups should avoid distracting clipped geometry;
- characters should not become tiny without a narrative reason;
- subtitles should not cover important acting or action.

The point is readability, not simply filling the frame with activity.

Safe margins and text-safe regions should become numeric production rules only after the target format and accepted examples establish them. Until then, inspect them visually instead of inventing universal values.

## 7. Animation acting

Do not let dialogue scenes become long stretches where only the mouth changes.

Use purposeful combinations of head turns/tilts, eye tracking/blinks, arm and hand gestures, weight shifts, anticipation, recoil/follow-through, and reaction beats.

Not every character needs constant movement. Movement should support the beat instead of becoming random noise.

## 8. Scene-boundary QA

Inspect frames immediately before and after every assembled cut.

Look for black frames, stale subtitles, scale jumps, unexplained position changes, visual discontinuities, and audio discontinuities. Independently good scenes can still fail at the seam.

## 9. Final MP4 QA

Validate codec, dimensions, FPS, duration, audio stream, successful decode, representative frames, effect events, dialogue close-ups, and the end card.

Then make the final judgment from the rendered video itself. The viewer sees the MP4, not the render log.

If a production is being promoted into a formal B-series visual baseline, preserve the exact artifact and evidence required by `baselines/README.md`.
