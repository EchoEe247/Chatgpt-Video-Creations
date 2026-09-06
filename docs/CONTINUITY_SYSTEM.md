# Continuity System

## Purpose

Prevent later episodes or fresh ChatGPT sessions from contradicting accepted story facts, character states, props, locations or unresolved threads.

## Authority

For an active show, authority order is:

1. user-approved canon decisions;
2. accepted episode `continuity-out.json` files;
3. current season continuity summary;
4. show bible/world/character rules;
5. planned but unrendered episode notes;
6. old chat context.

Accepted episode facts outrank stale planning notes.

## Continuity-in

Before producing an episode, resolve:

- character locations/status;
- relationships and knowledge;
- injuries/changes/abilities;
- inventory/held objects;
- location/set damage;
- unresolved promises/mysteries;
- running jokes/rules;
- setup/payoff obligations.

## Continuity-out

After an episode passes both reviews, record only facts established by the accepted final cut.

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

## Retcon rule

A later episode may intentionally revise prior understanding only when the script treats it as a reveal/retcon and continuity is updated explicitly. Do not let accidental model drift masquerade as storytelling.

## Visual continuity

Track recurring visual facts that affect rendering:

- character model/rig version;
- clothing;
- height/proportion relationships;
- signature colors;
- persistent props;
- set layout and anchor definitions;
- portal/object dimensions;
- damage/state changes.

A new render should import these values rather than approximate them from screenshots whenever possible.
