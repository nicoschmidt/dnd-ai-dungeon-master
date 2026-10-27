import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// The fonts are bundled, not fetched from a CDN: the table may be offline,
// and the screen should not call out to a third party.
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/literata/400.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
