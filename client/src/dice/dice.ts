// The dice block's arithmetic: which dice, which modifiers, the line a roll
// becomes, and a fair roll for a player who lets the screen roll.

export const DICE = [4, 6, 8, 10, 12, 20] as const
export type Sides = (typeof DICE)[number]

export const MODIFIERS = Array.from({ length: 21 }, (_, i) => i - 5) // −5 to +15

// A uniformly random 32-bit unsigned integer.
export type RandomSource = () => number

const UINT32_RANGE = 2 ** 32

export const cryptoSource: RandomSource = () => crypto.getRandomValues(new Uint32Array(1))[0]

// A face from 1 to `sides`, every face equally likely. Values from the top of
// the range that would favour the low faces are drawn again.
export function rollDie(sides: number, source: RandomSource = cryptoSource): number {
  const limit = UINT32_RANGE - (UINT32_RANGE % sides)
  let value = source()
  while (value >= limit) value = source()
  return (value % sides) + 1
}

// Signed, with a true minus sign: +5, +0, −1.
export function formatModifier(modifier: number): string {
  return modifier < 0 ? `−${-modifier}` : `+${modifier}`
}

// The line a roll adds to the declared action. It shows the face as well as
// the total, so a natural 1 or 20 is plain to the dungeon master.
export function rollLine(sides: number, face: number, modifier: number): string {
  if (modifier === 0) return `d${sides}: ${face}`
  const sign = modifier > 0 ? '+' : '−'
  return `d${sides}: ${face} ${sign} ${Math.abs(modifier)} = ${face + modifier}`
}

// Appends a line to the text of the action, on a line of its own.
export function appendLine(text: string, line: string): string {
  if (text === '' || text.endsWith('\n')) return text + line
  return `${text}\n${line}`
}
