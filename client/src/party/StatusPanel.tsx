import type { Character, Encounter } from '../contract/index.ts'
import { actingCharacterId } from '../stream/tableState.ts'

interface Props {
  party: Character[]
  encounter: Encounter | null
}

// The party as the backend holds it. Rendered from `party_updated` and
// `encounter_updated` and from nothing else: a number here came through a
// tool, never out of the narration (ADR-0005, commitment 2).
export function StatusPanel({ party, encounter }: Props) {
  const acting = actingCharacterId(encounter)
  const current =
    encounter && encounter.current_turn !== null
      ? encounter.turn_order[encounter.current_turn]
      : undefined

  return (
    <section className="status" aria-label="Party">
      {encounter && (
        <p className="turn">
          {encounter.outcome
            ? `The encounter against ${encounter.opponent_name} has ended.`
            : encounter.round === 0
              ? `${encounter.opponent_name}: rolling initiative`
              : `Round ${encounter.round}${current ? ` — ${current.name}'s turn` : ''}`}
        </p>
      )}
      {party.length === 0 ? (
        <p>No characters yet.</p>
      ) : (
        <ul>
          {party.map((character) => (
            <li
              key={character.id}
              className={character.id === acting ? 'acting' : undefined}
              aria-current={character.id === acting ? 'true' : undefined}
            >
              <strong>{character.name}</strong>{' '}
              <span className="class">
                {character.character_class} {character.level}
              </span>{' '}
              <span className="hit-points">
                {character.current_hit_points} / {character.max_hit_points} HP
              </span>
              {character.temporary_hit_points > 0 && (
                <span className="temporary"> +{character.temporary_hit_points} temporary</span>
              )}
              {character.conditions.length > 0 && (
                <span className="conditions"> {character.conditions.join(', ')}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
