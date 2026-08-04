<template>
  <div class="min-h-screen bg-cyber-black text-white overflow-hidden">
    <!-- Top Header Bar -->
    <header class="h-14 glass-panel flex items-center justify-between gap-2 px-3 sm:px-6 border-b border-cyan-500/20">
      <div class="flex min-w-0 items-center gap-2 sm:gap-3">
        <span class="shrink-0 text-xl sm:text-2xl">🛡️</span>
        <h1 class="whitespace-nowrap text-base sm:text-lg font-bold text-cyber-cyan font-sans tracking-wide">反诈指挥中心</h1>
      </div>
      <div class="flex shrink-0 items-center gap-2 sm:gap-4">
        <span class="max-w-20 text-right text-[10px] leading-tight text-gray-400 font-mono sm:max-w-none sm:text-sm sm:leading-normal">{{ currentTime }}</span>
        <button @click="logout" class="whitespace-nowrap text-xs text-gray-400 hover:text-alert-red transition-colors font-mono sm:text-sm">
          [退出]
        </button>
      </div>
    </header>

    <!-- Main Content Grid -->
    <main class="h-[calc(100vh-3.5rem)] overflow-y-auto p-3 sm:p-4 grid grid-cols-1 gap-3 sm:gap-4 lg:grid-cols-12 lg:grid-rows-6 lg:overflow-hidden">

      <!-- Left Column: Terminal + Word Cloud -->
      <section class="min-h-44 glass-panel rounded-xl p-4 flex flex-col lg:col-span-3 lg:row-span-4 lg:min-h-0">
        <h2 class="text-sm text-cyber-cyan font-mono mb-3 flex items-center gap-2">
          <span class="w-2 h-2 bg-safe-green rounded-full animate-pulse"></span>
          AI 实时态势
        </h2>
        <div class="flex-1 overflow-hidden">
          <TerminalStream :logs="aiLogs" />
        </div>
      </section>

      <!-- Center Column: DRI Gauge + Value Shield + Map -->
      <section class="flex flex-col gap-3 sm:gap-4 lg:col-span-6 lg:row-span-4">
        <!-- Stats Row -->
        <div class="grid grid-cols-3 gap-2 sm:gap-4">
          <StatCard title="防护指数" :value="impactStats.total_protection_score || 0" icon="🛡️" color="cyan" />
          <StatCard title="防御评分" :value="driScore.toFixed(1)" icon="📊" color="green" :suffix="'/ 100'" />
          <StatCard title="威胁拦截" :value="impactStats.total_detections" icon="🚫" color="pink" />
        </div>

        <!-- Map -->
        <div class="h-80 glass-panel rounded-xl p-4 lg:h-auto lg:flex-1">
          <h2 class="text-sm text-cyber-cyan font-mono mb-2">威胁态势地图</h2>
          <ThreatMap :points="geoPoints" />
        </div>
      </section>

      <!-- Right Column: Radar + Trend -->
      <section class="flex flex-col gap-3 sm:gap-4 lg:col-span-3 lg:row-span-4">
        <div class="h-72 glass-panel rounded-xl p-4 lg:h-auto lg:flex-1">
          <h2 class="text-sm text-cyber-cyan font-mono mb-2">诈骗类型雷达</h2>
          <FraudRadar :data="fraudTypes" />
        </div>
        <div class="h-72 glass-panel rounded-xl p-4 lg:h-auto lg:flex-1">
          <h2 class="text-sm text-cyber-cyan font-mono mb-2">24小时趋势预测</h2>
          <TrendChart :forecast="forecastData" />
        </div>
      </section>

      <!-- Bottom Row: Daily Report -->
      <section class="min-h-56 glass-panel rounded-xl p-4 flex flex-col lg:col-span-12 lg:row-span-2 lg:min-h-0">
        <h2 class="text-sm text-cyber-cyan font-mono mb-2 shrink-0">📝 AI 每日态势研判</h2>
        <div class="flex-1 overflow-y-auto text-gray-300 text-sm leading-relaxed font-mono markdown-report" v-html="renderedReport"></div>
      </section>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import apiClient from '../api/client'

import StatCard from '../components/StatCard.vue'
import TerminalStream from '../components/TerminalStream.vue'
import ThreatMap from '../components/ThreatMap.vue'
import FraudRadar from '../components/FraudRadar.vue'
import TrendChart from '../components/TrendChart.vue'

const router = useRouter()

// State
const currentTime = ref('')
const impactStats = ref({ total_protection_score: 0, total_tokens_used: 0, total_detections: 0 })
const driScore = ref(75)
const geoPoints = ref([])
const aiLogs = ref([])
const fraudTypes = ref([])
const forecastData = ref([])
const dailyReport = ref('正在加载今日态势分析...')

// Simple Markdown renderer
const renderedReport = computed(() => {
  try {
    return marked.parse(dailyReport.value || '')
  } catch {
    return dailyReport.value
  }
})

let refreshInterval = null

// Helpers
async function fetchData() {
  try {
    const [impact, dri, geo, stream, forecast, report] = await Promise.all([
      apiClient.get('/api/visuals/impact_stats'),
      apiClient.get('/api/visuals/defense_index'),
      apiClient.get('/api/visuals/geo_table'),
      apiClient.get('/api/visuals/ai/live_stream'),
      apiClient.get('/api/visuals/forecast'),
      apiClient.get('/api/visuals/ai/daily_report'),
    ])

    impactStats.value = impact.data
    driScore.value = dri.data.dri_score
    geoPoints.value = geo.data.points
    aiLogs.value = stream.data.stream
    forecastData.value = forecast.data.forecast
    dailyReport.value = report.data.content

    // Fraud types (from stats API)
    const typesRes = await apiClient.get('/api/stats/fraud_types')
    fraudTypes.value = typesRes.data.fraud_types || []
  } catch (e) {
    console.error('Data fetch error:', e)
    if (e.response?.status === 401) {
      logout()
    }
  }
}

function updateTime() {
  currentTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

function logout() {
  localStorage.removeItem('token')
  router.push('/login')
}

onMounted(() => {
  updateTime()
  fetchData()
  refreshInterval = setInterval(() => {
    updateTime()
    fetchData()
  }, 10000) // Refresh every 10s
})

onUnmounted(() => {
  clearInterval(refreshInterval)
})
</script>
