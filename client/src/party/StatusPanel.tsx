import type { Character, Encounter } from '../contract/index.ts'
import { useStrings } from '../language/strings.ts'
import { actingCharacterId, currentCombatant } from '../stream/tableState.ts'
import { Avatar } from './Avatar.tsx'
import { hitPointBar, hitPointSummary, roundLabel } from './presentation.ts'

interface Props {
  party: Character[]
  encounter: Encounter | null
}

// The state pane: the fight and the party as the backend holds them. Rendered
// from `party_updated` and `encounter_updated` and from nothing else: a number
// here came through a tool, never out of the narration (ADR-0005,
// commitment 2).
export function StatusPanel({ party, encounter }: Props) {
  const t = useStrings()
  const acting = actingCharacterId(encounter)

  return (
    <aside className="state-pane" aria-label={t.state.label}>
      {encounter && <Fight encounter={encounter} />}
      <section aria-labelledby="party-heading">
        <h2 id="party-heading" className="eyebrow">
          {t.state.party}
        </h2>
        {party.length === 0 ? (
          <p>{t.state.noCharacters}</p>
        ) : (
          <ul className="cards" aria-label={t.state.characters}>
            {party.map((character) => (
              <CharacterCard
                key={character.id}
                character={character}
                party={party}
                acting={character.id === acting}
              />
            ))}
          </ul>
        )}
      </section>
    </aside>
  )
}

// The opponent appears by name only: its numbers are hidden information and
// are not in `encounter_updated` at all.
function Fight({ encounter }: { encounter: Encounter }) {
  const t = useStrings()
  const current = currentCombatant(encounter)

  return (
    <section aria-labelledby="fight-heading">
      <div className="head">
        <h2 id="fight-heading" className="eyebrow">
          {t.state.fight}
        </h2>
        <span>{roundLabel(encounter, t)}</span>
      </div>
      {encounter.turn_order.length > 0 && (
        <ol className="turn-order" aria-label={t.state.turnOrder}>
          {encounter.turn_order.map((combatant, index) => (
            <li
              key={`${combatant.kind}:${combatant.id}`}
              aria-current={combatant === current ? 'step' : undefined}
            >
              <span className="position" aria-hidden="true">
                {index + 1}
              </span>
              <span className="name">{combatant.name}</span>
              {combatant === current ? (
                <span className="tag">{t.state.onTurn}</span>
              ) : (
                combatant.kind === 'opponent' && (
                  <span className="opponent">{t.state.opponent}</span>
                )
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

interface CardProps {
  character: Character
  party: Character[]
  acting: boolean
}

function CharacterCard({ character, party, acting }: CardProps) {
  const t = useStrings()
  const down = character.current_hit_points === 0
  const bar = hitPointBar(character)
  const percent = (share: number) => `${share * 100}%`

  return (
    <li className={down ? 'card down' : 'card'} aria-current={acting ? 'true' : undefined}>
      <div className="top">
        <Avatar character={character} party={party} />
        <div className="who">
          <div className="line">
            <span className="name">{character.name}</span>
            {acting && <span className="badge">{t.state.onTurn}</span>}
          </div>
          <div className="class">
            {character.character_class} · {t.state.level(character.level)}
          </div>
        </div>
        <div className="armour-class" title={t.state.armourClass}>
          <small>{t.state.armourClassShort}</small>
          <b>{character.armour_class}</b>
        </div>
      </div>
      <div className="hit-points">
        <div className="numbers">
          <span>{t.state.hitPoints}</span>
          <span>
            <strong>{character.current_hit_points}</strong>
            <span className="max"> / {character.max_hit_points}</span>
            {character.temporary_hit_points > 0 && (
              <span className="temporary"> {t.state.temporary(character.temporary_hit_points)}</span>
            )}
          </span>
        </div>
        <div
          className={bar.low ? 'bar low' : 'bar'}
          role="img"
          aria-label={hitPointSummary(character, t)}
        >
          <div className="current" style={{ width: percent(bar.current) }} />
          <div className="temporary-segment" style={{ width: percent(bar.temporary) }} />
        </div>
      </div>
      {character.conditions.length > 0 && (
        <p className="conditions" aria-label={t.state.conditions}>
          {character.conditions.map((condition) => (
            <span key={condition}>{t.conditions[condition]}</span>
          ))}
        </p>
      )}
    </li>
  )
}
