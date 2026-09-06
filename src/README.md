# Reusable Render Source

Reusable production code belongs here, separate from one-off project assets.

Intended boundaries:

```text
src/
├── core/          # timelines, scene transforms, audio, assembly, QA
├── business/      # release cards, product demos, motion graphics
├── animation_2d/  # rigs, sets, camera, effects, renderer
└── animation_3d/  # rigs, sets, camera, lighting, effects, renderer
```

Prefer shared set/anchor abstractions so characters, effects and cameras consume one geometry definition.
