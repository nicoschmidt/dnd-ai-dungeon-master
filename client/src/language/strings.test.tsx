import { fireEvent, render, screen, within } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ActionForm } from '../ActionForm.tsx'
import type { Character, Encounter } from '../contract/index.ts'
import { DiceBlock } from '../dice/DiceBlock.tsx'
import { StatusPanel } from '../party/StatusPanel.tsx'
import { type Language, StringsContext, dictionary, tableLanguage } from './strings.ts'

const brann: Character = {
  id: 'brann',
  name: 'Brann',
  character_class: 'Fighter',
  level: 3,
  armour_class: 16,
  max_hit_points: 28,
  current_hit_points: 17,
  temporary_hit_points: 0,
  conditions: ['prone'],
}

const fight: Encounter = {
  opponent_name: 'Ogre',
  round: 2,
  turn_order: [
    { kind: 'character', id: 'brann', name: 'Brann' },
    { kind: 'opponent', id: 'ogre', name: 'Ogre' },
  ],
  current_turn: 0,
  outcome: null,
}

function renderIn(language: Language, ui: ReactNode) {
  return render(<StringsContext value={dictionary(language)}>{ui}</StringsContext>)
}

function answering(response: Promise<Response>) {
  vi.stubGlobal('fetch', vi.fn(() => response))
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('the table’s language', () => {
  it.each([
    ['de', 'Ansagen', 'Wer handelt?', 'Alle'],
    ['en', 'Declare', 'Who acts?', 'The table'],
  ] as const)('labels the input in %s', (language, declare, whoActs, table) => {
    renderIn(
      language,
      <ActionForm party={[brann]} encounter={fight} busy={false} onDeclare={vi.fn()} />,
    )

    expect(screen.getByRole('button', { name: declare })).toBeTruthy()
    expect(screen.getByRole('radiogroup', { name: whoActs })).toBeTruthy()
    expect(screen.getByRole('radio', { name: table })).toBeTruthy()
  })

  it.each([
    ['de', 'Runde 2', 'Stufe 3', 'liegend'],
    ['en', 'Round 2', 'level 3', 'prone'],
  ] as const)('shows the state and the conditions in %s', (language, round, level, condition) => {
    renderIn(language, <StatusPanel party={[brann]} encounter={fight} />)

    expect(screen.getByText(round)).toBeTruthy()
    expect(screen.getByText(`Fighter · ${level}`)).toBeTruthy()
    expect(screen.getByText(condition)).toBeTruthy()
  })

  it('names the dice the German way, in the buttons and in the line', () => {
    const onLine = vi.fn()
    renderIn('de', <DiceBlock disabled={false} onLine={onLine} roll={() => 14} />)
    const dice = within(screen.getByRole('group', { name: 'Würfel' }))

    fireEvent.click(dice.getByRole('button', { name: 'W20' }))
    fireEvent.click(dice.getByRole('button', { name: 'Würfeln' }))
    expect(dice.getByText('W20: 14 · Modifikator?')).toBeTruthy()
    fireEvent.click(dice.getByRole('button', { name: '+5' }))

    expect(onLine).toHaveBeenCalledWith('W20: 14 + 5 = 19')
  })
})

describe('tableLanguage', () => {
  it('reads the language the backend is configured with', async () => {
    answering(Promise.resolve(Response.json({ language: 'en' })))

    expect(await tableLanguage()).toBe('en')
    expect(fetch).toHaveBeenCalledWith('/api/language')
  })

  it('starts in German when the backend cannot be reached', async () => {
    answering(Promise.reject(new TypeError('Failed to fetch')))

    expect(await tableLanguage()).toBe('de')
  })

  it('starts in German when the answer is not a language it knows', async () => {
    answering(Promise.resolve(Response.json({ language: 'fr' })))

    expect(await tableLanguage()).toBe('de')
  })
})
