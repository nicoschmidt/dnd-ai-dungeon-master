import type { Character } from '../contract/index.ts'
import { initials } from './presentation.ts'

// The number of avatar colours in index.css (--avatar-1 to --avatar-5).
const AVATAR_COLOURS = 5

interface Props {
  character: Character
  party: Character[]
  small?: boolean
}

// A character's initials on a colour chosen by their position in the party.
// Presentation only: the colour is not part of the character's state.
export function Avatar({ character, party, small = false }: Props) {
  const position = Math.max(0, party.findIndex((c) => c.id === character.id))
  const colour = (position % AVATAR_COLOURS) + 1
  return (
    <span className={`avatar avatar-${colour}${small ? ' small' : ''}`} aria-hidden="true">
      {initials(character.name)}
    </span>
  )
}
