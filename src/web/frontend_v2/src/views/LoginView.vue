<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-cyber-black via-cyber-dark to-cyber-black">
    <!-- Animated Background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute w-[500px] h-[500px] bg-cyber-blue/5 rounded-full blur-3xl -top-32 -left-32 animate-pulse"></div>
      <div class="absolute w-[400px] h-[400px] bg-cyber-pink/5 rounded-full blur-3xl -bottom-20 -right-20 animate-pulse-fast"></div>
    </div>

    <!-- Login Card -->
    <div class="glass-panel rounded-2xl p-8 w-full max-w-md relative z-10">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="text-5xl mb-4">🛡️</div>
        <h1 class="text-2xl font-bold text-cyber-cyan font-sans tracking-wider">反诈大屏</h1>
        <p class="text-gray-400 text-sm mt-1 font-mono">指挥中心登录</p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label class="block text-sm text-gray-400 mb-2 font-mono">用户名</label>
          <input
            v-model="username"
            type="text"
            class="w-full bg-cyber-black/50 border border-cyan-500/30 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyber-cyan focus:ring-1 focus:ring-cyber-cyan/50 transition-all font-mono"
            placeholder="请输入用户名"
          />
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-2 font-mono">密码</label>
          <input
            v-model="password"
            type="password"
            class="w-full bg-cyber-black/50 border border-cyan-500/30 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyber-cyan focus:ring-1 focus:ring-cyber-cyan/50 transition-all font-mono"
            placeholder="••••••••"
          />
        </div>

        <p v-if="error" class="text-alert-red text-sm font-mono">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 bg-gradient-to-r from-cyber-blue to-cyber-cyan text-black font-bold rounded-lg hover:shadow-[0_0_20px_rgba(0,243,255,0.5)] transition-all duration-300 disabled:opacity-50"
        >
          <span v-if="loading">正在验证...</span>
          <span v-else>进入指挥中心</span>
        </button>
      </form>

      <!-- Footer -->
      <p class="text-center text-gray-500 text-xs mt-6 font-mono">
        安全认证 v2.0 | JWT 保护
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const API_BASE = import.meta.env.VITE_API_BASE || ''

async function handleLogin() {
  loading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const response = await axios.post(`${API_BASE}/api/auth/login`, formData)
    localStorage.setItem('token', response.data.access_token)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || '认证失败'
  } finally {
    loading.value = false
  }
}
</script>
