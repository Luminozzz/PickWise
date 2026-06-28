// Turn the connectivity object ({ bluetooth, dongle, wired }) into a label.
export function connectivityLabel(conn) {
  if (!conn) return null
  const wireless = conn.bluetooth || conn.dongle
  const wired = conn.wired
  if (wireless && wired) return 'Wired + Wireless'
  if (wireless) return 'Wireless'
  if (wired) return 'Wired'
  return null
}

// Abbreviate a count of 1000 or more to a compact "1.5k" label (one decimal,
// with a trailing ".0" dropped: 1000 -> "1k", 1500 -> "1.5k", 12345 -> "12.3k").
// Smaller counts stay a plain grouped number.
export function formatCount(n) {
  if (n == null) return null
  const num = Number(n)
  if (!Number.isFinite(num)) return null
  if (num < 1000) return num.toLocaleString()
  const text = (num / 1000).toFixed(1).replace(/\.0$/, '')
  return `${text}k`
}

export function formatPrice(price) {
  if (!price || price.amount == null) return null
  const currency = price.currency || '$'
  const amount = Number(price.amount)
  const value = Number.isInteger(amount) ? amount.toString() : amount.toFixed(2)
  return `${currency}${value}`
}

export function buildDescription(item) {
  if (item.description) return item.description
  const parts = []
  if (typeof item.weight === 'number' && item.weight > 0 && item.weight <= 70) {
    parts.push('Lightweight')
  }
  const conn = connectivityLabel(item.connectivity)
  if (conn) parts.push(conn.toLowerCase())
  parts.push(item.gaming ? 'gaming mouse' : 'mouse')
  const sentence = parts.join(' ')
  return sentence.charAt(0).toUpperCase() + sentence.slice(1)
}

// Candidate spec tags. `base` is the general-public importance (used when the
// questionnaire hasn't been filled); the questionnaire raises the ones the user
// signalled they care about. Answers are keyed by question id.
const TAG_DEFS = [
  { key: 'weight', base: 3.0, label: (it) => (it.weight ? `${it.weight} g` : null) },
  { key: 'connectivity', base: 2.8, label: (it) => connectivityLabel(it.connectivity) },
  { key: 'dpi', base: 2.5, label: (it) => (it.max_DPI ? `${it.max_DPI.toLocaleString()} DPI` : null) },
  { key: 'polling', base: 1.5, label: (it) => (it.max_polling_rate ? `${it.max_polling_rate} Hz` : null) },
  { key: 'buttons', base: 1.2, label: (it) => (it.number_of_buttons ? `${it.number_of_buttons} buttons` : null) },
  { key: 'battery', base: 1.0, label: (it) => (it.max_battery_life ? `${it.max_battery_life} h battery` : null) },
]

function tagBoosts(answers) {
  const a = answers || {}
  const b = { weight: 0, connectivity: 0, dpi: 0, polling: 0, buttons: 0, battery: 0 }
  const travels = a[3] === 'daily' || a[3] === 'weekly'

  if (a[6] === 'high') b.weight += 4
  else if (a[6] === 'medium') b.weight += 2
  if (a[5] === 'fps') b.weight += 3
  if (a[8] === 'competitive') b.weight += 3
  if (travels) b.weight += 2

  if (a[15] != null) b.connectivity += 3
  if (a[10] === 'mobile') b.connectivity += 2
  if (travels) b.connectivity += 2

  if (a[20] === 'high') b.dpi += 4
  else if (a[20] === 'medium') b.dpi += 2
  if (a[5] === 'fps') b.dpi += 3
  if (a[8] === 'competitive') b.dpi += 2
  if (a[5] != null) b.dpi += 1

  if (a[20] === 'high') b.polling += 3
  else if (a[20] === 'medium') b.polling += 1
  if (a[8] === 'competitive') b.polling += 3
  if (a[5] === 'rts' || a[5] === 'moba') b.polling += 2

  if (a[4] === 'yes') b.buttons += 3
  if (a[9] === 'yes') b.buttons += 3
  else if (a[9] === 'sometimes') b.buttons += 1
  if (a[5] === 'mmorpg') b.buttons += 4

  if (travels) b.battery += 3
  if (a[15] === 'yes' || a[15] === 'preferably') b.battery += 2
  if (typeof a[11] === 'number' && a[11] >= 8) b.battery += 2

  return b
}

// Spec tags ordered by importance to the user (their questionnaire answers), or
// by general-public defaults when no answers are given. Only tags the item has
// a value for are returned. Callers slice to the count they want to show.
export function buildTags(item, answers) {
  const boost = tagBoosts(answers)
  return TAG_DEFS.map((def) => ({ label: def.label(item), score: def.base + (boost[def.key] || 0) }))
    .filter((t) => t.label)
    .sort((a, b) => b.score - a.score)
    .map((t) => t.label)
}
