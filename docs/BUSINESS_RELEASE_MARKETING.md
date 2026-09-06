# Business / OSS Release Marketing

## Purpose

Create polished marketing videos for public projects that are actually intended for users and tied to an exact released version.

## Source-of-truth contract

When a target belongs to the OSS Shipping System portfolio, resolve marketing eligibility from that repository's `state/public-products.json` and verify the actual project/release before production.

The video repository should keep a **production snapshot**, not a competing mutable release registry.

Minimum snapshot fields:

```json
{
  "project": "owner/repo",
  "release": "vX.Y.Z",
  "previous_release": "vX.Y.Z",
  "exact_tag": "vX.Y.Z",
  "exact_commit": "sha",
  "package": null,
  "live_url": null,
  "source_verified_at": "ISO-8601",
  "production_type": "release-marketing"
}
```

## Eligibility gate

A repository is not automatically marketable because it is public.

Before producing release marketing, confirm:

- deliberate user-facing/public-product classification;
- coherent license/public scope when applicable;
- canonical release exists;
- release was validated by its own project process;
- public package/download/live URL claims are current;
- meaningful user value exists;
- known limitations are not hidden by the video.

## Release video structure

A strong default structure:

1. **Hook (0–2s)** — useful outcome/problem.
2. **Identity + version** — project name and exact version.
3. **What it does** — concrete capability, preferably demonstrated.
4. **Why it matters** — user value.
5. **What's new** — for update releases, changes from previous canonical release.
6. **Proof/demo** — UI/tool/terminal/data/real behavior as appropriate.
7. **Limit/expectation** — only when material to truthful use.
8. **CTA** — repo/package/live URL.

## Version display rule

The exact version should appear visibly near the opening identity and may appear again on the end card.

Example:

`Hermes Commerce Control — v0.1.2`

Do not use a generic evergreen promo to describe release-specific behavior without a version marker.

## New release workflow

For each new canonical release:

**verify release → snapshot current/prior versions → inspect changelog/diff/user-facing behavior → choose strongest story → script → scene plan → render variants → QA → publish**

Store production under:

`productions/business/<repo>/<release>/`

Do not rewrite the old release package when a new version ships; preserve it as historical marketing evidence.

## Recommended production package

```text
<release>/
├── production.json
├── brief.md
├── source-snapshot.json
├── script.md
├── scene-plan.json
├── assets/
├── renders/scenes/
├── qa/
└── final/
```

## Platforms

Produce aspect-ratio/platform variants from the same verified message when useful:

- 9:16 — Shorts/Reels/TikTok;
- 16:9 — YouTube/product demo;
- 1:1 — optional social creative.

Do not change factual release claims between variants.
