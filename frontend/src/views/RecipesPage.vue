<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchRecipes } from '../api'
import { useFavorites } from '../composables/useFavorites'
import RecipeCard from '../components/RecipeCard.vue'

const recipes = ref([])
const searchQuery = ref('')
const activeTab = ref('all')
const status = ref('Loading recipes...')

const { isFavorite, favoritesCount } = useFavorites()

const filteredRecipes = computed(() => {
  let list = recipes.value
  if (activeTab.value === 'favorites') {
    list = list.filter((r) => isFavorite(r.id))
  }
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return list
  return list.filter((recipe) => {
    const titleMatch = recipe.title?.toLowerCase().includes(q)
    const descMatch = recipe.description?.toLowerCase().includes(q)
    const ingMatch = recipe.ingredients?.some((ing) =>
      ing.toLowerCase().includes(q)
    )
    return titleMatch || descMatch || ingMatch
  })
})

function clearSearch() {
  searchQuery.value = ''
}

onMounted(async () => {
  try {
    recipes.value = await fetchRecipes()
    status.value = ''
  } catch (err) {
    status.value = 'Could not load recipes: ' + err.message
  }
})
</script>

<template>
  <main class="section">
    <div class="section-heading">
      <h1>All recipes</h1>
    </div>

    <div class="recipes-toolbar">
      <div class="filter-tabs" role="tablist" aria-label="Recipe filters">
        <button
          type="button"
          class="tab-btn"
          :class="{ 'is-active': activeTab === 'all' }"
          role="tab"
          :aria-selected="activeTab === 'all'"
          @click="activeTab = 'all'"
        >
          All recipes ({{ recipes.length }})
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ 'is-active': activeTab === 'favorites' }"
          role="tab"
          :aria-selected="activeTab === 'favorites'"
          @click="activeTab = 'favorites'"
        >
          ❤️ Saved ({{ favoritesCount }})
        </button>
      </div>

      <div class="search-bar">
        <div class="search-input-wrapper">
          <svg
            class="search-icon"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            v-model="searchQuery"
            type="search"
            :placeholder="activeTab === 'favorites' ? 'Search saved recipes...' : 'Search by recipe name or ingredient...'"
            aria-label="Search recipes"
            class="search-input"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="search-clear-btn"
            aria-label="Clear search"
            @click="clearSearch"
          >
            ✕
          </button>
        </div>
        <p v-if="searchQuery && !status" class="search-meta">
          Showing {{ filteredRecipes.length }} of {{ activeTab === 'favorites' ? favoritesCount : recipes.length }} {{ filteredRecipes.length === 1 ? 'recipe' : 'recipes' }}
        </p>
      </div>
    </div>

    <p v-if="status" class="status">{{ status }}</p>

    <!-- Empty state when no recipes exist yet -->
    <div v-else-if="recipes.length === 0" class="empty-state">
      <p class="empty-title">No recipes yet</p>
      <p class="empty-text">Recipes added from the admin panel show up here.</p>
    </div>

    <!-- Empty state for empty saved list -->
    <div
      v-else-if="activeTab === 'favorites' && favoritesCount === 0"
      class="empty-state"
    >
      <p class="empty-title">No saved recipes yet</p>
      <p class="empty-text">
        Click the heart icon (❤️) on any recipe card to save it for quick access here.
      </p>
      <button type="button" class="button" @click="activeTab = 'all'">
        Browse all recipes
      </button>
    </div>

    <!-- Empty state for search query with zero matches -->
    <div v-else-if="filteredRecipes.length === 0" class="empty-state">
      <p class="empty-title">No recipes found</p>
      <p class="empty-text">
        We couldn't find any recipes matching "<strong>{{ searchQuery }}</strong>"{{ activeTab === 'favorites' ? ' in your saved collection' : '' }}.
      </p>
      <button type="button" class="button" @click="clearSearch">
        Clear search
      </button>
    </div>

    <ul v-else class="recipe-grid">
      <RecipeCard
        v-for="recipe in filteredRecipes"
        :key="recipe.id"
        :recipe="recipe"
      />
    </ul>
  </main>
</template>
