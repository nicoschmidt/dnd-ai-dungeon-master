import type { Character, Encounter } from '../contract/index.ts'
import { actingCharacterId } from '../stream/tableState.ts'

interface Props {
  party: Character[]
  encounter: Encounter | null
}

// The state pane: the encounter and the party as the backend holds them.
// Rendered from `party_updated` and `encounter_updated` and from nothing else:
// a number here came through a tool, never out of the narration (ADR-0005,
// commitment 2).
export function StatusPanel({ party, encounter }: Props) {
  const acting = actingCharacterId(encounter)

  return (
    <aside className="state-pane" aria-label="State">
      {encounter && <EncounterState encounter={encounter} />}
      {party.length === 0 ? (
        <p>No characters yet.</p>
      ) : (
        <ul className="cards" aria-label="Characters">
          {party.map((character) => (
            <CharacterCard
              key={character.id}
              character={character}
              acting={character.id === acting}
            />
          ))}
        </ul>
      )}
    </aside>
  )
}

// The opponent appears by name only: its numbers are hidden information and
// are not in `encounter_updated` at all.
function EncounterState({ encounter }: { encounter: Encounter }) {
  const current = encounter.outcome ? null : encounter.current_turn

  return (
    <section className="encounter" aria-label="Encounter">
      <h2>{encounter.opponent_name}</h2>
      <p className="round">
        {encounter.outcome
          ? 'The encounter has ended.'
          : encounter.round === 0
            ? 'Rolling initiative'
            : `Round ${encounter.round}`}
      </p>
      {encounter.turn_order.length > 0 && (
        <ol className="turn-order" aria-label="Turn order">
          {encounter.turn_order.map((combatant, index) => (
            <li
              key={`${combatant.kind}:${combatant.id}`}
              className={combatant.kind}
              aria-current={index === current ? 'true' : undefined}
            >
              {combatant.name}
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

function CharacterCard({ character, acting }: { character: Character; acting: boolean }) {
  const down = character.current_hit_points === 0
  const share =
    character.max_hit_points > 0
      ? Math.min(1, character.current_hit_points / character.max_hit_points)
      : 0

  return (
    <li className={down ? 'card down' : 'card'} aria-current={acting ? 'true' : undefined}>
      <div className="heading">
        <strong className="name">{character.name}</strong>
        <span className="armour-class">AC {character.armour_class}</span>
      </div>
      <span className="class">
        {character.character_class} {character.level}
      </span>
      <div className="hit-points">
        <span>
          {character.current_hit_points} / {character.max_hit_points} HP
        </span>
        {character.temporary_hit_points > 0 && (
          <span className="temporary">+{character.temporary_hit_points} temporary</span>
        )}
      </div>
      {/* The numbers above say the same; the bar is for reading across the table. */}
      <div className="bar" aria-hidden="true">
        <div style={{ width: `${share * 100}%` }} />
      </div>
      {character.conditions.length > 0 && (
        <p className="conditions" aria-label="Conditions">
          {character.conditions.map((condition) => (
            <span key={condition}>{condition}</span>
          ))}
        </p>
      )}
    </li>
  )
}
