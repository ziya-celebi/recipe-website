// Backend base URL. Set VITE_API_BASE (e.g. in Vercel project env vars)
// to point at the deployed backend; falls back to local dev by default.
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function fetchRecipes(query = '') {
  const url = query
    ? `${API_BASE}/recipes?q=${encodeURIComponent(query)}`
    : `${API_BASE}/recipes`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Network response was not ok')
  return res.json()
}

export async function fetchRecipe(id) {
  const res = await fetch(`${API_BASE}/recipes/${id}`)
  if (res.status === 404) throw new Error('Recipe not found')
  if (!res.ok) throw new Error('Network response was not ok')
  return res.json()
}
