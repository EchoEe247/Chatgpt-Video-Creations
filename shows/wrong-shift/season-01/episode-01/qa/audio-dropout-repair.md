# S01E01 audio dropout repair

## Trigger
User review reported sound switching on/off from roughly the three-minute point onward in the Episode 1 candidate master.

## Diagnosis
The original master audio mixed the full-duration bed and 123 delayed dialogue inputs through one large `amix` graph. The bed source itself remained continuous for the full 480 seconds, but the resulting master contained repeated exact digital-zero gaps beginning around 178 seconds whenever dialogue was absent.

Measured on the original PCM master:
- 196 one-second windows of exact digital silence in total;
- 194 of those windows occurred at or after 180 seconds;
- the issue therefore matched the user's report and was not intentional sound design.

## Repair
Rebuilt the audio architecture as two stable buses:
1. a speech-only bus containing all 123 character lines with the existing Rae/Owen/Hale voice identities and character-specific processing;
2. the existing continuous 480-second environmental/music/anomaly bed;
3. light speech-driven ducking on the bed;
4. a two-input final mix followed by loudness normalization.

The approved video stream was preserved; only the audio was replaced.

## Repaired candidate
- file: `wrong_shift_s01e01_floor_minus_zero_audio_fixed.mp4`
- duration: 480.000 seconds
- video: 1280x720 H.264/yuv420p at 24 fps, copied from the approved candidate visual stream
- audio: AAC stereo, 48 kHz
- SHA-256: `d9a49d5fb1dcdd00565ed60cb2536d375baa5a0ed00efae3ded8cf5cc50329c2`
- integrated loudness: approximately -16.8 LUFS
- true peak: approximately -1.4 dBFS

## Full-timeline audio QA
- unintended exact one-second digital-silence windows: 0
- unintended exact one-second digital-silence windows at/after 3:00: 0
- quietest one-second window at/after 3:00: approximately -29.4 dBFS RMS, confirming that the continuous bed remains present between dialogue lines
- duration: exactly 480.000 seconds

## Gate
Assistant audio/technical re-review: PASS.
User review remains required before Episode 1 can become DONE/canon.
