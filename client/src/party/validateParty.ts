import type { Character, CharacterEntry, PartyEntry } from '../contract/index.ts'

// One character as the form holds it: every field as typed.
export interface CharacterRow {
  name: string
  character_class: string
  level: string
  armour_class: string
  max_hit_points: string
  current_hit_points: string
  temporary_hit_points: string
}

export type RowErrors = Partial<Record<keyof CharacterRow, string>>

export interface PartyValidation {
  entry: PartyEntry | null
  rows: RowErrors[]
  party: string[]
}

export function emptyRow(): CharacterRow {
  return {
    name: '',
    character_class: '',
    level: '1',
    armour_class: '',
    max_hit_points: '',
    current_hit_points: '',
    temporary_hit_points: '0',
  }
}

export function rowFromCharacter(character: Character): CharacterRow {
  return {
    name: character.name,
    character_class: character.character_class,
    level: String(character.level),
    armour_class: String(character.armour_class),
    max_hit_points: String(character.max_hit_points),
    current_hit_points: String(character.current_hit_points),
    temporary_hit_points: String(character.temporary_hit_points),
  }
}

function integer(text: string): number | null {
  const trimmed = text.trim()
  return /^-?\d+$/.test(trimmed) ? Number(trimmed) : null
}

// The client's half of "validated at both ends": the same constraints the
// backend's CharacterEntry and PartyEntry enforce, checked before sending.
export function validateParty(rows: CharacterRow[]): PartyValidation {
  const rowErrors: RowErrors[] = []
  const characters: CharacterEntry[] = []

  for (const row of rows) {
    const errors: RowErrors = {}
    const name = row.name.trim()
    const characterClass = row.character_class.trim()
    const level = integer(row.level)
    const armourClass = integer(row.armour_class)
    const maximum = integer(row.max_hit_points)
    const current = row.current_hit_points.trim() === '' ? null : integer(row.current_hit_points)
    const temporary = integer(row.temporary_hit_points)

    if (!name) errors.name = 'A name is needed.'
    if (!characterClass) errors.character_class = 'A class is needed.'
    if (level === null || level < 1 || level > 20) errors.level = 'Level is 1 to 20.'
    if (armourClass === null || armourClass < 0) errors.armour_class = 'A whole number, 0 or more.'
    if (maximum === null || maximum < 1) errors.max_hit_points = 'A whole number, 1 or more.'
    if (row.current_hit_points.trim() !== '' && (current === null || current < 0)) {
      errors.current_hit_points = 'A whole number, 0 or more — or empty for the maximum.'
    } else if (current !== null && maximum !== null && current > maximum) {
      errors.current_hit_points = 'Cannot be more than the maximum.'
    }
    if (temporary === null || temporary < 0) errors.temporary_hit_points = 'A whole number, 0 or more.'

    rowErrors.push(errors)
    if (Object.keys(errors).length === 0) {
      characters.push({
        name,
        character_class: characterClass,
        level: level!,
        armour_class: armourClass!,
        max_hit_points: maximum!,
        current_hit_points: current,
        temporary_hit_points: temporary!,
      })
    }
  }

  const partyErrors: string[] = []
  const seen = new Set<string>()
  for (const row of rows) {
    const key = row.name.trim().toLocaleLowerCase()
    if (key && seen.has(key)) partyErrors.push(`Two characters are called ${row.name.trim()}.`)
    seen.add(key)
  }

  const valid = characters.length === rows.length && partyErrors.length === 0
  return { entry: valid ? { characters } : null, rows: rowErrors, party: partyErrors }
}
