export function connectivityLabel(raw) {
  if (!raw) return null
  const v = String(raw).toLowerCase()
  const wireless = v.includes('wireless')
  const wired = v.includes('wired')
  if (wireless && wired) return 'Wired + Wireless'
  if (wireless) return 'Wireless'
  if (wired) return 'Wired'
  return null
}

export function buildDescription(item) {
  if (item.description) return item.description
  const parts = []
  if (typeof item.weight === 'number' && item.weight > 0 && item.weight <= 60) {
    parts.push('Lightweight')
  }
  const conn = connectivityLabel(item.connectivity)
  if (conn) parts.push(conn.toLowerCase())
  parts.push('gaming mouse')
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