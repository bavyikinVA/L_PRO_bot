<script setup lang="ts">
import headerImage from './assets/header.png';
</script>

<template>
  <div class="px-2 pt-4">
  <header
      class="w-full h-72 bg-cover bg-center bg-no-repeat rounded-3xl overflow-hidden"
      :style="{ backgroundImage: `url(${headerImage})` }"
  />
  </div>

  <main class="container mx-auto p-4">
    <router-view />
  </main>
</template>
<style scoped></style>