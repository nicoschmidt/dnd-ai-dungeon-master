import { type KeyboardEvent, useEffect, useRef, useState } from 'react'

import { DICE, MODIFIERS, formatModifier, rollDie, rollLine } from './dice.ts'
import { DiceIcon } from './DiceIcon.tsx'

interface Props {
  disabled: boolean
  onLine: (line: string) => void
  // The screen's die, for a player who lets it roll. Tests pass a fixed one.
  roll?: (sides: number) => number
}

type Step =
  | { kind: 'dice'; from?: number }
  | { kind: 'face'; sides: number }
  | { kind: 'modifier'; sides: number; face: number }

// A shortcut to typing a roll: pick the die, then the face that came up (or
// let the screen roll it), then the modifier. The line it makes is appended to
// the action's text, where it can still be changed before it is declared.
export function DiceBlock({ disabled, onLine, roll = rollDie }: Props) {
  const [step, setStep] = useState<Step>({ kind: 'dice' })
  const block = useRef<HTMLDivElement>(null)
  // Focus follows a step only when the player moved there, never on mount.
  const moved = useRef(false)

  useEffect(() => {
    if (!moved.current) return
    moved.current = false
    block.current?.querySelector<HTMLElement>('[data-focus]')?.focus()
  }, [step])

  function go(next: Step) {
    moved.current = true
    setStep(next)
  }

  function back() {
    if (step.kind === 'face') go({ kind: 'dice', from: step.sides })
    if (step.kind === 'modifier') go({ kind: 'face', sides: step.sides })
  }

  function onKey(event: KeyboardEvent) {
    if (event.key === 'Escape' && step.kind !== 'dice') {
      event.preventDefault()
      back()
    }
  }

  function finish(sides: number, face: number, modifier: number) {
    setStep({ kind: 'dice' })
    onLine(rollLine(sides, face, modifier))
  }

  return (
    <div className="dice" ref={block} role="group" aria-label="Dice" onKeyDown={onKey}>
      {step.kind === 'dice' && (
        <>
          <p className="caption">Enter a roll</p>
          <div className="dice-grid">
            {DICE.map((sides) => (
              <button
                key={sides}
                type="button"
                aria-label={`d${sides}`}
                title={`d${sides}`}
                disabled={disabled}
                data-focus={step.from === sides ? '' : undefined}
                onClick={() => go({ kind: 'face', sides })}
              >
                <DiceIcon sides={sides} />
              </button>
            ))}
          </div>
        </>
      )}

      {step.kind === 'face' && (
        <>
          <p className="caption">d{step.sides}: what came up?</p>
          <div className="dice-grid">
            <BackButton label="Back to the dice" onClick={back} />
            {Array.from({ length: step.sides }, (_, i) => i + 1).map((face) => (
              <button
                key={face}
                type="button"
                data-focus={face === 1 ? '' : undefined}
                onClick={() => go({ kind: 'modifier', sides: step.sides, face })}
              >
                {face}
              </button>
            ))}
            <button
              type="button"
              className="roll"
              onClick={() => go({ kind: 'modifier', sides: step.sides, face: roll(step.sides) })}
            >
              <DiceIcon sides={step.sides} size={18} />
              Roll
            </button>
          </div>
        </>
      )}

      {step.kind === 'modifier' && (
        <>
          <p className="caption">
            d{step.sides}: {step.face} · modifier?
          </p>
          <div className="dice-grid">
            <BackButton label="Back to the faces" onClick={back} />
            {MODIFIERS.map((modifier) => (
              <button
                key={modifier}
                type="button"
                data-focus={modifier === 0 ? '' : undefined}
                onClick={() => finish(step.sides, step.face, modifier)}
              >
                {formatModifier(modifier)}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function BackButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" className="back" aria-label={label} title={label} onClick={onClick}>
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M19 12H5M11 6l-6 6 6 6" />
      </svg>
    </button>
  )
}
