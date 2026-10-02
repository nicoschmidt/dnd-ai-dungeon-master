import { describe, expect, it } from 'vitest'

import { type CharacterRow, emptyRow, validateParty } from './validateParty.ts'

function row(overrides: Partial<CharacterRow> = {}): CharacterRow {
  return {
    ...emptyRow(),
    name: 'Brann',
    character_class: 'Fighter',
    level: '3',
    armour_class: '16',
    max_hit_points: '28',
    ...overrides,
  }
}

describe('validateParty', () => {
  it('turns valid rows into the PartyEntry the backend expects', () => {
    const result = validateParty([row({ name: ' Brann ', current_hit_points: '17' })])

    expect(result.entry).toEqual({
      characters: [
        {
          name: 'Brann',
          character_class: 'Fighter',
          level: 3,
          armour_class: 16,
          max_hit_points: 28,
          current_hit_points: 17,
          temporary_hit_points: 0,
        },
      ],
    })
  })

  it('sends empty current hit points as null, meaning the maximum', () => {
    expect(validateParty([row()]).entry?.characters[0].current_hit_points).toBeNull()
  })

  it.each([
    [{ name: '  ' }, 'name'],
    [{ character_class: '' }, 'character_class'],
    [{ level: '0' }, 'level'],
    [{ level: '21' }, 'level'],
    [{ level: '2.5' }, 'level'],
    [{ armour_class: '-1' }, 'armour_class'],
    [{ max_hit_points: '0' }, 'max_hit_points'],
    [{ current_hit_points: '29' }, 'current_hit_points'],
    [{ current_hit_points: 'lots' }, 'current_hit_points'],
    [{ temporary_hit_points: '' }, 'temporary_hit_points'],
  ] as const)('rejects %o in %s', (overrides, field) => {
    const result = validateParty([row(overrides)])

    expect(result.entry).toBeNull()
    expect(result.rows[0][field]).toBeTruthy()
  })

  it('rejects two characters with the same name, ignoring case', () => {
    const result = validateParty([row({ name: 'Brann' }), row({ name: 'brann' })])

    expect(result.entry).toBeNull()
    expect(result.party).toHaveLength(1)
  })

  it('accepts an empty party', () => {
    expect(validateParty([]).entry).toEqual({ characters: [] })
  })
})
