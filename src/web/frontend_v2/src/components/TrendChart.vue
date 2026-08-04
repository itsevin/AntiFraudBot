<template>
  <div class="h-full w-full">
    <v-chart :option="chartOption" autoresize class="w-full h-full" />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  forecast: { type: Array, default: () => [] }
})

const chartOption = computed(() => ({
  backgroundColor: 'transparent',
  grid: { left: 40, right: 20, top: 20, bottom: 30 },
  xAxis: {
    type: 'category',
    data: props.forecast.map(d => d.time),
    axisLine: { lineStyle: { color: '#1e3a5f' } },
    axisLabel: { color: '#6b7280', fontSize: 10 }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    splitLine: { lineStyle: { color: '#1e3a5f', type: 'dashed' } },
    axisLabel: { color: '#6b7280', fontSize: 10 }
  },
  series: [{
    type: 'line',
    data: props.forecast.map(d => d.value),
    smooth: true,
    lineStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [
          { offset: 0, color: '#00f3ff' },
          { offset: 1, color: '#ff00ff' }
        ]
      },
      width: 2
    },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(0,243,255,0.3)' },
          { offset: 1, color: 'rgba(0,243,255,0)' }
        ]
      }
    },
    symbol: 'none'
  }],
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(10,25,47,0.9)',
    borderColor: '#00f3ff',
    textStyle: { color: '#fff' }
  }
}))
</script>
