<template>
  <div class="glass-panel rounded-xl px-2 py-3 sm:p-4 flex flex-col items-center justify-center h-full text-center">
    <div class="text-2xl mb-1 sm:text-4xl sm:mb-2">{{ icon }}</div>
    <p class="whitespace-nowrap text-[10px] text-gray-400 font-mono uppercase tracking-wide sm:text-xs sm:tracking-wider">{{ title }}</p>
    <p class="whitespace-nowrap text-2xl font-bold mt-1 sm:text-3xl" :class="colorClass">
      {{ value }}<span v-if="suffix" class="ml-0.5 text-xs text-gray-400 sm:text-lg">{{ suffix }}</span>
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  value: [String, Number],
  icon: String,
  color: { type: String, default: 'cyan' },
  suffix: String
})

const colorClass = computed(() => {
  const map = {
    cyan: 'text-cyber-cyan',
    green: 'text-safe-green',
    pink: 'text-cyber-pink',
    red: 'text-alert-red'
  }
  return map[props.color] || 'text-white'
})
</script>
