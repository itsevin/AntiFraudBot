import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

// ECharts
import ECharts from 'vue-echarts'
import { use, registerMap } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { EffectScatterChart, LineChart, RadarChart } from 'echarts/charts'
import { GeoComponent, GridComponent, RadarComponent, TooltipComponent } from 'echarts/components'

use([
    CanvasRenderer,
    LineChart,
    EffectScatterChart,
    RadarChart,
    GridComponent,
    TooltipComponent,
    GeoComponent,
    RadarComponent,
])

import chinaMap from './assets/china.json'
registerMap('china', chinaMap)

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.component('v-chart', ECharts)

app.mount('#app')
