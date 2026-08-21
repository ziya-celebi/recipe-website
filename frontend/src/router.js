import { createRouter, createWebHistory } from 'vue-router'
import HomePage from './views/HomePage.vue'
import RecipesPage from './views/RecipesPage.vue'
import RecipePage from './views/RecipePage.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomePage },
    { path: '/recipes', name: 'recipes', component: RecipesPage },
    { path: '/recipes/:id', name: 'recipe', component: RecipePage },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})
