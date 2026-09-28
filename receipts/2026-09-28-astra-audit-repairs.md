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
   - `productionctl render-spec` and `productionctl rendering` require a current bootstrap result and fail if the active bridge/profile changed.

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
- Live Local Workspace bridge-binding smoke: evaluated core-production bridge evidence bound successfully and `productionctl render-spec --bootstrap-result` passed.
- The live smoke also exposed and fixed an adjacent stale schema mismatch: production manifests now accept the canonical `cinematic` lane used by workflow bootstrap.
- Production v2 template validation: **PASS**.
- Markdown local-link audit: **0 broken links**.
- Python compilation of changed core/controller modules: **PASS**.
- `git diff --check`: **clean**.

Canonical workflow version: **2026.09.28.10**.