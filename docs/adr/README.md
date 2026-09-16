# Architecture Decision Records

Each file records one architecturally significant decision: its context, the
options considered, the choice made, and the consequences accepted with it.

## Rules

- ADRs are numbered sequentially and never renumbered.
- An accepted ADR is immutable. To change a decision, write a new ADR and
  mark the old one `superseded by ADR-XXXX`.
- Statuses: `proposed`, `accepted`, `rejected`, `superseded by ADR-XXXX`.
- Write the ADR before the code that implements the decision.
- Copy `0000-template.md` to start a new one.

## Index

| # | Title | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | accepted |
| [0002](0002-application-form-factor.md) | Application form factor | accepted |
| [0003](0003-adventure-content-separation.md) | Adventure content separation | accepted |
| [0004](0004-character-state-ownership.md) | Character state ownership | proposed |
