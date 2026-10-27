import type { Character, Encounter } from '../contract/index.ts'

// How the state is put into words and shapes on the screen. Pure functions
// of the state, shared by the pane, the strip and the narration.

// Two letters for a name: the first letters of its first two words, or the
// first two letters of a single word.
export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  const letters = words.length > 1 ? words[0][0] + words[1][0] : (words[0] ?? '').slice(0, 2)
  return letters.toUpperCase()
}

export function roundLabel(encounter: Encounter): string {
  if (encounter.outcome) return 'Ended'
  return encounter.round === 0 ? 'Rolling initiative' : `Round ${encounter.round}`
}

// The bar's segments as shares of its width: current and temporary hit points
// out of the maximum plus the temporary ones. Low is half the maximum or less.
export function hitPointBar(character: Character) {
  const total = character.max_hit_points + character.temporary_hit_points
  return {
    current: total > 0 ? character.current_hit_points / total : 0,
    temporary: total > 0 ? character.temporary_hit_points / total : 0,
    low: character.current_hit_points * 2 <= character.max_hit_points,
  }
}

export function hitPointSummary(character: Character): string {
  const temporary = character.temporary_hit_points
  return (
    `${character.current_hit_points} of ${character.max_hit_points} hit points` +
    (temporary > 0 ? `, ${temporary} temporary` : '')
  )
}
