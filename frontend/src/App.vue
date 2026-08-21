<script setup>
import { ref, onMounted } from 'vue'

const message = ref('Loading...')

onMounted(() => {
  fetch('http://localhost:8000/')
    .then(res => {
      if (!res.ok) throw new Error('Network response was not ok')
      return res.json()
    })
    .then(data => {
      message.value = data.message
    })
    .catch(err => {
      message.value = 'Error: ' + err.message
    })
})
</script>

<template>
  <div style="text-align: center; margin-top: 50px;">
    <h1>FastAPI + Vue</h1>
    <p>Backend says: {{ message }}</p>
  </div>
</template>