import { useEffect, useState } from 'react'

type BackendStatus = 'connecting' | 'ok' | 'unreachable'

function App() {
  const [status, setStatus] = useState<BackendStatus>('connecting')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => response.json())
      .then((body: { status: string }) =>
        setStatus(body.status === 'ok' ? 'ok' : 'unreachable'),
      )
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <main>
      <h1>AI Dungeon Master</h1>
      <p>Backend: {status}</p>
    </main>
  )
}

export default App
