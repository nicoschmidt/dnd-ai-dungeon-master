import { describe, expect, it } from 'vitest'

import { MODIFIERS, appendLine, formatModifier, rollDie, rollLine } from './dice.ts'

// A random source that answers with the given values, in order.
function sequence(...values: number[]) {
  let next = 0
  return () => values[next++]
}

describe('rollDie', () => {
  it('reaches both ends of the range', () => {
    expect(rollDie(20, sequence(0))).toBe(1)
    expect(rollDie(20, sequence(19))).toBe(20)
    expect(rollDie(6, sequence(2 ** 32 - 5))).toBe(6)
  })

  it('gives every face the same share of the values it keeps', () => {
    const counts = [0, 0, 0, 0, 0, 0]
    for (let value = 0; value < 600; value++) counts[rollDie(6, sequence(value)) - 1]++

    expect(counts).toEqual([100, 100, 100, 100, 100, 100])
  })

  it('draws again from the top of the range, which would favour the low faces', () => {
    // 2^32 is 4 more than a multiple of 6: the last four values are dropped.
    expect(rollDie(6, sequence(2 ** 32 - 1, 2 ** 32 - 4, 3))).toBe(4)
  })

  it('rolls with the browser’s random source by default', () => {
    for (let i = 0; i < 50; i++) {
      const face = rollDie(4)
      expect(face).toBeGreaterThanOrEqual(1)
      expect(face).toBeLessThanOrEqual(4)
    }
  })
})

describe('rollLine', () => {
  it('shows face, modifier and total', () => {
    expect(rollLine(20, 14, 5)).toBe('d20: 14 + 5 = 19')
  })

  it('subtracts a negative modifier with a true minus sign', () => {
    expect(rollLine(20, 14, -1)).toBe('d20: 14 − 1 = 13')
  })

  it('shows the face alone for +0', () => {
    expect(rollLine(8, 6, 0)).toBe('d8: 6')
  })
})

describe('the modifiers', () => {
  it('run from −5 to +15', () => {
    expect(MODIFIERS[0]).toBe(-5)
    expect(MODIFIERS.at(-1)).toBe(15)
    expect(MODIFIERS).toHaveLength(21)
  })

  it('are written with their sign', () => {
    expect([-5, 0, 3].map(formatModifier)).toEqual(['−5', '+0', '+3'])
  })
})

describe('appendLine', () => {
  it('starts an empty text with the line', () => {
    expect(appendLine('', 'd20: 14')).toBe('d20: 14')
  })

  it('puts the line under the text there', () => {
    expect(appendLine('I attack the ogre.', 'd20: 14')).toBe('I attack the ogre.\nd20: 14')
  })

  it('does not add a blank line after a line break', () => {
    expect(appendLine('I attack the ogre.\n', 'd20: 14')).toBe('I attack the ogre.\nd20: 14')
  })
})
