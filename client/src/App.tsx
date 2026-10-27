import { useState } from 'react'

import { ActionForm } from './ActionForm.tsx'
import type { DeclaredAction } from './contract/index.ts'
import { Narration } from './Narration.tsx'
import { PartyDialog } from './party/PartyDialog.tsx'
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
        <h1>AI Dungeon Master</h1>
        <p className="connection">{CONNECTION_LABEL[connection]}</p>
        <div className="party">
          {partyFixed ? (
            <p className="note">The party is fixed for this encounter.</p>
          ) : (
            <button type="button" onClick={() => setEditingParty(true)}>
              {state.party.length === 0 ? 'Enter the party' : 'Edit the party'}
            </button>
          )}
        </div>
      </header>

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

export default App
