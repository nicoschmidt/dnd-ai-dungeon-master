import { useEffect, useReducer, useState } from 'react'

import { TABLE_EVENT_TYPES, type TableEvent } from '../contract/index.ts'
import { applyEvent, initialTableState, type TableState } from './tableState.ts'

export type Connection = 'connecting' | 'open' | 'reconnecting' | 'closed'

type Action = { kind: 'event'; event: TableEvent } | { kind: 'reset' }

function reduce(state: TableState, action: Action): TableState {
  return action.kind === 'reset' ? initialTableState : applyEvent(state, action.event)
}

// The table's state, kept current from the backend's event stream.
//
// The browser reconnects on its own after a dropped connection and sends the
// id of the last event it received, so the backend resumes right after it.
// Event ids start with the backend's session id: when that changes, the
// backend has restarted and is replaying a new session from its start, so the
// state is rebuilt rather than appended to.
export function useTableStream(url = '/api/session/stream') {
  const [state, dispatch] = useReducer(reduce, initialTableState)
  const [connection, setConnection] = useState<Connection>('connecting')

  useEffect(() => {
    dispatch({ kind: 'reset' })
    const source = new EventSource(url)
    let session: string | null = null

    const receive = (message: MessageEvent<string>) => {
      const eventSession = message.lastEventId.split(':')[0]
      if (session !== null && eventSession !== session) {
        dispatch({ kind: 'reset' })
      }
      session = eventSession
      dispatch({ kind: 'event', event: JSON.parse(message.data) as TableEvent })
    }

    source.onopen = () => setConnection('open')
    source.onerror = () =>
      setConnection(source.readyState === EventSource.CLOSED ? 'closed' : 'reconnecting')
    for (const type of TABLE_EVENT_TYPES) {
      source.addEventListener(type, receive)
    }
    return () => source.close()
  }, [url])

  return { state, connection }
}
