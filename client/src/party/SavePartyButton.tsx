import type { Character } from '../contract/index.ts'
import { useStrings } from '../language/strings.ts'
import { partyFile, partyFileName } from './partyFile.ts'

interface Props {
  party: Character[]
}

// Downloads the party as it stands, at any time: before, during and after a
// fight. The browser decides where the file goes; the backend keeps nothing.
export function SavePartyButton({ party }: Props) {
  const t = useStrings()

  function save() {
    const link = document.createElement('a')
    link.href = `data:application/json;charset=utf-8,${encodeURIComponent(partyFile(party))}`
    link.download = partyFileName(t.party.fileStem, new Date())
    link.click()
  }

  return (
    <button type="button" className="party-button" onClick={save}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 4v11M7 10l5 5 5-5M5 20h14" />
      </svg>
      {t.party.saveFile}
    </button>
  )
}
