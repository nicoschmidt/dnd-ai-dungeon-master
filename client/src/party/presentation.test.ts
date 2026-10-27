import { describe, expect, it } from 'vitest'

import type { Character } from '../contract/index.ts'
import { hitPointBar, initials } from './presentation.ts'

const brann: Character = {
  id: 'brann',
  name: 'Brann',
  character_class: 'Fighter',
  level: 3,
  armour_class: 16,
  max_hit_points: 20,
  current_hit_points: 20,
  temporary_hit_points: 0,
  conditions: [],
}

describe('initials', () => {
  it('takes the first two letters of a single name', () => {
    expect(initials('Brann')).toBe('BR')
  })

  it('takes the first letters of the first two words', () => {
    expect(initials(' ser  galen of the vale ')).toBe('SG')
  })

  it('makes do with a name of one letter, or none', () => {
    expect(initials('Q')).toBe('Q')
    expect(initials('')).toBe('')
  })
})

describe('hitPointBar', () => {
  it('measures current and temporary hit points against maximum plus temporary', () => {
    expect(hitPointBar({ ...brann, current_hit_points: 15, temporary_hit_points: 5 })).toEqual({
      current: 15 / 25,
      temporary: 5 / 25,
      low: false,
    })
  })

  it('is low at half the maximum or below, and not above it', () => {
    expect(hitPointBar({ ...brann, current_hit_points: 11 }).low).toBe(false)
    expect(hitPointBar({ ...brann, current_hit_points: 10 }).low).toBe(true)
    expect(hitPointBar({ ...brann, current_hit_points: 0 }).low).toBe(true)
  })

  it('judges low on the maximum alone, whatever the temporary hit points', () => {
    expect(hitPointBar({ ...brann, current_hit_points: 10, temporary_hit_points: 8 }).low).toBe(
      true,
    )
  })
})
