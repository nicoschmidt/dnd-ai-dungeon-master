import { createContext, useContext } from 'react'

import { de } from './de.ts'
import { en, type Strings } from './en.ts'

export type { Strings }

// The table's language, as the backend is configured (`DM_LANGUAGE`). Fixed
// for the session: there is no switch, and a different language is a restart.
export type Language = 'de' | 'en'

export const DEFAULT_LANGUAGE: Language = 'de'

const DICTIONARIES: Record<Language, Strings> = { de, en }

export function dictionary(language: Language): Strings {
  return DICTIONARIES[language]
}

// Without a provider — in a component test — the strings are English, the
// repository's language. The page always provides the configured one.
export const StringsContext = createContext<Strings>(en)

export function useStrings(): Strings {
  return useContext(StringsContext)
}

function isLanguage(value: unknown): value is Language {
  return value === 'de' || value === 'en'
}

// Asks the backend once, before the page renders. When it cannot be reached,
// the page starts in the default language and shows the table as
// disconnected; a reload asks again.
export async function tableLanguage(): Promise<Language> {
  try {
    const response = await fetch('/api/language')
    const body: unknown = await response.json()
    const language = (body as { language?: unknown } | null)?.language
    if (isLanguage(language)) return language
  } catch {
    // Unreachable, or not JSON: fall through to the default.
  }
  return DEFAULT_LANGUAGE
}
