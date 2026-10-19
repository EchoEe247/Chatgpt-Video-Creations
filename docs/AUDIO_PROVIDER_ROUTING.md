# Audio-provider routing — current preferences

This is the provider policy for **Chatgpt-Video-Creations**, not the separate
`create-animated-videos` installable skill. Retain the established
`src/core/av_timeline.py` as the single audiovisual clock.

## Narration: Deepgram first

When a film **actually needs** spoken narration, the current preference is
the user's **existing Deepgram API**, using available authorized credits, a
consistent selected voice, proper pauses, and measured real clip duration.

- Only use Deepgram when the **active production runtime** has authorized
  credential access and network/API transport. A key stored on another machine,
  phone app or unrelated connector does not establish accessibility.
- Keep `DEEPGRAM_API_KEY` in a secure runtime environment. Never commit
  it, log it, or echo it into a file or chat.
- Preserve voice/model/settings and actual clip timings in production-specific
  receipts; generate captions and speech windows from measured audio.
- On unavailable API access, failed authentication, or exhausted credits,
  **report the blocker and preserve the independent visual work**. Do **not**
  silently replace Deepgram with low-quality phone/system TTS. Local neural
  narration is a *future user-approved alternative*, not today's default.
- A particular offline/no-network job remains offline; do not override
  user-specific restrictions based on the default preference.

The provider routing policy is **not proof of an implemented authenticated
Deepgram transport** in this repository. Verify with a bounded real narration
audition before claiming that actual synthesis succeeded. If the user wants
only music/SFX, omit narration rather than adding unnecessary voiceover.

## Motion sound effects: optional native Earshot v0.3

The existing six-sound Audio Commons remain a free procedural baseline.
For appropriate kinetic typography, whooshes, designed impacts, UI clicks,
pops, risers and stings, the new optional adapter
`src/core/native_earshot.py` calls the real `earshot.forge.bank.render`
instead of imitating it with custom DSP.

It can create a 48 kHz stereo **effects-only** WAV stem synchronized to
an existing compiled A/V timeline event by exact sample index:

```json
[
  {
    "event_id": "hero.reveal-impact",
    "sound_id": "whoosh_fast/crisp",
    "align": "peak",
    "gain_db": -15,
    "seed": 17
  }
]
```

The referenced event must exist in the compiled timeline and target `audio`.
The effect can align to the sound's measured `start`, `onset`, `peak`
or `end` landmark. The adapter caches repeated native takes and
records actual bank identity, cue parameters, pre-roll/truncation and
sample position. It refuses missing native Earshot dependencies rather than
substituting generic synthesized audio.

```sh
python scripts/earshotctl.py \
  --timeline work/film/av-timeline.json \
  --cues work/film/earshot-cues.json \
  --out work/film/effects-earshot.wav \
  --report work/film/earshot-receipt.json
```

Earshot's procedural sound bank is CPU-based. Its separate AI audio-analysis
components are **not** implied to be installed. Termux-local installation
does not guarantee availability in a different ChatGPT production VM.

## Mix and delivery

Keep the existing composed score, sourced Foley, ambience and original
Audio Commons; select effects by sonic appropriateness rather than forcing
Earshot onto every cue. The stem is **unmastered**. Mix alongside speech
(when necessary), preserve ducking/headroom, run the existing `audioctl qa`,
`videoctl qa`, decoded A/V checks, and genuine listening when capability
is available. Reference soundtrack copying requires appropriate usage rights.

Neither loudness metadata nor passing a sound-bank check proves excellent
sound design or perfect audio-picture sync. Deepgram and Earshot are
different roles and are never interchangeable.

## Implementation status

- Native Earshot effect-stem adapter: implemented with focused tests;
  use in a full film still needs actual runtime and listening validation.
- Deepgram-first narration preference: documented; authenticated API
  invocation is conditional on runtime access and remains separately
  verified before use. No credentials were modified.
- Automatic switching to local TTS: intentionally **not enabled**.

Test with `python -m pytest -q tests/test_native_earshot.py`.
