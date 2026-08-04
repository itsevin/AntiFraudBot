<template>
  <div class="h-full w-full flex items-center justify-center">
    <v-chart :option="chartOption" autoresize style="width: 100%; height: 100%; min-height: 300px;" />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: { type: Array, default: () => [] }
})

const chartOption = computed(() => ({
  backgroundColor: 'transparent',
  geo: {
    map: 'china',
    roam: true,  // 允许缩放和拖拽
    zoom: 1.2,   // 初始放大倍数
    center: [105, 36],  // 中国地理中心
    itemStyle: {
      areaColor: '#0a192f',
      borderColor: '#1e3a5f'
    },
    emphasis: {
      itemStyle: {
        areaColor: '#1e3a5f'
      }
    },
    label: { show: false }
  },
  series: [
    {
      type: 'effectScatter',
      coordinateSystem: 'geo',
      data: props.points.map(p => ({
        name: p.name,
        value: p.value,
        itemStyle: {
          color: p.status === 'alert' ? '#ff2a2a' : '#00f3ff'
        }
      })),
      symbolSize: val => Math.max(10, Math.min(30, val[2] / 5)),
      rippleEffect: {
        brushType: 'stroke',
        scale: 3
      },
      label: { show: false }
    }
  ]
}))
</script>
