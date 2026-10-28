import type { Strings } from './en.ts'

// Every string the table reads, in German. The terms are those of the German
// Player's Handbook: Trefferpunkte, Rüstungsklasse, Stufe, W20.
export const de: Strings = {
  connection: {
    connecting: 'verbinde…',
    open: 'verbunden',
    reconnecting: 'Verbindung unterbrochen, verbinde neu…',
    closed: 'getrennt — Seite neu laden',
  },
  send: {
    busy: 'Der Dungeon Master antwortet noch auf die letzte Aktion.',
    failed: 'Die Aktion hat den Dungeon Master nicht erreicht. Bitte noch einmal versuchen.',
  },
  errors: {
    agent_failed:
      'Der Dungeon Master konnte diesen Zug nicht beenden. Bitte die Aktion noch einmal ansagen.',
    authentication_failed:
      'Der Dungeon Master konnte sich nicht anmelden: Claude Code ist auf diesem Rechner nicht ' +
      'angemeldet, oder der API-Schlüssel wurde abgelehnt. Was davon, steht im Terminal des ' +
      'Backends. Danach die Aktion noch einmal ansagen.',
    credential_mismatch:
      'Der Dungeon Master wäre mit einer anderen Anmeldung als der gewählten gelaufen und wurde ' +
      'angehalten, bevor etwas das Modell erreicht hat. Welche, steht im Terminal des Backends.',
    usage_limit_reached:
      'Das Nutzungslimit ist erreicht: das des Abos oder das Ratenlimit des API-Schlüssels. ' +
      'Was davon und was zu tun ist, steht im Terminal des Backends. Danach die Aktion noch ' +
      'einmal ansagen.',
  },
  header: {
    fightAgainst: 'Kampf gegen',
    rollingInitiative: 'Initiative wird gewürfelt',
    round: (round) => `Runde ${round}`,
    partyFixed: 'Die Gruppe steht für diesen Kampf fest',
    enterParty: 'Gruppe eintragen',
    editParty: 'Gruppe bearbeiten',
  },
  action: {
    form: 'Eine Aktion ansagen',
    whoActs: 'Wer handelt?',
    table: 'Alle',
    field: 'Angesagte Aktion',
    placeholder: 'Was tust du? Nenne auch, was du gewürfelt hast.',
    declare: 'Ansagen',
    hint: 'Enter sagt an · Shift+Enter für eine neue Zeile',
  },
  dice: {
    group: 'Würfel',
    die: (sides) => `W${sides}`,
    choose: 'Wurf eintragen',
    face: (die) => `${die}: Was ist gefallen?`,
    modifier: (die, face) => `${die}: ${face} · Modifikator?`,
    backToDice: 'Zurück zu den Würfeln',
    backToFaces: 'Zurück zu den Augenzahlen',
    roll: 'Würfeln',
  },
  narration: {
    label: 'Erzählung',
    empty: 'Die Geschichte beginnt mit dem, was ihr tut.',
  },
  state: {
    label: 'Spielstand',
    party: 'Gruppe',
    noCharacters: 'Noch keine Charaktere.',
    characters: 'Charaktere',
    fight: 'Kampf',
    turnOrder: 'Zugreihenfolge',
    onTurn: 'am Zug',
    opponent: 'Gegner',
    ended: 'Beendet',
    rollingInitiative: 'Initiative wird gewürfelt',
    round: (round) => `Runde ${round}`,
    level: (level) => `Stufe ${level}`,
    armourClass: 'Rüstungsklasse',
    armourClassShort: 'RK',
    hitPoints: 'Trefferpunkte',
    temporary: (points) => `+${points} temp.`,
    hitPointSummary: (current, maximum, temporary) =>
      `${current} von ${maximum} Trefferpunkten` +
      (temporary > 0 ? `, ${temporary} temporäre` : ''),
    conditions: 'Zustände',
  },
  conditions: {
    blinded: 'blind',
    charmed: 'bezaubert',
    deafened: 'taub',
    exhaustion: 'Erschöpfung',
    frightened: 'verängstigt',
    grappled: 'gepackt',
    incapacitated: 'kampfunfähig',
    invisible: 'unsichtbar',
    paralyzed: 'gelähmt',
    petrified: 'versteinert',
    poisoned: 'vergiftet',
    prone: 'liegend',
    restrained: 'festgesetzt',
    stunned: 'betäubt',
    unconscious: 'bewusstlos',
    stable: 'stabil',
    dead: 'tot',
  },
  party: {
    dialog: 'Die Gruppe',
    heading: 'Die Gruppe',
    intro: 'Nur, was das System für den Kampf braucht. Alles andere bleibt auf euren Bögen.',
    columns: {
      name: { heading: 'Name', label: 'Name' },
      character_class: { heading: 'Klasse', label: 'Klasse' },
      level: { heading: 'Stufe', label: 'Stufe' },
      armour_class: { heading: 'RK', label: 'Rüstungsklasse' },
      max_hit_points: { heading: 'Max. TP', label: 'Maximale Trefferpunkte' },
      current_hit_points: { heading: 'Akt. TP', label: 'Aktuelle Trefferpunkte' },
      temporary_hit_points: { heading: 'Temp. TP', label: 'Temporäre Trefferpunkte' },
    },
    maximum: 'max.',
    character: (position) => `Charakter ${position}`,
    remove: (who) => `${who} entfernen`,
    add: 'Charakter hinzufügen',
    currentEmpty: 'Akt. TP leer lassen für volle Trefferpunkte.',
    cancel: 'Abbrechen',
    save: 'Gruppe speichern',
    locked:
      'Der Kampf hat begonnen. Die Gruppe ändern jetzt nur noch die Werkzeuge des Dungeon Masters.',
    notSaved: 'Die Gruppe konnte nicht gespeichert werden.',
    unreachable: 'Das Backend war nicht erreichbar.',
  },
  validation: {
    name: 'Ein Name fehlt.',
    characterClass: 'Eine Klasse fehlt.',
    level: 'Die Stufe ist 1 bis 20.',
    zeroOrMore: 'Eine ganze Zahl, 0 oder mehr.',
    oneOrMore: 'Eine ganze Zahl, 1 oder mehr.',
    currentHitPoints: 'Eine ganze Zahl, 0 oder mehr — oder leer für das Maximum.',
    aboveMaximum: 'Kann nicht mehr als das Maximum sein.',
    sameName: (name) => `Zwei Charaktere heißen ${name}.`,
  },
}
