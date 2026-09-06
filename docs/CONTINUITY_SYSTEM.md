# Continuity System

## Why this exists

Chat context is useful while a session is active, but I do not want a show's canon to depend on whether a future session happens to remember the same details.

This system keeps accepted story facts, character state, props, locations, visual state, and unresolved threads explicit so later episodes can continue from what was actually accepted.

## Authority order

For an active show, use this order when sources disagree:

1. user-approved canon decisions;
2. accepted episode `continuity-out.json` files;
3. current season continuity summary;
4. show bible, world, and character rules;
5. planned but unrendered episode notes;
6. old chat context.

The important distinction is that an accepted episode is stronger evidence than an old planning idea. Once something has been established in the final accepted cut, later sessions should not casually revert to a stale note that came before it.

## Continuity-in

Before producing an episode, resolve the state that the episode inherits:

- character locations and status;
- relationships and what each character knows;
- injuries, changes, and abilities;
- inventory and held objects;
- location/set damage;
- unresolved promises or mysteries;
- running jokes and recurring rules;
- setup/payoff obligations.

The episode plan should start from this state rather than reconstructing it from memory.

## Continuity-out

After an episode passes both assistant and user review, record the facts established by the accepted final cut.

Example:

```json
{
  "episode": "S01E01",
  "characters": {
    "Milo": ["learned the portal warning rule", "kept the damaged scanner"],
    "Vex": ["knows why the creature appeared but has not told Milo"]
  },
  "world": ["east portal frame is damaged"],
  "unresolved": ["scanner origin", "creature purpose"]
}
```

Do not write planned events into `continuity-out` merely because they existed in the script. Record what the accepted episode actually established.

## Retcons and reveals

A later episode can intentionally change how an earlier event is understood. That can be good storytelling when the script treats it as a reveal or deliberate retcon.

What I do not want is accidental model drift being mistaken for a creative decision.

If prior understanding changes intentionally, make the change explicit and update continuity accordingly.

## Visual continuity

Continuity is not only story text. Track recurring visual state that affects rendering:

- character model or rig version;
- clothing;
- height and proportion relationships;
- signature colors;
- persistent props;
- set layout and anchor definitions;
- portal/object dimensions;
- damage and other state changes.

Whenever possible, a new render should import these values directly instead of approximating them from screenshots or old chat descriptions.

The goal is simple: accepted canon should be portable across sessions and production turns.