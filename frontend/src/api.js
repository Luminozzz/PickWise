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

// Single product, scored against the user's answers (empty {} = no questionnaire).
export async function fetchProduct(id, answers) {
  const res = await fetch(`${BASE}/api/v1/product/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(answers || {}),
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  return res.json()
}

// Several products side by side: spec rows aligned across every mouse and
// ordered by what matters to this user (default order with empty answers).
export async function fetchCompare(ids, answers) {
  const res = await fetch(`${BASE}/api/v1/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids: ids || [], answers: answers || {} }),
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  return res.json()
}