<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { fetchRecipe } from '../api'
import { useFavorites } from '../composables/useFavorites'

const route = useRoute()
const recipe = ref(null)
const status = ref('Loading recipe...')
const imgError = ref(false)
const checkedIngredients = ref(new Set())
const completedSteps = ref(new Set())
const copyStatus = ref('')
const { isFavorite, toggleFavorite } = useFavorites()

function toggleIngredient(item) {
  if (checkedIngredients.value.has(item)) {
    checkedIngredients.value.delete(item)
  } else {
    checkedIngredients.value.add(item)
  }
}

function toggleStep(idx) {
  if (completedSteps.value.has(idx)) {
    completedSteps.value.delete(idx)
  } else {
    completedSteps.value.add(idx)
  }
}

function resetChecklist() {
  checkedIngredients.value.clear()
  completedSteps.value.clear()
}

async function copyIngredients() {
  if (!recipe.value?.ingredients?.length) return
  const text = `${recipe.value.title} - Ingredients:\n` +
    recipe.value.ingredients.map((item) => `• ${item}`).join('\n')
  try {
    await navigator.clipboard.writeText(text)
    copyStatus.value = '✓ Copied!'
    setTimeout(() => {
      copyStatus.value = ''
    }, 2000)
  } catch {
    copyStatus.value = 'Error copying'
    setTimeout(() => {
      copyStatus.value = ''
    }, 2000)
  }
}

watch(
  () => route.params.id,
  async (id) => {
    recipe.value = null
    status.value = 'Loading recipe...'
    imgError.value = false
    checkedIngredients.value.clear()
    completedSteps.value.clear()
    copyStatus.value = ''
    try {
      recipe.value = await fetchRecipe(id)
      status.value = ''
    } catch (err) {
      status.value = err.message
    }
  },
  { immediate: true },
)
</script>

<template>
  <main class="section recipe-detail">
    <div class="recipe-top-bar">
      <RouterLink class="back" to="/recipes">← All recipes</RouterLink>
      <button
        v-if="recipe"
        type="button"
        class="fav-toggle-btn"
        :class="{ 'is-active': isFavorite(recipe.id) }"
        :aria-label="isFavorite(recipe.id) ? 'Remove from saved' : 'Save recipe'"
        @click="toggleFavorite(recipe.id)"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
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
        <span>{{ isFavorite(recipe.id) ? 'Saved' : 'Save recipe' }}</span>
      </button>
    </div>
    <p v-if="status" class="status">{{ status }}</p>
    <article v-else-if="recipe">
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
      </div>
      <h1 class="recipe-title">{{ recipe.title }}</h1>
      <p class="recipe-description">{{ recipe.description }}</p>

      <div class="recipe-block">
        <div class="recipe-section-header">
          <h2>Ingredients</h2>
          <div class="recipe-actions">
            <button
              type="button"
              class="copy-btn"
              :class="{ 'copy-btn-success': copyStatus === '✓ Copied!' }"
              @click="copyIngredients"
            >
              <svg
                v-if="copyStatus !== '✓ Copied!'"
                xmlns="http://www.w3.org/2000/svg"
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
                <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
              </svg>
              <span>{{ copyStatus || 'Copy ingredients' }}</span>
            </button>
            <button
              v-if="checkedIngredients.size > 0 || completedSteps.size > 0"
              type="button"
              class="reset-btn"
              @click="resetChecklist"
            >
              Reset checklist
            </button>
          </div>
        </div>
        <p class="section-hint">Check off ingredients as you prepare them:</p>
        <ul class="checklist">
          <li
            v-for="item in recipe.ingredients"
            :key="item"
            class="checklist-item"
            :class="{ 'item-checked': checkedIngredients.has(item) }"
            @click="toggleIngredient(item)"
          >
            <input
              type="checkbox"
              :checked="checkedIngredients.has(item)"
              :aria-label="item"
              @click.stop="toggleIngredient(item)"
            />
            <span>{{ item }}</span>
          </li>
        </ul>
      </div>

      <div class="recipe-block">
        <div class="recipe-section-header">
          <h2>Steps</h2>
          <span v-if="completedSteps.size > 0" class="step-progress-badge">
            {{ completedSteps.size }} of {{ recipe.steps.length }} completed
          </span>
        </div>
        <p class="section-hint">Tap each step to track your cooking progress:</p>
        <ol class="step-list">
          <li
            v-for="(step, idx) in recipe.steps"
            :key="idx"
            class="step-item"
            :class="{ 'step-done': completedSteps.has(idx) }"
            @click="toggleStep(idx)"
          >
            <span class="step-number">{{ idx + 1 }}</span>
            <div class="step-content">
              <p>{{ step }}</p>
            </div>
          </li>
        </ol>
      </div>
    </article>
  </main>
</template>
