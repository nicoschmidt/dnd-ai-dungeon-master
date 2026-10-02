import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Unmount what a test rendered, so the next one starts from an empty page.
afterEach(cleanup)
