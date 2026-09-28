# 2026-09-28 Astra audit repairs

Audit basis: `Chatgpt-Video-Creations-Audit-2026-09-28.md`, audited commit `071f411`.

## Repairs implemented

1. **Final-screening evidence authority**
   - Every final-screening evidence ID must resolve to `studio_review.evidence`.
   - Screening evidence must be `REVIEWED` and candidate-SHA bound.
   - Modality evidence must explicitly declare the modality it supports.
   - Missing/unknown/stale/modality-mismatched evidence keeps promotion fail-closed.

2. **CI test coverage and triggers**
   - Media-runtime CI now installs pytest.
   - CI verifies test collection and runs the complete `tests/` directory through pytest.
   - Workflow triggers cover maintained `src/**`, `scripts/**`, `tests/**`, `templates/**`, `workflow/**`, `docs/**`, and workflow files.

3. **Transactional studio-review publication**
   - `assistant-pass` evaluates the complete prospective promotion state before writing the immutable accepted studio review.
   - Rejected attempts no longer poison the accepted review path.
   - An orphan review left by the older failure mode may be replaced; an already-published accepted review remains immutable.

4. **Studio-review requirement precedence**
   - `workflow.studio_review_required` is authoritative when present.
   - Nested `studio_review.required=false` cannot downgrade a required workflow.
   - The production template now uses consistent required=true defaults.

5. **Bridge compatibility binding and dispatch revalidation**
   - Repository-native bootstrap explicitly reports bridge compatibility as unevaluated; final binding rejects that unevaluated result.
   - Final production binding requires evaluated compatible Local Workspace bootstrap evidence.
   - `workflowctl bind --bootstrap-result <json>` persists the evaluated bridge version/profile evidence.
   - `productionctl render-spec` and `productionctl rendering` initially rechecked supplied bootstrap evidence. **Superseded by workflow 2026.09.28.12:** dispatch now queries the running bridge readiness endpoint directly and does not treat saved bootstrap JSON as live evidence.

6. **Previs/look-dev/proof integrity**
   - Execution-plan compilation records SHA-256 for available approved visual-development artifacts and asset-proof artifacts.
   - Final preflight rejects missing hash bindings or changed bytes.
   - Previs must probe/decode as video.
   - Look-dev must validate as image/video media.
   - Empty/truncated/replaced evidence invalidates the approval.

## Regression coverage

New adversarial tests cover:
- missing authoritative final-screening evidence;
- workflow-required review with nested `required=false`;
- native bootstrap rejected for final binding;
- active bridge profile drift at render dispatch;
- invalid studio review followed by corrected review in the same iteration;
- approved previs replaced after plan compilation.

## Validation

- Complete pytest suite after final audit repairs and adjacent cinematic-lane consistency fix: **186 passed**.
- Test collection before the adjacent lane regression was added: **185 tests collected**; final suite contains **186** passing tests.
- Initial live bridge-binding smoke passed with evaluated core-production evidence. Astra's follow-up correctly found that dispatch could still reuse a stale bootstrap file; workflow 2026.09.28.12 replaces that liveness claim with direct runtime readiness queries.
- The live smoke also exposed and fixed an adjacent stale schema mismatch: production manifests now accept the canonical `cinematic` lane used by workflow bootstrap.
- Production v2 template validation: **PASS**.
- Markdown local-link audit: **0 broken links**.
- Python compilation of changed core/controller modules: **PASS**.
- `git diff --check`: **clean**.

Canonical workflow version: **2026.09.28.10**.

## Follow-up review closure — workflow 2026.09.28.12

Astra independently re-reviewed commit `6b4b11c` and identified four remaining issues. This section supersedes the earlier claim that all original gaps were fully closed:

1. **Dispatch liveness** — `workflowctl bind` now queries the running bridge readiness endpoint and records runtime identity (bridge version/profile/tool-set hash/source commit). `productionctl render-spec` and `productionctl rendering` query the running endpoint again. Reusing an old bootstrap JSON cannot mask current bridge/profile drift.
2. **CI dependencies** — `requirements-test.txt` explicitly declares `numpy`, `pillow`, and `pytest`; media-runtime CI installs that file and changes to it trigger the workflow.
3. **Development-artifact path base** — relative previs/look-dev/proof paths are resolved against the bound director-brief directory at both compilation and preflight. Relocating the execution-plan JSON no longer changes evidence resolution.
4. **RIDGELINE identity** — the actual current master hashes to `348de54393756c5d7e28b9c9fb64383242e56fa76ea336cc92203de34ea99e56`. The `846454e8...` paragraph is explicitly historical/superseded.

GitHub-hosted CI success must not be claimed while Actions execution is blocked by the separate account billing/spending-limit condition. Local test results and live runtime smokes are reported separately.
Current canonical workflow after follow-up: **2026.09.28.12**.

### Follow-up validation evidence

- Full local pytest suite: **187/187 passed** in 77.24 s.
- Test collection: **187 tests collected**.
- Production-v2 template validation: **PASS**.
- Markdown local-link audit: **30 files, 0 broken local links**.
- RIDGELINE current master SHA-256 verified directly: `348de54393756c5d7e28b9c9fb64383242e56fa76ea336cc92203de34ea99e56`.
- Post-commit live bind → `render-spec` smoke: **PASS** using the running bridge directly, with no `--bootstrap-result` supplied to render dispatch.
- Adversarial dispatch smoke against a live readiness endpoint reporting profile `core` instead of bound `core-production`: **blocked**, reporting both profile drift and tool-set hash drift.
- Local Git state after push: clean and synchronized with `origin/main`.
- GitHub combined commit status currently exposes no completed status contexts; do not claim a GitHub-hosted CI pass from that absence.
