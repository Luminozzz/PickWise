const BASE = import.meta.env.VITE_API_URL || ''

export async function fetchItems() {
  const res = await fetch(`${BASE}/api/v1/items`)
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function fetchRecommendations(answers) {
  const res = await fetch(`${BASE}/api/v1/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(answers),
  })
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function createProfile(answers) {
  const res = await fetch(`${BASE}/api/v1/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers }),
  })
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  return res.json()
}

export async function getProfile(id) {
  const res = await fetch(`${BASE}/api/v1/profile/${id}`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  return res.json()
}

export async function updateProfile(id, answers) {
  const res = await fetch(`${BASE}/api/v1/profile/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers }),
  })
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  return res.json()
}