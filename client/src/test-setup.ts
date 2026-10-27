import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Unmount what a test rendered, so the next one starts from an empty page.
afterEach(cleanup)

// jsdom has dialogs but no modal ones. Opened as a modal, a dialog is simply
// open here: what a test can see of it is the same.
HTMLDialogElement.prototype.showModal ??= function (this: HTMLDialogElement) {
  this.open = true
}
