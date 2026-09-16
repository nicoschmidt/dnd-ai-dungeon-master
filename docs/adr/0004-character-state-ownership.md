# ADR-0004: Character state ownership

- **Status:** proposed
- **Date:** 2026-09-16
- **Deciders:** Nico Schmidt
- **Supersedes:** —
- **Superseded by:** —

## Context

The players sit at a table with pen, paper and dice. Each of them has a
character sheet. The question is whether the application holds character
data too, and if so, how much.

This is not a user-interface question. It determines what the deterministic
rules core (ADR-0002) is able to compute, and therefore what can be moved
out of the model's judgement into code at all.

One observation narrows the question sharply: **the players roll their own
dice and add their own modifiers.** When a player says "18 auf den Angriff,
7 Schaden", the system never needs that character's attack bonus or damage
dice — it needs only the reported result. So the system does not need a
character model in order to adjudicate what players do. It needs character
data only for the things it computes *against* a character:

- Does the ogre's attack hit? → needs armour class.
- How badly is the fighter hurt? → needs current and maximum hit points.
- Is the wizard still concentrating, prone, poisoned? → needs conditions.

That is a much smaller set than a full 5e character model.

## Decision drivers

- Deterministic combat (ADR-0002) requires armour class and hit points to be
  available to code. Without them, combat cannot leave the model's judgement.
- A party status panel is wanted early, ideally in the first iteration. It is
  a view over character state; without such state there is nothing to show.
- Modelling 5e characters fully is a project in itself and would consume the
  first several iterations without producing play.
- Paper sheets carry real value: they belong to the player, they work
  offline, they need no onboarding, and crossing off hit points is part of
  the experience.
- Any value stored in two places will drift. Dual bookkeeping is the failure
  mode to design against.

## Options considered

### Option A: Paper only — the system holds no character data

- Good: zero implementation cost; players bring characters from anywhere.
- Good: the character stays wholly the player's.
- Bad: the system must ask for armour class on every single monster attack.
  A value needed several times per round cannot live on paper.
- Bad: deterministic combat becomes impossible, which contradicts ADR-0002.
- Bad: no party status panel, and no accurate state to resume a session with.

### Option B: Digital only — the system holds a full character model

- Good: everything is computable and checkable; the agent can catch mistakes.
- Bad: requires character creation or import before the first session can be
  played at all, which blocks iteration 1.
- Bad: the 5e model is large — classes, subclasses, spells, feats, items,
  resistances. Every gap becomes a defect discovered mid-session.
- Bad: removes the paper sheet's charm without a proportionate gain, since
  most of the model is never used by the system (see Context).

### Option C: Split by who needs the value, and how often

The system owns only what it computes against; everything else stays on
paper. Each value lives in exactly one place.

System owns: name, class and level (for narration), armour class, maximum
and current hit points, temporary hit points, active conditions, and — once
relevant — position on the map.

Paper keeps: ability scores and all modifiers, skills, proficiencies,
attacks, spells known and prepared, inventory, gold, background, notes.

The discriminating question for any future field: *how often does the system
need this value, and can a player answer it in one second?* Needed several
times per round and arithmetic in nature → the system owns it. Needed
occasionally and answerable by a glance at the sheet → paper keeps it.

- Good: roughly ten fields per character; enterable in minutes, implementable
  in one iteration.
- Good: unlocks deterministic combat and the status panel immediately.
- Good: the paper sheet keeps everything that is about the character rather
  than about combat arithmetic.
- Bad: hit points move off paper. This is the one habit players give up, and
  it is the part of the sheet they are most attached to.
- Bad: the boundary needs maintaining as features arrive; spell slots and
  inventory will both make a case for crossing it.

## Decision

_Open. Option C is the recommendation._

## Open questions

1. Are spell slots and other limited resources inside or outside the
   boundary? They are needed only when the player acts, so by the rule above
   they stay on paper — but consistency checking is the strongest argument
   for pulling them in.
2. How does character data get in? Typed into the client once per campaign,
   or photographed and read via the same ingest pipeline the adventure needs?
3. Does the status panel show exact hit points, or a coarse state (healthy /
   bloodied / down)? Exact numbers are more useful; coarse states preserve
   some of the tension.
4. Are monster hit points shown to the game master's view only, or not at all
   — is there even a game master's view at a table where everyone is a player?

## Consequences

_To be written with the decision._
