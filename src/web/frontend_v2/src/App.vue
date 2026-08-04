<template>
  <router-view class="min-h-screen bg-cyber-black text-white selection:bg-cyber-blue selection:text-black"></router-view>
</template>

<script setup>
// Root Component
</script>

<style>
/* Global Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
