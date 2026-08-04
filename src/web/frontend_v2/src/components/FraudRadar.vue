<template>
  <div class="h-full w-full">
    <v-chart :option="chartOption" autoresize class="w-full h-full" />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartOption = computed(() => {
  const indicators = [
    { name: '杀猪盘', max: 100 },
    { name: '刷单诈骗', max: 100 },
    { name: '冒充客服', max: 100 },
    { name: '冒充公检法', max: 100 },
    { name: '投资理财', max: 100 },
    { name: '其他类型', max: 100 }
  ]

  // Map fraud_types data to radar values
  const values = indicators.map(ind => {
    const found = props.data.find(d => d.type && d.type.includes(ind.name.slice(0, 2)))
    return found ? Math.min(100, found.count * 10) : 0
  })

  return {
    backgroundColor: 'transparent',
    radar: {
      indicator: indicators,
      axisName: { color: '#6b7280', fontSize: 10 },
      splitArea: { areaStyle: { color: ['rgba(0,243,255,0.02)', 'rgba(0,243,255,0.05)'] } },
      axisLine: { lineStyle: { color: '#1e3a5f' } },
      splitLine: { lineStyle: { color: '#1e3a5f' } }
    },
    series: [{
      type: 'radar',
      data: [{ value: values, name: '威胁等级' }],
      areaStyle: { color: 'rgba(0,243,255,0.2)' },
      lineStyle: { color: '#00f3ff' },
      itemStyle: { color: '#00f3ff' }
    }]
  }
})
</script>
