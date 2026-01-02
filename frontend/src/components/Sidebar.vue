<template>
  <aside class="w-64 bg-slate-900 text-white flex flex-col shadow-lg transition-all duration-300">
    <div class="h-16 flex items-center justify-center border-b border-slate-700">
      <h1 class="text-xl font-bold tracking-wider">
        <i class="fa-solid fa-car-burst mr-2"></i>FuzzTest
      </h1>
    </div>

    <nav class="flex-1 py-6 space-y-2 px-3">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item flex items-center space-x-3 px-4 py-3 rounded-lg transition"
        :class="isActive(item.path) 
          ? 'bg-blue-600 text-white hover:bg-blue-700' 
          : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
      >
        <i :class="item.icon" class="w-5 text-center"></i>
        <span>{{ item.label }}</span>
      </router-link>
      <button
        @click="handleLogout"
        class="nav-item flex items-center space-x-3 px-4 py-3 rounded-lg transition text-red-400 hover:bg-red-900/30 hover:text-red-300 mt-auto"
      >
        <i class="fa-solid fa-right-from-bracket w-5 text-center"></i>
        <span>退出登录</span>
      </button>
    </nav>
  </aside>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const navItems = [
  { path: '/dashboard', icon: 'fa-solid fa-gauge-high', label: '仪表盘' },
  { path: '/charts', icon: 'fa-solid fa-chart-line', label: '数据图表' },
  { path: '/config', icon: 'fa-solid fa-sliders', label: '系统配置' },
  { path: '/logs', icon: 'fa-solid fa-terminal', label: '运行日志' },
  { path: '/users', icon: 'fa-solid fa-users', label: '用户管理' }
]

const isActive = (path) => {
  return route.path === path
}

const handleLogout = async () => {
  if (confirm('确定要退出登录吗？')) {
    try {
      await axios.post('/api/logout')
    } catch (e) {
      console.error('Logout failed:', e)
    } finally {
      localStorage.removeItem('isAuthenticated')
      router.push('/login')
    }
  }
}
</script>
