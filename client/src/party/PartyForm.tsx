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

const FIELDS: { key: keyof CharacterRow; label: string; numeric: boolean }[] = [
  { key: 'name', label: 'Name', numeric: false },
  { key: 'character_class', label: 'Class', numeric: false },
  { key: 'level', label: 'Level', numeric: true },
  { key: 'armour_class', label: 'AC', numeric: true },
  { key: 'max_hit_points', label: 'Max HP', numeric: true },
  { key: 'current_hit_points', label: 'Current HP', numeric: true },
  { key: 'temporary_hit_points', label: 'Temp HP', numeric: true },
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

  return (
    <form className="party-form" onSubmit={save} noValidate>
      <h2>The party</h2>
      {rows.map((row, index) => (
        <fieldset key={index}>
          <legend>Character {index + 1}</legend>
          {FIELDS.map(({ key, label, numeric }) => {
            const error = validation?.rows[index]?.[key]
            return (
              <label key={key}>
                {label}
                <input
                  value={row[key]}
                  inputMode={numeric ? 'numeric' : undefined}
                  placeholder={key === 'current_hit_points' ? 'max' : undefined}
                  aria-invalid={error ? 'true' : undefined}
                  onChange={(event) => update(index, key, event.target.value)}
                />
                {error && <span className="error">{error}</span>}
              </label>
            )
          })}
          <button type="button" onClick={() => setRows(rows.filter((_, i) => i !== index))}>
            Remove
          </button>
        </fieldset>
      ))}
      {[...(validation?.party ?? []), ...serverErrors].map((message) => (
        <p key={message} role="alert">
          {message}
        </p>
      ))}
      <button type="button" onClick={() => setRows([...rows, emptyRow()])}>
        Add a character
      </button>{' '}
      <button type="submit" disabled={saving}>
        Save the party
      </button>{' '}
      <button type="button" onClick={onClose}>
        Cancel
      </button>
    </form>
  )
}
