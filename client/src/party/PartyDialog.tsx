import { useEffect, useRef } from 'react'

import type { Character } from '../contract/index.ts'
import { PartyForm } from './PartyForm.tsx'

interface Props {
  party: Character[]
  onClose: () => void
}

// The party form over the table screen, as a modal dialog: the page behind it
// is inert, and Escape closes it like Cancel does.
export function PartyDialog({ party, onClose }: Props) {
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    // Strict mode runs this twice; opening an open dialog would throw.
    if (dialog.current && !dialog.current.open) dialog.current.showModal()
  }, [])

  return (
    <dialog ref={dialog} className="party-dialog" aria-label="The party" onClose={onClose}>
      <PartyForm party={party} onClose={onClose} />
    </dialog>
  )
}
