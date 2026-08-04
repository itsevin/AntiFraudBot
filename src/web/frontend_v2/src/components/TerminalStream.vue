<template>
  <div class="h-full overflow-y-auto terminal-text text-safe-green text-xs leading-relaxed">
    <div v-for="log in logs" :key="log.id" class="mb-2 border-b border-green-900/30 pb-2">
      <span class="text-gray-500">[{{ log.time }}]</span>
      <span :class="riskClass(log.risk)" class="ml-2">{{ log.risk }}</span>
      <span class="text-cyber-cyan ml-2">{{ log.type || '分析中' }}</span>
      <p class="text-gray-400 mt-1 pl-4">> {{ log.trace }}</p>
    </div>
    <div v-if="logs.length === 0" class="text-gray-500 animate-pulse">
      > 正在等待威胁信号...
    </div>
  </div>
</template>

<script setup>
defineProps({
  logs: { type: Array, default: () => [] }
})

function riskClass(risk) {
  if (risk === '高危') return 'text-alert-red'
  if (risk === '中危') return 'text-yellow-400'
  return 'text-safe-green'
}
</script>
