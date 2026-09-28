# 2026-09-28 cinematic quality feedback and documentation refresh

## Status

Documentation-only workflow refresh. Further LAX production work is paused. The local LAX review server and render/finalizer processes were stopped; the local production payload remains available for a later deliberate rebuild.

## User quality outcomes captured

- Severance-style show candidate: **trash / failed**.
- Alien/Avatar concept candidate: **medium-bad**.
- LAX landing candidate: **medium-bad, currently closer to bad**.
- LAX concrete defects: the airport/environment reads unfinished, and aircraft direction/orientation can read as though the plane is moving backward.

None of these three candidates is an accepted realistic/cinematic visual baseline.

## Durable workflow changes

1. Motion-density/freeze activity is no longer treated as evidence that motion is semantically correct. Moving-subject previs must check local forward axis, travel vector, screen direction, camera relationship and contact/phase kinematics.
2. Environment asset presence is no longer treated as evidence that the world is finished. Representative look-dev/final review must judge environment completeness from actual hero/wide/action cameras.
3. A later negative user review supersedes earlier internal green QA for acceptance and baseline-promotion purposes.
4. Review pages must be practically seekable/rewindable/scrubbable before user handoff.
5. The historical V2 3D reference is scoped to stylized real-3D capability. There is currently no accepted realistic/cinematic visual baseline.
6. Outcome learning now applies to decisive negative results as well as respectful/good results.

## Documentation touched

- `README.md`
- `AGENTS.md`
- `docs/CAPABILITY_BASELINES.md`
- `docs/CHATGPT_SHOT_WORKFLOW.md`
- `docs/CREATIVE_QA_WORKFLOW.md`
- `docs/EVIDENCE_FIRST_REVIEW.md`
- `docs/LOCAL_WORKSPACE_VIDEO_WORKFLOW.md`
- `docs/OPERATING_MODEL.md`
- `docs/OUTCOME_LEARNING_LOOP.md`
- `docs/PRODUCTION_WORKFLOW.md`
- `docs/QUALITY_FLOOR.md`
- `docs/REFERENCE_SAMPLES.md`
- `docs/VISUAL_DEVELOPMENT.md`
- `workflow/CURRENT.json`

Canonical workflow version after this refresh: **2026.09.28.9**.

## Validation

- Local markdown link audit: 0 broken local links.
- `git diff --check`: clean.
- No production-code changes are part of this refresh.
