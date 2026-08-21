import { ref, computed } from 'vue'

const STORAGE_KEY = 'recipe_website_favorites'

function loadFavorites() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return new Set()
    const parsed = JSON.parse(raw)
    return new Set(Array.isArray(parsed) ? parsed : [])
  } catch {
    return new Set()
  }
}

function saveFavorites(favoritesSet) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...favoritesSet]))
  } catch {
    // Ignore storage quota or disabled localStorage errors
  }
}

// Shared singleton state across components
const favorites = ref(loadFavorites())

export function useFavorites() {
  function isFavorite(id) {
    if (id === undefined || id === null) return false
    return favorites.value.has(Number(id))
  }

  function toggleFavorite(id) {
    if (id === undefined || id === null) return
    const numId = Number(id)
    const next = new Set(favorites.value)
    if (next.has(numId)) {
      next.delete(numId)
    } else {
      next.add(numId)
    }
    favorites.value = next
    saveFavorites(next)
  }

  const favoritesCount = computed(() => favorites.value.size)

  return {
    favorites,
    favoritesCount,
    isFavorite,
    toggleFavorite,
  }
}

