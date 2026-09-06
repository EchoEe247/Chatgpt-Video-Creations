# Business / OSS Release Marketing

## Purpose

For this lane, I want marketing that is useful because it is grounded in a real public project and an exact release. I do not want generic software promotion where the video says something impressive but the viewer cannot tell which version, feature set, or current project state it actually refers to.

The release itself is part of the story.

## Source of truth

When a target belongs to the OSS Shipping System portfolio, resolve marketing eligibility from that repository's `state/public-products.json`, then verify the actual project and release before production.

`Chatgpt-Video-Creations` should keep a **production snapshot** of the facts used for the video. It should not become a second mutable release registry competing with the project or OSS Shipping System.

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

This snapshot matters because the video may remain public after the project changes. We should always be able to reconstruct what release facts the marketing was based on.

## Release version is not a validated baseline

A product release such as `v0.1.2` identifies the version being marketed.

A B-series validated baseline such as `B1` identifies an internal known-good production state for this video repository.

They can point to the same production evidence, but they answer different questions. Do not substitute one identifier for the other.

Formal baseline rules live in `baselines/README.md`.

## Eligibility gate

Public does not automatically mean marketable.

Before producing release marketing, confirm that:

- the repository is deliberately classified as a user-facing/public product;
- licensing and public scope are coherent when applicable;
- a canonical release actually exists;
- that release passed the project's own validation process;
- package, download, or live-URL claims are still current;
- there is meaningful user value worth communicating;
- known limitations are not being hidden to make the video look stronger.

If those conditions are not there yet, fix the product/release state first rather than manufacture marketing around it.

## What a release video should communicate

A strong default sequence is:

1. **Hook (0–2s)** — the useful outcome or problem.
2. **Identity + version** — project name and exact release.
3. **What it does** — concrete capability, preferably shown rather than only claimed.
4. **Why it matters** — practical user value.
5. **What's new** — when this is an update release, explain the meaningful changes from the previous canonical release.
6. **Proof/demo** — UI, terminal, data, workflow, or other real behavior where appropriate.
7. **Limit/expectation** — include this when it materially affects truthful use.
8. **CTA** — repository, package, or live URL.

This is a default structure, not a requirement to force every video into identical pacing. The facts stay fixed; the creative presentation can change.

## Version display

The exact release should appear visibly near the opening identity and can appear again on the end card.

Example:

`Hermes Commerce Control — v0.1.2`

This matters because an evergreen-looking video can become misleading when it demonstrates release-specific behavior without telling the viewer which release they are looking at.

## New release workflow

When a new canonical release is worth promoting:

**verify release → snapshot current/prior versions → inspect changelog/diff/user-facing behavior → choose the strongest story → script → scene plan → render variants → QA → publish**

Store the production under:

`productions/business/<repo>/<release>/`

Do not overwrite the old release package when a new version ships. The old package is historical marketing evidence for what we were showing at that time.

If the production process itself establishes a reusable known-good state worth preserving, promote that separately through the B-series baseline process after the required validation passes.

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

## Platform variants

When useful, produce different aspect-ratio/platform outputs from the same verified release message:

- 9:16 — Shorts, Reels, TikTok;
- 16:9 — YouTube or product demo;
- 1:1 — optional social creative.

The presentation can change between platforms. The release facts cannot.
