# VELOCITY — A Highway Study

A 120-second locally rendered 3D highway film created without real driving footage or an external video-generation model.

The hero is a proportioned dark-blue performance coupe. Traffic vehicles occupy authored lanes at varied plausible speeds, with sparse deliberate lane changes. The hero cruises near normal highway speeds, accelerates in two windows, then returns to a night-time cruise. Speed is communicated through actual world velocity, lane/guardrail parallax, lens changes, controlled camera vibration, engine/wind/tire audio, traffic pass-bys, dusk-to-night lighting, streetlights, reflectors, overpasses and skyline depth.

All picture rendering, audio synthesis, editing and QA are local.

## Audit-driven iteration 02

The original reviewed candidate is preserved at `baseline/velocity-v1.mp4`. Iteration 02 replaces stepped picture speed with a shared continuous speed model used by both picture and audio; removes modulo-recycled traffic and fixes lane-change snap-back; uses variable shot durations and a less periodic camera sequence; reframes wheel-detail coverage; raises the night exposure floor; adds procedural road/body detail and an ending credit; and replaces the near-mono air/pass-by mix with genuinely separated stereo layers.

A new `scripts/cinematicqactl.py` complements the legacy Creative QA with acceleration continuity, traffic trajectory continuity, periodic camera reuse, exposure/detail, stereo spatialization, picture/audio speed-model SHA agreement, and plan-hygiene gates. The current v2 passes every new gate except the late-frame detail-energy floor, so it is intentionally marked `REFINEMENT_REQUIRED` rather than falsely promoted to final.
