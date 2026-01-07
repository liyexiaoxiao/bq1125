<template>
  <header class="h-16 bg-white shadow-sm flex items-center justify-between px-6 z-10">
    <div class="flex items-center text-gray-500">
      <button class="mr-4 hover:text-blue-600 lg:hidden">
        <i class="fa-solid fa-bars"></i>
      </button>
      <div class="flex items-center space-x-3">
        <span class="text-xl font-bold text-gray-900">北汽模糊测试系统</span>
        <span class="text-sm text-gray-400">|</span>
        <h2 class="text-lg font-semibold text-gray-800">{{ pageTitle }}</h2>
      </div>
    </div>
    <div class="flex items-center space-x-4">
      <!-- System Status -->
      <div 
        class="flex items-center px-3 py-1 rounded-full text-sm font-medium border"
        :class="statusClass"
      >
        <span 
          v-if="systemStatus === 'ready'" 
          class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"
        ></span>
        <span 
          v-else-if="systemStatus === 'running'" 
          class="w-2 h-2 rounded-full bg-blue-500 mr-2 animate-ping"
        ></span>
        <i v-else class="fa-solid fa-stop mr-2"></i>
        {{ statusText }}
      </div>
      
      <!-- User Info -->
      <div class="flex items-center px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium border border-gray-200">
        <i class="fa-solid fa-user mr-2"></i>
        <span>{{ userName }}</span>
        <span class="mx-2 text-gray-400">/</span>
        <span>{{ userRole }}</span>
      </div>
      
      <button 
        @click="openHelp"
        class="px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
      >
        帮助
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, inject, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTestStore } from '../stores/testStore'

const route = useRoute()
const showHelp = inject('showHelp')
const testStore = useTestStore()

const userName = ref('北汽工程师')
// const userRole = ref('13579')

// 使用 state 确保响应式
const systemStatus = computed(() => testStore.state.systemStatus)

onMounted(() => {
  const storedName = localStorage.getItem('userName')
  const storedRoles = localStorage.getItem('roles')
  
  if (storedName) userName.value = storedName.trim()
  if (storedRoles) {
    try {
      const parsed = JSON.parse(storedRoles)
      if (Array.isArray(parsed)) {
        userRole.value = parsed.join(',')
      } else {
        userRole.value = storedRoles
      }
    } catch {
      userRole.value = storedRoles
    }
  }
})

const pageTitle = computed(() => {
  return route.meta?.title || '仪表盘'
})

const statusClass = computed(() => {
  const classes = {
    ready: 'bg-green-100 text-green-700 border-green-200',
    running: 'bg-blue-100 text-blue-700 border-blue-200',
    stopped: 'bg-red-100 text-red-700 border-red-200'
  }
  return classes[systemStatus.value] || classes.ready
})

const statusText = computed(() => {
  const texts = {
    ready: '系统就绪',
    running: '测试运行中...',
    stopped: '已停止'
  }
  return texts[systemStatus.value] || '系统就绪'
})

const openHelp = () => {
  showHelp.value = true
}
</script>
