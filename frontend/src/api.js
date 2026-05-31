const BASE = import.meta.env.VITE_API_URL || ''

export async function fetchItems() {
  const res = await fetch(`${BASE}/api/v1/items`)
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}