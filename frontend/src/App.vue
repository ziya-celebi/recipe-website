<script setup>
</script>

<template>
  <div class="site">
    <header class="site-header">
      <RouterLink class="logo" to="/">Fun recipes</RouterLink>
      <nav class="nav-links">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/recipes">Recipes</RouterLink>
      </nav>
    </header>
    <RouterView />
  </div>
</template>
