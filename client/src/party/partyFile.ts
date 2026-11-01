import type { Character, CharacterEntry, PartyEntry } from '../contract/index.ts'
import type { Strings } from '../language/strings.ts'
import { type CharacterRow, validateParty } from './validateParty.ts'

// A party file is a `PartyEntry`, as `PUT /api/session/party` takes it
// (docs/event-contract.md): nothing around it, nothing beyond it. The backend
// stores nothing; the file lives wherever the browser saves it.

// The party as it stands, with its current hit points: what the group would
// type in to carry on from here. Ids and conditions are not part of an entry.
export function partyEntryOf(party: Character[]): PartyEntry {
  return {
    characters: party.map(
      (c): CharacterEntry => ({
        name: c.name,
        character_class: c.character_class,
        level: c.level,
        armour_class: c.armour_class,
        max_hit_points: c.max_hit_points,
        current_hit_points: c.current_hit_points,
        temporary_hit_points: c.temporary_hit_points,
      }),
    ),
  }
}

export function partyFile(party: Character[]): string {
  return `${JSON.stringify(partyEntryOf(party), null, 2)}\n`
}

// The day goes into the name, so the files of several evenings sit side by side.
export function partyFileName(stem: string, day: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${stem}-${day.getFullYear()}-${pad(day.getMonth() + 1)}-${pad(day.getDate())}.json`
}

export type PartyFileResult = { rows: CharacterRow[] } | { problems: string[] }

const REQUIRED_TEXT = ['name', 'character_class'] as const
const REQUIRED_NUMBERS = ['level', 'armour_class', 'max_hit_points'] as const
const FIELDS: readonly string[] = [
  ...REQUIRED_TEXT,
  ...REQUIRED_NUMBERS,
  'current_hit_points',
  'temporary_hit_points',
]

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

// A problem names the character it is about: by name, or by position.
function who(name: unknown, index: number, t: Strings): string {
  return typeof name === 'string' && name.trim() ? name.trim() : t.party.character(index + 1)
}

// Reads a party file into rows for the party form, or says what is wrong with
// it. The shape is checked here; the values by the same checks the form runs
// before saving, so a file is refused for exactly what the form would refuse.
export function readPartyFile(text: string, t: Strings): PartyFileResult {
  const m = t.party.file
  let data: unknown
  try {
    data = JSON.parse(text)
  } catch {
    return { problems: [m.notJson] }
  }
  if (!isObject(data) || !Array.isArray(data.characters)) return { problems: [m.notParty] }
  const extra = Object.keys(data).filter((key) => key !== 'characters')
  if (extra.length > 0) return { problems: [m.unknownField(extra[0])] }

  const problems: string[] = []
  const rows: CharacterRow[] = []
  data.characters.forEach((entry: unknown, index) => {
    if (!isObject(entry)) {
      problems.push(`${who(null, index, t)}: ${m.notCharacter}`)
      return
    }
    const fail = (problem: string) => problems.push(`${who(entry.name, index, t)}: ${problem}`)
    for (const key of Object.keys(entry)) {
      if (!FIELDS.includes(key)) fail(m.unknownField(key))
    }
    for (const key of REQUIRED_TEXT) {
      if (typeof entry[key] !== 'string') fail(m.text(t.party.columns[key].label))
    }
    for (const key of REQUIRED_NUMBERS) {
      if (!Number.isInteger(entry[key])) fail(m.number(t.party.columns[key].label))
    }
    const current = entry.current_hit_points ?? null
    if (current !== null && !Number.isInteger(current)) {
      fail(m.number(t.party.columns.current_hit_points.label))
    }
    const temporary = entry.temporary_hit_points ?? 0
    if (!Number.isInteger(temporary)) fail(m.number(t.party.columns.temporary_hit_points.label))

    rows.push({
      name: String(entry.name ?? ''),
      character_class: String(entry.character_class ?? ''),
      level: String(entry.level ?? ''),
      armour_class: String(entry.armour_class ?? ''),
      max_hit_points: String(entry.max_hit_points ?? ''),
      current_hit_points: current === null ? '' : String(current),
      temporary_hit_points: String(temporary),
    })
  })
  if (problems.length > 0) return { problems }

  const validation = validateParty(rows, t.validation)
  if (validation.entry) return { rows }
  validation.rows.forEach((errors, index) => {
    for (const [key, message] of Object.entries(errors) as [keyof CharacterRow, string][]) {
      problems.push(`${who(rows[index].name, index, t)}, ${t.party.columns[key].label}: ${message}`)
    }
  })
  return { problems: [...problems, ...validation.party] }
}
