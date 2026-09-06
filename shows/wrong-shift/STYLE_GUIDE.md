# Wrong Shift — Style Guide

## Visual direction
Graphic limited 2D animation with deliberately readable silhouettes, imperfect hand-drawn-feeling shapes, and restrained motion. The production should look intentional rather than like static assets being moved around.

## Color language
Normal RealityCare / ordinary spaces:
- desaturated blue-gray, beige, brown, muted workwear;
- fluorescent practical lighting;
- paper/signage textures and subdued screens.

Continuity anomalies:
- brighter green/cyan/magenta accents;
- geometry, light, or UI behavior can become subtly wrong;
- use contrast so anomaly color means something rather than coloring every shot loudly.

## Animation language
Rae:
- small head turns, gaze changes, blinks;
- minimal arm travel;
- closed stance;
- nervous tape-check/straightening tell.

Owen:
- larger arm arcs;
- leaning and recoil;
- tablet interaction;
- open stance and visibly changing weight.

Limited animation is acceptable and preferred over generic over-smoothing. Repetition should still be character-specific.

## Geometry
B1 is the current trusted 2D geometry/composition reference. Reuse its principles, not blindly its exact lab measurements:
- characters are placed from local foot anchors onto a set-owned floor/contact line;
- parent effects/props inherit shared world anchors;
- camera crops/transforms use shared world coordinates;
- world-space text/boards transform as one object when they belong to the environment.

## Camera
Favor clear coverage:
- wide for premise/location relationships;
- two-shot for character contrast;
- close-ups for reactions;
- inserts for machine/ticket/evidence information;
- avoid camera motion unless it serves discovery or escalation.

## Text and UI
- no text may overflow its owning sign/card;
- maintain meaningful bottom safe clearance for subtitles;
- subtitles use stable speaker-name treatment and high contrast;
- environmental text should remain readable enough to reward pause/rewatch but is secondary to dialogue.

## Audio
- recurring characters receive distinct voice identities;
- current casting direction: Owen deep male, Rae lighter female;
- fast conversational rhythm, never rushed or mushy;
- 48 kHz stereo production master;
- dialogue is the priority in the mix;
- environmental/anomaly sound remains audible but ducks beneath speech;
- target around -16 LUFS integrated and approximately -1 to -1.5 dBTP for web review masters.

### Audio bus architecture
Episode audio must not mix the continuous bed and every delayed dialogue clip in one large `amix` graph. S01E01 demonstrated that this can produce intermittent digital-zero gaps later in a long timeline even when the bed source itself is continuous.

Use two stable stages instead:
1. build a speech-only bus from the timed dialogue clips;
2. keep the full-duration room/music/anomaly bed as its own bus;
3. optionally duck the bed from the speech bus;
4. combine only the stable bed and speech buses into the premaster;
5. loudness-normalize after that two-bus mix.

Long-form audio QA must scan the complete master timeline, not only representative moments. A Wrong Shift episode with a continuous room/anomaly bed must have zero unintended one-second digital-silence windows, including after scene boundaries and late in the episode.

## Production master
Target for episodes:
- 1280×720 minimum;
- 24 fps delivery;
- H.264/yuv420p review master;
- high-quality encode suitable for platform recompression;
- scenes rendered independently and assembled into one master timeline.
