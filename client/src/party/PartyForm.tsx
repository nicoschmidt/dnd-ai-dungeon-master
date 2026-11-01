import { type ChangeEvent, type FormEvent, useRef, useState } from 'react'

import type { Character } from '../contract/index.ts'
import { useStrings } from '../language/strings.ts'
import { readPartyFile } from './partyFile.ts'
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

// The columns of the party grid. Their short heading above, and the full name
// for assistive technology on every input, are in the dictionary.
const FIELDS: { key: keyof CharacterRow; numeric: boolean }[] = [
  { key: 'name', numeric: false },
  { key: 'character_class', numeric: false },
  { key: 'level', numeric: true },
  { key: 'armour_class', numeric: true },
  { key: 'max_hit_points', numeric: true },
  { key: 'current_hit_points', numeric: true },
  { key: 'temporary_hit_points', numeric: true },
]

// Typing the characters in, once before the fight (ADR-0004). What is saved
// reaches the status panel only as `party_updated`, like every other change.
export function PartyForm({ party, onClose }: Props) {
  const t = useStrings()
  const [rows, setRows] = useState<CharacterRow[]>(
    party.length > 0 ? party.map(rowFromCharacter) : [emptyRow()],
  )
  const [validation, setValidation] = useState<PartyValidation | null>(null)
  const [serverErrors, setServerErrors] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [fileProblems, setFileProblems] = useState<string[]>([])
  const fileInput = useRef<HTMLInputElement>(null)

  function update(index: number, key: keyof CharacterRow, value: string) {
    setRows(rows.map((row, i) => (i === index ? { ...row, [key]: value } : row)))
  }

  // A party file replaces the rows, to be changed and saved like typed ones.
  // A file that is not a party is refused, and the rows stay as they were.
  async function load(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = '' // so that the same file can be chosen again
    if (!file) return
    const text = await file.text().catch(() => null)
    const result = text === null ? { problems: [t.party.file.unreadable] } : readPartyFile(text, t)
    if ('rows' in result) {
      setRows(result.rows)
      setValidation(null)
      setServerErrors([])
      setFileProblems([])
    } else {
      setFileProblems(result.problems)
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    const result = validateParty(rows, t.validation)
    setValidation(result)
    setServerErrors([])
    setFileProblems([])
    if (!result.entry) return

    setSaving(true)
    const response = await fetch('/api/session/party', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(result.entry),
    }).catch(() => null)
    setSaving(false)

    // The backend's own messages are English; the table reads its own. A
    // refusal other than the started encounter means the client let through
    // what the backend does not accept, which the checks above are there to
    // prevent.
    if (response?.ok) {
      onClose()
    } else if (response) {
      setServerErrors([response.status === 409 ? t.party.locked : t.party.notSaved])
    } else {
      setServerErrors([t.party.unreachable])
    }
  }

  const messages = [...fileProblems, ...(validation?.party ?? []), ...serverErrors]

  return (
    <form className="party-form" onSubmit={save} noValidate>
      <div className="head">
        <div className="intro">
          <h2>{t.party.heading}</h2>
          <p>{t.party.intro}</p>
        </div>
        <input
          ref={fileInput}
          type="file"
          accept=".json,application/json"
          hidden
          onChange={(event) => void load(event)}
        />
        <button type="button" className="secondary" onClick={() => fileInput.current?.click()}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M12 15V4M7 9l5-5 5 5M5 20h14" />
          </svg>
          {t.party.loadFile}
        </button>
      </div>
      <div className="rows-box">
        <div className="rows">
          <div className="grid column-heads" aria-hidden="true">
            {FIELDS.map(({ key }) => (
              <span key={key}>{t.party.columns[key].heading}</span>
            ))}
            <span />
          </div>
          {rows.map((row, index) => (
            <div className="grid row" role="group" aria-label={t.party.character(index + 1)} key={index}>
              {FIELDS.map(({ key, numeric }) => {
                const error = validation?.rows[index]?.[key]
                const errorId = `party-${index}-${key}-error`
                return (
                  <div className="cell" key={key}>
                    <input
                      className={numeric ? 'number' : key === 'name' ? 'name' : undefined}
                      aria-label={t.party.columns[key].label}
                      value={row[key]}
                      inputMode={numeric ? 'numeric' : undefined}
                      placeholder={key === 'current_hit_points' ? t.party.maximum : undefined}
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
                aria-label={t.party.remove(row.name.trim() || t.party.character(index + 1))}
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
              {t.party.add}
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
        <p>{t.party.currentEmpty}</p>
        <button type="button" className="secondary" onClick={onClose}>
          {t.party.cancel}
        </button>
        <button type="submit" className="primary" disabled={saving}>
          {t.party.save}
        </button>
      </div>
    </form>
  )
}
