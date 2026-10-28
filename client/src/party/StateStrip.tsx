import type { Character, Encounter } from '../contract/index.ts'
import { useStrings } from '../language/strings.ts'
import { actingCharacterId, currentCombatant } from '../stream/tableState.ts'
import { hitPointSummary, roundLabel } from './presentation.ts'

interface Props {
  party: Character[]
  encounter: Encounter | null
}

// The state pane's place on narrow screens: above the narration, so the state
// stays in view on a tablet held upright. Whose turn and the round on one
// line, then one chip per character with their hit points, scrolling
// sideways. Rendered from the same state as the pane, and from nothing else.
export function StateStrip({ party, encounter }: Props) {
  const t = useStrings()
  const acting = actingCharacterId(encounter)
  const current = currentCombatant(encounter)

  return (
    <section className="state-strip" aria-label={t.state.label}>
      {encounter && (
        <p className="summary">
          {current && <strong>{current.name} {t.state.onTurn} · </strong>}
          {roundLabel(encounter, t)}
        </p>
      )}
      {party.length > 0 && (
        <ul aria-label={t.state.characters}>
          {party.map((character) => (
            <li
              key={character.id}
              className={character.current_hit_points === 0 ? 'down' : undefined}
              aria-current={character.id === acting ? 'true' : undefined}
              title={hitPointSummary(character, t)}
            >
              <span>{character.name}</span>
              <span>
                {character.current_hit_points}/{character.max_hit_points}
                {character.temporary_hit_points > 0 && (
                  <span className="temporary"> +{character.temporary_hit_points}</span>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
