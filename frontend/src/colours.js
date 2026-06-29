// Map a mouse colour name (possibly compound, e.g. "Quartz Pink") to a hex
// swatch. Returns null for names we can't place — the UI renders those as a
// neutral "unknown" swatch. Order matters: the first keyword match wins.
const COLOUR_RULES = [
  [/black|obsidian|midnight|carbon|stealth|onyx|noir/i, '#1b1b22'],
  [/white|mercury|frost|arctic|snow|pearl/i, '#ececf0'],
  [/pink|quartz|rose|blush|magenta/i, '#f0a6c4'],
  [/red|crimson|scarlet|ruby/i, '#e2515f'],
  [/orange|amber|sunset/i, '#f0a05a'],
  [/yellow|gold/i, '#f2cf63'],
  [/green|mint|emerald|lime|jade/i, '#5fcaa0'],
  [/blue|cyan|azure|sky|navy|cobalt/i, '#5cb8ff'],
  [/purple|violet|lilac|lavender|amethyst/i, '#9a6cf0'],
  [/silver|platinum|chrome/i, '#c7ccd6'],
  [/grey|gray|graphite|slate|gunmetal|ash/i, '#8b8f9e'],
  [/brown|bronze|copper|tan|sand/i, '#b07a4e'],
]

export function colourToHex(name) {
  if (!name) return null
  for (const [re, hex] of COLOUR_RULES) {
    if (re.test(name)) return hex
  }
  return null
}
