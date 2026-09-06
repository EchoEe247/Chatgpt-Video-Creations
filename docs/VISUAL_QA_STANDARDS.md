# Visual QA Standards

These are hard production gates for serious renders.

## 1. Shared set coordinate system

Elements that belong to one physical set must derive from the same canonical set geometry.

Do not separately guess:

- character floor Y;
- portal frame center;
- portal energy center;
- held-prop location;
- camera crop offsets.

Instead define named anchors and transform them together.

## 2. Character grounding

Every standing character has a foot/ground anchor.

Required checks:

- feet contact the intended floor plane;
- contact shadow/ground cue agrees with feet;
- character does not float because the sprite bounding box changed;
- different poses preserve the same ground anchor unless the character intentionally jumps/falls;
- camera cuts preserve world height/scale relationships.

A practical 2D rule:

`character_screen_y = project(set.floor_anchor(character_position))`

not `character_screen_y = guessed_sprite_top + height`.

## 3. Portal/effect alignment

A portal set object should define at minimum:

```json
{
  "center": [x, y],
  "outer_radius": 120,
  "inner_radius": 94,
  "orientation": 0
}
```

The green/energy effect inherits the **inner center/radius/orientation** of the gray/black physical portal frame.

Do not maintain a second unrelated `PORTAL_POS` table for the effect if the frame already has canonical geometry.

Required checks:

- glow is concentric with physical frame;
- energy does not visibly spill outside the frame except intentional bloom;
- camera crops transform both together;
- portal size stays physically consistent across shots.

## 4. Prop attachment

Held objects inherit hand anchors. Screen content inherits monitor/screen bounds. Effects inherit emitters.

If the parent moves, the child follows through the same transform hierarchy.

## 5. Depth/layering

Define intentional depth ordering for:

- background set;
- portal interior/energy;
- characters;
- creature/props;
- foreground architecture;
- subtitles/UI.

Reject accidental overlaps that make a creature look pasted onto a character or let a character improperly cover foreground architecture.

## 6. Composition

For each shot:

- main speaker/action reads first;
- effects do not dominate unless they are the story beat;
- close-ups do not include distracting clipped portal geometry;
- characters are not tiny without narrative reason;
- subtitles do not cover important acting/action.

## 7. Animation acting

Reject scenes where only the mouth changes for too long. Use purposeful combinations of:

- head turns/tilts;
- eye tracking/blinks;
- arm/hand gestures;
- weight shift;
- anticipation;
- recoil/follow-through;
- reaction beats.

## 8. Scene-boundary QA

Inspect frames immediately before and after every assembled cut. Verify there are no black frames, stale subtitles, scale jumps, unexplained position changes or audio discontinuities.

## 9. Final MP4 QA

Validate codec, dimensions, FPS, duration, audio stream, decode, representative frames, effect events, dialogue close-ups and end card.
