<template>
  <div v-if="!isLoggedIn">
    <router-view />
  </div>
  <div v-else class="bg-gray-100 font-sans text-gray-800 h-screen flex overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-64 bg-slate-900 text-white flex flex-col shadow-lg">
      <div class="h-16 flex items-center justify-center border-b border-slate-700">
        <h1 class="text-xl font-bold tracking-wider">
          <i class="fa-solid fa-car-burst mr-2"></i>FuzzTest
        </h1>
      </div>

      <nav class="flex-1 py-6 space-y-2 px-3">
        <router-link 
          to="/" 
          class="nav-item flex items-center space-x-3 px-4 py-3 rounded-lg transition"
          :class="isActive('/') ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <i class="fa-solid fa-gauge-high w-5 text-center"></i>
          <span>仪表盘</span>
        </router-link>
        <router-link 
          to="/analysis" 
          class="nav-item flex items-center space-x-3 px-4 py-3 rounded-lg transition"
          :class="isActive('/analysis') ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <i class="fa-solid fa-images w-5 text-center"></i>
          <span>批次分析报告</span>
        </router-link>
        <router-link 
          to="/config" 
          class="nav-item flex items-center space-x-3 px-4 py-3 rounded-lg transition"
          :class="isActive('/config') ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <i class="fa-solid fa-sliders w-5 text-center"></i>
          <span>系统配置</span>
        </router-link>
        <router-link 
          to="/logs" 
          class="nav-item flex items-center space-x-3 px-4 py-3 rounded-lg transition"
          :class="isActive('/logs') ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <i class="fa-solid fa-terminal w-5 text-center"></i>
          <span>运行日志</span>
        </router-link>
        <router-link 
          v-if="isAdmin"
          to="/users" 
          class="nav-item flex items-center space-x-3 px-4 py-3 rounded-lg transition"
          :class="isActive('/users') ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <i class="fa-solid fa-users w-5 text-center"></i>
          <span>用户管理</span>
        </router-link>
      </nav>

      <div class="p-4 border-t border-slate-700">
        <button 
          @click="handleLogout"
          class="w-full flex items-center justify-center space-x-2 px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition"
        >
          <i class="fa-solid fa-right-from-bracket"></i>
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0 bg-gray-50">
      <!-- Top Header -->
      <header class="h-16 bg-white shadow-sm flex items-center justify-between px-6 z-10">
        <div class="flex items-center text-gray-500">
          <div class="flex items-center space-x-3">
            <span class="text-xl font-bold text-gray-900">北汽模糊测试系统</span>
            <span class="text-sm text-gray-400">|</span>
            <h2 class="text-lg font-semibold text-gray-800">{{ currentTitle }}</h2>
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div 
            class="flex items-center px-3 py-1 rounded-full text-sm font-medium border"
            :class="statusClass"
          >
            <span class="w-2 h-2 rounded-full mr-2" :class="statusDotClass"></span>
            {{ statusText }}
          </div>
          <div class="flex items-center px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium border border-gray-200">
            <i class="fa-solid fa-user mr-2"></i>
            <span>{{ username }}</span>
            <span class="mx-2 text-gray-400">/</span>
            <span>{{ userRole }}</span>
          </div>
        </div>
      </header>

      <!-- Content Area -->
      <div class="flex-1 overflow-auto p-6">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { processApi } from './api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isLoggedIn = computed(() => authStore.isLoggedIn)
const isAdmin = computed(() => authStore.isAdmin)
const username = computed(() => authStore.username)
const userRole = computed(() => authStore.user?.role || '')

// Process status
const processRunning = ref(false)
let statusInterval = null

const statusClass = computed(() => 
  processRunning.value 
    ? 'bg-blue-100 text-blue-700 border-blue-200' 
    : 'bg-green-100 text-green-700 border-green-200'
)

const statusDotClass = computed(() => 
  processRunning.value 
    ? 'bg-blue-500 animate-ping' 
    : 'bg-green-500 animate-pulse'
)

const statusText = computed(() => 
  processRunning.value ? '测试运行中...' : '系统就绪'
)

const titles = {
  '/': '系统仪表盘',
  '/analysis': '批次分析报告',
  '/config': '系统配置',
  '/logs': '详细运行日志',
  '/users': '用户管理'
}

const currentTitle = computed(() => titles[route.path] || '仪表盘')

function isActive(path) {
  return route.path === path
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

async function checkProcessStatus() {
  try {
    const response = await processApi.status()
    processRunning.value = response.data.running
  } catch (error) {
    console.error('Failed to check process status:', error)
  }
}

onMounted(() => {
  if (isLoggedIn.value) {
    checkProcessStatus()
    statusInterval = setInterval(checkProcessStatus, 5000)
  }
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>
