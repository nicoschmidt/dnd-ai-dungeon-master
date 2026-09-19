# ADR-0004: Character state ownership

- **Status:** accepted
- **Date:** 2026-09-19
- **Deciders:** Maintainer
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

We choose **Option C**. The system owns the values it computes *against* a
character; the paper sheet keeps everything else. Every value lives in
exactly one place.

The system owns, per character: name, class and level — for narration —
armour class, maximum hit points, current hit points, temporary hit points,
active conditions, and, once a map exists, position.

The paper sheet keeps everything else: ability scores and modifiers, skills,
proficiencies, attacks, spells known and prepared, spell slots and other
limited resources, inventory, gold, background and notes.

What is decided here is not that list. It is the rule that produced it, and
that decides every field considered later:

> How often does the system need this value, and can a player answer it in
> one second? Needed several times per round and arithmetic in nature — the
> system owns it. Needed occasionally and answerable by a glance at the
> sheet — paper keeps it.

The boundary is expected to move. Spells, inventory and limited resources all
have plausible cases for crossing it in a later iteration. A crossing is a new
ADR argued against the rule above, not a quiet addition. What this record
fixes is the rule and the starting position, not a permanent list of fields.

Four applications of the rule settle the questions left open while this record
was proposed.

**Limited resources stay outside for now.** Spell slots, rage uses, bardic
inspiration, hit dice: the player needs them only when acting and reads them
off the sheet in a second, so the rule says paper. Consistency checking — the
system noticing a fourth third-level slot — is the one serious argument for
pulling them in, and today it is worth less than a per-class resource model
costs. It is carried as a backlog spike rather than as an open question here,
because a decision record is not a place to store a question.

**The status panel shows exact hit points.** 17 of 28, not "bloodied". A
coarse state hides nothing from the player whose character it is — they have
their own sheet — so it hides only from the rest of the table, and at a table
where everybody is a player there is nobody for whom that tension is designed.
Exact numbers are also what makes a miscalculation visible.

**Hit points move off paper, and syncing back is the player's business.** The
system's number is authoritative, and the screen is where it is read. Whether
a player also crosses it off on their sheet, and at which moment, is up to
them: nothing enforces that copy and no code ever reads it. This is the single
place where a value appears twice, and it is tolerated precisely because the
paper copy is a comfort rather than a source.

**Character data is typed in once per campaign.** Ten fields in a form in the
client — minutes per character, and no dependency on anything that does not
exist yet. Reading a photographed character sheet through the adventure ingest
pipeline is an obvious later convenience, and a backlog item rather than a
precondition for iteration 001.

## Consequences

What becomes easy:

- Deterministic combat becomes possible at all. Armour class and hit points
  are available to code, so a monster's attack against a character resolves in
  the rules core ([ADR-0002](0002-application-form-factor.md), commitment 2)
  instead of in the model's judgement.
- The party status panel is a view over state that already exists, not a
  subsystem of its own.
- A session can be resumed accurately, because the state that matters in the
  middle of a fight is the state the backend holds.
- Character setup is a form, not an import format. Iteration 001 waits for
  nothing.

What becomes hard, and what we accept:

- Crossing off hit points on paper stops being how damage is recorded. This is
  the habit players give up, and it is the part of the sheet they are most
  attached to.
- The boundary needs defending. Every later feature that wants one more field
  is a request to blur it; the rule above is the answer, and an ADR is the
  price of crossing.
- The system cannot check what it does not hold. A player who reports a wrong
  attack bonus, or forgets a spent spell slot, is not caught. That is
  deliberate: the alternative is the full 5e model, which is Option B.
- Class and level are held for narration only. Computing from them —
  proficiency bonus, spell slots by level — is the first step across the
  boundary and needs its own record.

What we are committed to:

- Party state is durable state, so it changes only through tools
  ([ADR-0002](0002-application-form-factor.md), commitment 3). Damage taken is
  a tool call, never a sentence the model writes.
- The client renders party state and nothing else about characters; what the
  backend does not send cannot appear on the shared screen.

Revisit this decision if: miscounted resources spoil play often enough to be
worth a per-class model — the signal that limited resources belong inside the
boundary — or if typing characters in turns out to be the friction that stops
a group from starting a campaign.

## Follow-up

- Backlog spike: are limited resources — spell slots, rage uses, bardic
  inspiration, hit dice — inside the boundary? Taken up when a feature makes
  the case, or when miscounting spoils play.
- Backlog feature: read a photographed character sheet through the ingest
  pipeline instead of typing the fields in.
- Not owned by this record: whether the shared screen also carries a view
  outside the fiction — monster hit points, the last roll the system made — so
  that a table with no human game master can check the AI's arithmetic. That
  is a question about monster and system state rather than character state,
  and belongs in a record of its own.
- Iteration 001 (#6) inherits the field list above as its party state model.
