import type { Character, TableError } from '../contract/index.ts'

type Condition = Character['conditions'][number]

// Every string the table reads, in English. Its shape is the dictionary's
// type: the German one must have exactly these keys, no more and no fewer.
export const en = {
  connection: {
    connecting: 'connecting…',
    open: 'connected',
    reconnecting: 'connection lost, reconnecting…',
    closed: 'disconnected — reload the page',
  },
  send: {
    busy: 'The dungeon master is still answering the last action.',
    failed: 'The action did not reach the dungeon master. Try again.',
  },
  // A failed turn, by its error code. The event's own message is English and
  // technical; the backend's terminal has it (docs/event-contract.md).
  errors: {
    agent_failed: 'The dungeon master could not finish this turn. Declare the action again.',
    authentication_failed:
      'The dungeon master could not log in: Claude Code is not logged in on this machine, or ' +
      'the API key was rejected. The backend’s terminal says which. Then declare the action again.',
    credential_mismatch:
      'The dungeon master would have run on another credential than the chosen one, so it was ' +
      'stopped before anything reached the model. The backend’s terminal says which.',
    usage_limit_reached:
      'The usage limit is reached: the subscription’s, or the API key’s rate limit. The ' +
      'backend’s terminal says which, and what to do. Then declare the action again.',
  } satisfies Record<TableError['code'], string>,
  header: {
    fightAgainst: 'Fight against',
    rollingInitiative: 'rolling initiative',
    round: (round: number) => `round ${round}`,
    partyFixed: 'The party is fixed for this encounter',
    enterParty: 'Enter the party',
    editParty: 'Edit the party',
  },
  action: {
    form: 'Declare an action',
    whoActs: 'Who acts?',
    table: 'The table',
    field: 'Declared action',
    placeholder: 'What do you do? Include what you rolled.',
    declare: 'Declare',
    hint: 'Enter declares · Shift+Enter for a new line',
  },
  dice: {
    group: 'Dice',
    die: (sides: number) => `d${sides}`,
    choose: 'Enter a roll',
    face: (die: string) => `${die}: what came up?`,
    modifier: (die: string, face: number) => `${die}: ${face} · modifier?`,
    backToDice: 'Back to the dice',
    backToFaces: 'Back to the faces',
    roll: 'Roll',
  },
  narration: {
    label: 'Narration',
    empty: 'The story begins with what you do.',
  },
  state: {
    label: 'State',
    party: 'Party',
    noCharacters: 'No characters yet.',
    characters: 'Characters',
    fight: 'Fight',
    turnOrder: 'Turn order',
    onTurn: 'on turn',
    opponent: 'opponent',
    ended: 'Ended',
    rollingInitiative: 'Rolling initiative',
    round: (round: number) => `Round ${round}`,
    level: (level: number) => `level ${level}`,
    armourClass: 'Armour class',
    armourClassShort: 'AC',
    hitPoints: 'Hit points',
    temporary: (points: number) => `+${points} temp.`,
    hitPointSummary: (current: number, maximum: number, temporary: number) =>
      `${current} of ${maximum} hit points` + (temporary > 0 ? `, ${temporary} temporary` : ''),
    conditions: 'Conditions',
  },
  conditions: {
    blinded: 'blinded',
    charmed: 'charmed',
    deafened: 'deafened',
    exhaustion: 'exhaustion',
    frightened: 'frightened',
    grappled: 'grappled',
    incapacitated: 'incapacitated',
    invisible: 'invisible',
    paralyzed: 'paralyzed',
    petrified: 'petrified',
    poisoned: 'poisoned',
    prone: 'prone',
    restrained: 'restrained',
    stunned: 'stunned',
    unconscious: 'unconscious',
    stable: 'stable',
    dead: 'dead',
  } satisfies Record<Condition, string>,
  party: {
    dialog: 'The party',
    heading: 'The party',
    intro: 'Only what the system needs for the fight. Everything else stays on your sheets.',
    // Column headings above the grid, and the full name of each input.
    columns: {
      name: { heading: 'Name', label: 'Name' },
      character_class: { heading: 'Class', label: 'Class' },
      level: { heading: 'Level', label: 'Level' },
      armour_class: { heading: 'AC', label: 'Armour class' },
      max_hit_points: { heading: 'Max HP', label: 'Maximum hit points' },
      current_hit_points: { heading: 'Current HP', label: 'Current hit points' },
      temporary_hit_points: { heading: 'Temp HP', label: 'Temporary hit points' },
    },
    maximum: 'max',
    character: (position: number) => `Character ${position}`,
    remove: (who: string) => `Remove ${who}`,
    add: 'Add a character',
    currentEmpty: 'Leave current HP empty for full hit points.',
    cancel: 'Cancel',
    save: 'Save the party',
    locked: 'The encounter has started. Only the dungeon master’s tools change the party now.',
    notSaved: 'The party could not be saved.',
    unreachable: 'The backend could not be reached.',
    saveFile: 'Save as file',
    loadFile: 'Load from file',
    fileStem: 'party',
    // Why a file was not loaded. The form keeps what it had.
    file: {
      unreadable: 'The file could not be read.',
      notJson: 'This is not a party file: it is not JSON.',
      notParty: 'This is not a party file: it has no list of characters.',
      notCharacter: 'not a character.',
      unknownField: (field: string) => `“${field}” is not a field of a party file.`,
      text: (label: string) => `${label} must be text.`,
      number: (label: string) => `${label} must be a whole number.`,
    },
  },
  validation: {
    name: 'A name is needed.',
    characterClass: 'A class is needed.',
    level: 'Level is 1 to 20.',
    zeroOrMore: 'A whole number, 0 or more.',
    oneOrMore: 'A whole number, 1 or more.',
    currentHitPoints: 'A whole number, 0 or more — or empty for the maximum.',
    aboveMaximum: 'Cannot be more than the maximum.',
    sameName: (name: string) => `Two characters are called ${name}.`,
  },
}

export type Strings = typeof en
