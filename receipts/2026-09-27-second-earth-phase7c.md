# Phase 7C — SECOND EARTH final QA and repair receipt

Date: 2026-09-27

## Final result

SECOND EARTH is ready for Angel's final review.

Final candidate:

- SHA-256: `f23a08583afd141b906cad486c088fb9ad355ecc3617939a28d7e78f4abf6d59`
- duration: 150.000 seconds
- video: H.264 / 1280×720 / 24 fps / yuv420p
- audio: AAC / 48 kHz / stereo
- size: 17,812,996 bytes
- full decode: PASS

Production controller state:

- status: `USER_REVIEW`
- technical gate: PASS
- assistant gate: PASS
- user gate: PENDING
- ready_for_user_review: true
- repair cycle: 1
- remaining autonomous repair budget: 3

## Why iteration 00 was rejected

Iteration 00 passed deterministic technical QA, but candidate-bound creative QA and manual assistant evidence review found that it was not strong enough to hand to Angel.

Concrete failures:

1. shot 03's civilization was too small at phone scale;
2. probe-world shots 10/11/20 looked like placeholder blocks/rings instead of the intended spacecraft world;
3. shot 13 clipped `WE CAN SEE YOU`;
4. shot 13 → shot 14 repeated push-family camera grammar;
5. shot 21 was effectively static and triggered weak-motion QA.

The production controller recorded assistant FAIL and opened repair cycle 1 rather than bypassing the gate.

## Repair cycle 1

Changes:

- enlarged the hand-drawn city and made early expansion readable;
- rebuilt the probe lane around the verified Quaternius spacecraft;
- switched the repaired probe lane to Eevee with authored cyan/gold lighting;
- strengthened launch-bay, planetary and boundary-station scale;
- fixed second-message typography and composition;
- made shot 14 a locked analytic view with lateral data-map traversal;
- carried shot-20 spatial motion into shot 21 beneath the thesis;
- updated declared layout geometry to match the actual rendered typography.

## Final QA

Technical evidence:

- integrated loudness: -17.18 LUFS
- true peak: -2.02 dBFS
- unintended silence: 0.0 seconds
- decode errors: none

Creative evidence:

- freeze spans: 0
- weak-motion shots: 0
- consecutive camera-family repeats: 0
- layout violations: 0
- warning count: 0
- candidate-bound evidence items: 43
- assistant creative review criteria: 5/5 PASS

The final assistant review explicitly inspected composition, phone-scale readability, visible motion, camera variety, and normal-speed story read.

## Delivery

Local review page:

`http://127.0.0.1:8880/`

Direct MP4:

`http://127.0.0.1:8880/final/second-earth.mp4`

The review server was verified reachable with HTTP 200 and the final MP4 passed an independent decode acceptance check.

No online video-generation model was used.
