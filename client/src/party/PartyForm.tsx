import { type FormEvent, useState } from 'react'

import type { Character } from '../contract/index.ts'
import {
  type CharacterRow,
  emptyRow,
  type PartyValidation,
  rowFromCharacter,
  validateParty,
} from './validateParty.ts'

interface Props {
  party: Character[]
  onClose: () => void
}

// The columns of the party grid: a short heading above, a full name for
// assistive technology on every input.
const FIELDS: { key: keyof CharacterRow; heading: string; label: string; numeric: boolean }[] = [
  { key: 'name', heading: 'Name', label: 'Name', numeric: false },
  { key: 'character_class', heading: 'Class', label: 'Class', numeric: false },
  { key: 'level', heading: 'Level', label: 'Level', numeric: true },
  { key: 'armour_class', heading: 'AC', label: 'Armour class', numeric: true },
  { key: 'max_hit_points', heading: 'Max HP', label: 'Maximum hit points', numeric: true },
  { key: 'current_hit_points', heading: 'Current HP', label: 'Current hit points', numeric: true },
  { key: 'temporary_hit_points', heading: 'Temp HP', label: 'Temporary hit points', numeric: true },
]

// Messages from a rejected PUT: FastAPI's validation list, or a plain detail.
function serverMessages(body: unknown): string[] {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return [detail]
  if (Array.isArray(detail)) {
    return detail.map((d: { msg?: string; loc?: unknown[] }) =>
      [d.loc?.slice(1).join(' '), d.msg].filter(Boolean).join(': '),
    )
  }
  return ['The party could not be saved.']
}

// Typing the characters in, once before the fight (ADR-0004). What is saved
// reaches the status panel only as `party_updated`, like every other change.
export function PartyForm({ party, onClose }: Props) {
  const [rows, setRows] = useState<CharacterRow[]>(
    party.length > 0 ? party.map(rowFromCharacter) : [emptyRow()],
  )
  const [validation, setValidation] = useState<PartyValidation | null>(null)
  const [serverErrors, setServerErrors] = useState<string[]>([])
  const [saving, setSaving] = useState(false)

  function update(index: number, key: keyof CharacterRow, value: string) {
    setRows(rows.map((row, i) => (i === index ? { ...row, [key]: value } : row)))
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    const result = validateParty(rows)
    setValidation(result)
    setServerErrors([])
    if (!result.entry) return

    setSaving(true)
    const response = await fetch('/api/session/party', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(result.entry),
    }).catch(() => null)
    setSaving(false)

    if (response?.ok) {
      onClose()
    } else if (response) {
      setServerErrors(serverMessages(await response.json().catch(() => null)))
    } else {
      setServerErrors(['The backend could not be reached.'])
    }
  }

  const messages = [...(validation?.party ?? []), ...serverErrors]

  return (
    <form className="party-form" onSubmit={save} noValidate>
      <div className="head">
        <div className="intro">
          <h2>The party</h2>
          <p>Only what the system needs for the fight. Everything else stays on your sheets.</p>
        </div>
      </div>
      <div className="rows-box">
        <div className="rows">
          <div className="grid column-heads" aria-hidden="true">
            {FIELDS.map(({ key, heading }) => (
              <span key={key}>{heading}</span>
            ))}
            <span />
          </div>
          {rows.map((row, index) => (
            <div className="grid row" role="group" aria-label={`Character ${index + 1}`} key={index}>
              {FIELDS.map(({ key, label, numeric }) => {
                const error = validation?.rows[index]?.[key]
                const errorId = `party-${index}-${key}-error`
                return (
                  <div className="cell" key={key}>
                    <input
                      className={numeric ? 'number' : key === 'name' ? 'name' : undefined}
                      aria-label={label}
                      value={row[key]}
                      inputMode={numeric ? 'numeric' : undefined}
                      placeholder={key === 'current_hit_points' ? 'max' : undefined}
                      aria-invalid={error ? 'true' : undefined}
                      aria-describedby={error ? errorId : undefined}
                      onChange={(event) => update(index, key, event.target.value)}
                    />
                    {error && (
                      <span id={errorId} className="error">
                        {error}
                      </span>
                    )}
                  </div>
                )
              })}
              <button
                type="button"
                className="remove"
                aria-label={`Remove ${row.name.trim() || `character ${index + 1}`}`}
                onClick={() => setRows(rows.filter((_, i) => i !== index))}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
                  <path d="M6 6l12 12M18 6 6 18" />
                </svg>
              </button>
            </div>
          ))}
          <div className="add">
            <button type="button" onClick={() => setRows([...rows, emptyRow()])}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
              </svg>
              Add a character
            </button>
          </div>
        </div>
      </div>
      {messages.length > 0 && (
        <div className="messages">
          {messages.map((message) => (
            <p key={message} role="alert">
              {message}
            </p>
          ))}
        </div>
      )}
      <div className="foot">
        <p>Leave current HP empty for full hit points.</p>
        <button type="button" className="secondary" onClick={onClose}>
          Cancel
        </button>
        <button type="submit" className="primary" disabled={saving}>
          Save the party
        </button>
      </div>
    </form>
  )
}
