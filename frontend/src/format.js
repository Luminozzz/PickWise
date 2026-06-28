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

export function buildTags(item) {
  const tags = []
  if (typeof item.weight === 'number' && item.weight > 0) {
    tags.push(`${item.weight} g`)
  }
  const conn = connectivityLabel(item.connectivity)
  if (conn) tags.push(conn)
  if (item.max_polling_rate) tags.push(`${item.max_polling_rate} Hz`)
  if (item.max_DPI) tags.push(`${item.max_DPI.toLocaleString()} DPI`)
  return tags
}
