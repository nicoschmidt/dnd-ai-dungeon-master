import { useState } from 'react'

import { ActionForm } from './ActionForm.tsx'
import type { DeclaredAction } from './contract/index.ts'
import { Narration } from './Narration.tsx'
import { PartyDialog } from './party/PartyDialog.tsx'
import { StateStrip } from './party/StateStrip.tsx'
import { StatusPanel } from './party/StatusPanel.tsx'
import { type Connection, useTableStream } from './stream/useTableStream.ts'

const CONNECTION_LABEL: Record<Connection, string> = {
  connecting: 'connecting…',
  open: 'connected',
  reconnecting: 'connection lost, reconnecting…',
  closed: 'disconnected — reload the page',
}

function App() {
  const { state, connection } = useTableStream()
  const [sendError, setSendError] = useState<string | null>(null)
  const [editingParty, setEditingParty] = useState(false)
  const partyFixed = state.encounter !== null
  // The fight is running from the start of an encounter until its outcome.
  const fight = state.encounter && !state.encounter.outcome ? state.encounter : null

  async function declare(action: DeclaredAction): Promise<boolean> {
    const response = await fetch('/api/session/actions', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(action),
    }).catch(() => null)

    if (response?.status === 202) {
      setSendError(null)
      return true
    }
    setSendError(
      response?.status === 409
        ? 'The dungeon master is still answering the last action.'
        : 'The action did not reach the dungeon master. Try again.',
    )
    return false
  }

  return (
    <div className="table">
      <header className="table-header">
        <h1 className="brand">
          <D20Icon />
          AI Dungeon Master
        </h1>
        {fight && (
          <p className="fight-pill">
            <span className="dot" aria-hidden="true" />
            <span>
              Fight against <strong>{fight.opponent_name}</strong>
            </span>
            <span className="round">
              · {fight.round === 0 ? 'rolling initiative' : `round ${fight.round}`}
            </span>
          </p>
        )}
        <p className={`connection ${connection}`}>
          <span className="dot" aria-hidden="true" />
          {CONNECTION_LABEL[connection]}
        </p>
        {partyFixed ? (
          <button type="button" className="party-button" disabled>
            <LockIcon />
            The party is fixed for this encounter
          </button>
        ) : (
          <button type="button" className="party-button" onClick={() => setEditingParty(true)}>
            {state.party.length === 0 ? 'Enter the party' : 'Edit the party'}
          </button>
        )}
      </header>

      <StateStrip party={state.party} encounter={state.encounter} />

      <main className="story">
        <Narration turns={state.turns} party={state.party} />
        {state.error && <p role="alert">{state.error.message}</p>}
        {sendError && <p role="alert">{sendError}</p>}
        <ActionForm
          party={state.party}
          encounter={state.encounter}
          busy={state.busy}
          onDeclare={declare}
        />
      </main>

      <StatusPanel party={state.party} encounter={state.encounter} />

      {editingParty && !partyFixed && (
        <PartyDialog party={state.party} onClose={() => setEditingParty(false)} />
      )}
    </div>
  )
}

// A d20 in outline, the app's mark.
function D20Icon() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" strokeWidth="1.6"
      strokeLinejoin="round" aria-hidden="true">
      <path d="M12 2.5 20.5 7.25v9.5L12 21.5 3.5 16.75v-9.5Z" />
      <path d="M12 6.5 17 15H7Z" />
      <path d="M12 2.5v4M3.5 7.25 7 15M20.5 7.25 17 15M7 15l-3.5 1.75M17 15l3.5 1.75M7 15h10M12 21.5 7 15M12 21.5 17 15" />
    </svg>
  )
}

function LockIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </svg>
  )
}

export default App
