<script setup>
import { ref, onMounted } from 'vue'
import { fetchRecipes } from '../api'
import RecipeCard from '../components/RecipeCard.vue'

const recipes = ref([])
const status = ref('Loading recipes...')

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
  <main>
    <section class="hero-banner">
      <img src="/hero-kitchen.jpg" alt="" />
      <div class="hero-copy">
        <p class="eyebrow">Weeknight cooking, kept simple</p>
        <h1>Recipes worth making twice</h1>
        <p>
          Short ingredient lists, clear steps, and food that actually looks like
          dinner.
        </p>
        <RouterLink class="button" to="/recipes">Browse recipes</RouterLink>
      </div>
    </section>

    <section class="section">
      <div class="section-heading">
        <h2>Featured</h2>
        <RouterLink to="/recipes">See all</RouterLink>
      </div>
      <p v-if="status" class="status">{{ status }}</p>
      <div v-else-if="recipes.length === 0" class="empty-state">
        <p class="empty-title">No recipes yet</p>
        <p class="empty-text">Recipes added from the admin panel show up here.</p>
      </div>
      <ul v-else class="recipe-grid">
        <RecipeCard
          v-for="recipe in recipes"
          :key="recipe.id"
          :recipe="recipe"
        />
      </ul>
    </section>
  </main>
</template>
