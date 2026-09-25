# Long-Form Scene Architecture

## Principle

For long-form work, the final video is a master production assembled from independently rendered scenes.

I do not want to lower the whole animation quality just to make a two-minute or longer render fit through one giant scene. The better approach is to preserve the richer short-scene baseline, render manageable sections, fix them individually, and assemble the accepted pieces into the master.

## Master timeline first

Before individual rendering starts, define the whole episode or video:

- exact duration target;
- scene order and time ranges;
- dialogue and master-audio positions;
- music and ambience continuity;
- character and set continuity state;
- transitions;
- camera intent.

Each scene then receives its own timeline range and continuity input. That keeps independently rendered scenes connected to one production rather than becoming unrelated clips that happen to be concatenated later.

## Independent scene rendering

Typical working ranges:

- 2D: commonly 5–15 seconds;
- 3D: commonly 4–12 seconds;
- business motion: can run longer when scene complexity is low.

These are production guidance, not hard caps. Use the duration that lets the scene keep the needed quality and remain practical to inspect and replace.

Each scene should render at the appropriate FPS and resolution instead of inheriting an unnecessary whole-video quality compromise.

## Scene handles

For transitions or continuous action, render extra handle frames when they help.

Example:

- intended Scene A: `00:18–00:27`;
- render: `00:17.5–00:27.5`.

The overlap gives us room to choose a cleaner cut and verify continuity without having to regenerate an entire sequence.

## Master audio

Prefer one continuous master audio timeline for dialogue, ambience, music, and cross-scene SFX.

That separation is useful because a visual scene can be replaced without restarting or drifting the whole audio bed. Scene boundaries should serve production, not force audible boundaries into the final video.

## Scene QA before assembly

Check each scene for:

- successful decode;
- correct duration and FPS;
- correct starting and ending continuity state;
- no floor-anchor or source/effect drift;
- correct dialogue acting and subtitle timing;
- no unintended clipped props or characters.

A scene that fails should be repaired before it becomes part of the accepted master.

## Assembly

Assembly order must be explicit, not inferred from whatever MP4 files happen to be present in a directory.

Create an ordered manifest based on `templates/scene-assembly.json`, listing each scene ID and path and, when useful, its expected duration and SHA-256. Run:

```text
python scripts/assemble-scenes.py scene-assembly.json final/master.mp4
```

The assembler uses only those listed inputs, rejects missing/duplicate scenes and output-as-input collisions, verifies compatible stream signatures and optional duration/hash constraints, and decode-checks the master after concat-copy.

Avoid unnecessary re-encoding when scene formats match.

After assembly, inspect the seams and representative interior frames. A set of individually valid scenes can still produce a bad master if a cut introduces a position jump, stale subtitle, audio discontinuity, or other continuity problem.

## Why this architecture matters

If Scene 6 is wrong, I want to replace Scene 6.

Do not rerender Scenes 1–5 and 7–12 unless a shared asset, timing, or continuity change genuinely requires it. Long-form production becomes much more practical when a local defect stays local.