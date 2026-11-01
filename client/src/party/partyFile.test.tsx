import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Character } from '../contract/index.ts'
import { en } from '../language/en.ts'
import { PartyForm } from './PartyForm.tsx'
import { partyEntryOf, partyFile, partyFileName, readPartyFile } from './partyFile.ts'
import { SavePartyButton } from './SavePartyButton.tsx'
import { validateParty } from './validateParty.ts'

const brann: Character = {
  id: 'brann',
  name: 'Brann',
  character_class: 'Fighter',
  level: 3,
  armour_class: 16,
  max_hit_points: 28,
  current_hit_points: 17,
  temporary_hit_points: 5,
  conditions: ['prone'],
}

const mira: Character = {
  ...brann,
  id: 'mira',
  name: 'Mira',
  character_class: 'Wizard',
  max_hit_points: 9,
  current_hit_points: 9,
  temporary_hit_points: 0,
  conditions: [],
}

const party = [brann, mira]

function problemsOf(content: unknown): string[] {
  const text = typeof content === 'string' ? content : JSON.stringify(content)
  const result = readPartyFile(text, en)
  return 'problems' in result ? result.problems : []
}

function character(overrides: Record<string, unknown> = {}) {
  return { ...partyEntryOf([brann]).characters[0], ...overrides }
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('a party file', () => {
  it('is the PartyEntry of the party as it stands, current hit points included', () => {
    expect(JSON.parse(partyFile(party))).toEqual({
      characters: [
        {
          name: 'Brann',
          character_class: 'Fighter',
          level: 3,
          armour_class: 16,
          max_hit_points: 28,
          current_hit_points: 17,
          temporary_hit_points: 5,
        },
        {
          name: 'Mira',
          character_class: 'Wizard',
          level: 3,
          armour_class: 16,
          max_hit_points: 9,
          current_hit_points: 9,
          temporary_hit_points: 0,
        },
      ],
    })
  })

  it('loads back into the same party', () => {
    const result = readPartyFile(partyFile(party), en)

    expect('rows' in result && validateParty(result.rows, en.validation).entry).toEqual(
      partyEntryOf(party),
    )
  })

  it('may leave out what a PartyEntry has defaults for', () => {
    const result = readPartyFile(
      JSON.stringify({ characters: [{ ...character(), current_hit_points: undefined, temporary_hit_points: undefined }] }),
      en,
    )

    expect('rows' in result && result.rows[0]).toMatchObject({
      current_hit_points: '',
      temporary_hit_points: '0',
    })
  })

  it('is named after the day it was saved', () => {
    expect(partyFileName('party', new Date(2026, 10, 1))).toBe('party-2026-11-01.json')
  })
})

describe('a file that is not a party', () => {
  it.each([
    ['not JSON', '{"characters": [', en.party.file.notJson],
    ['without characters', { name: 'Brann' }, en.party.file.notParty],
    ['a list', [character()], en.party.file.notParty],
    ['with more than the characters', { version: 2, characters: [] }, en.party.file.unknownField('version')],
  ])('is refused when it is %s', (_, content, problem) => {
    expect(problemsOf(content)).toEqual([problem])
  })

  it('names the character and the field that are wrong', () => {
    const problems = problemsOf({
      characters: [character(), character({ name: 'Mira', level: 'three', id: 'mira' })],
    })

    expect(problems).toEqual([
      'Mira: “id” is not a field of a party file.',
      'Mira: Level must be a whole number.',
    ])
  })

  it('is refused for what the form would refuse', () => {
    expect(problemsOf({ characters: [character({ level: 21 })] })).toEqual([
      'Brann, Level: Level is 1 to 20.',
    ])
    expect(problemsOf({ characters: [character({ name: ' ' })] })).toEqual([
      'Character 1, Name: A name is needed.',
    ])
    expect(problemsOf({ characters: [character(), character({ name: 'brann' })] })).toEqual([
      'Two characters are called brann.',
    ])
  })
})

function choose(content: string) {
  const input = document.querySelector<HTMLInputElement>('input[type="file"]')!
  fireEvent.change(input, {
    target: { files: [new File([content], 'party.json', { type: 'application/json' })] },
  })
}

function names(): string[] {
  return screen.getAllByRole('textbox', { name: 'Name' }).map((i) => (i as HTMLInputElement).value)
}

describe('loading in the party form', () => {
  it('puts the file’s characters into the form, to be changed before saving', async () => {
    render(<PartyForm party={[]} onClose={vi.fn()} />)

    choose(partyFile(party))

    await waitFor(() => expect(names()).toEqual(['Brann', 'Mira']))
    expect(screen.getAllByRole('textbox', { name: 'Current hit points' })[0]).toHaveProperty(
      'value',
      '17',
    )
  })

  it('refuses a file that is not a party, says why, and keeps what it had', async () => {
    render(<PartyForm party={[mira]} onClose={vi.fn()} />)

    choose('{"party": []}')

    expect(await screen.findByRole('alert')).toHaveProperty('textContent', en.party.file.notParty)
    expect(names()).toEqual(['Mira'])
  })
})

describe('saving as a file', () => {
  it('downloads the party file, named after the day', () => {
    const clicked: HTMLAnchorElement[] = []
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      clicked.push(this)
    })
    render(<SavePartyButton party={party} />)

    fireEvent.click(screen.getByRole('button', { name: 'Save party' }))

    expect(clicked).toHaveLength(1)
    const [kind, content] = clicked[0].href.split(',')
    expect(kind).toBe('data:application/json;charset=utf-8')
    expect(decodeURIComponent(content)).toBe(partyFile(party))
    expect(clicked[0].download).toMatch(/^party-\d{4}-\d{2}-\d{2}\.json$/)
  })
})
