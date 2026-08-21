<script setup>
import { ref } from 'vue'
import { useFavorites } from '../composables/useFavorites'

defineProps({
  recipe: {
    type: Object,
    required: true,
  },
})

const imgError = ref(false)
const { isFavorite, toggleFavorite } = useFavorites()
</script>

<template>
  <li>
    <RouterLink class="recipe-card" :to="`/recipes/${recipe.id}`">
      <div class="recipe-photo">
        <img
          v-if="recipe.image && !imgError"
          :src="recipe.image"
          :alt="recipe.title"
          @error="imgError = true"
        />
        <div v-else class="photo-placeholder">
          <span>🍳 Photo coming soon</span>
        </div>
        <button
          type="button"
          class="card-fav-btn"
          :class="{ 'is-active': isFavorite(recipe.id) }"
          :aria-label="isFavorite(recipe.id) ? 'Remove from saved' : 'Save recipe'"
          @click.prevent.stop="toggleFavorite(recipe.id)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            :fill="isFavorite(recipe.id) ? 'currentColor' : 'none'"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
          </svg>
        </button>
      </div>
      <div class="recipe-card-body">
        <h2>{{ recipe.title }}</h2>
        <p>{{ recipe.description }}</p>
      </div>
    </RouterLink>
  </li>
</template>
