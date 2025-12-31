<template>
  <div class="space-y-6 fade-in">
    <!-- Control Bar -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div class="flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center space-x-4 w-full md:w-auto">
          <button 
            @click="startTest" 
            :disabled="isRunning"
            class="flex-1 md:flex-none flex items-center justify-center px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition shadow-md hover:shadow-lg btn-active disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <i class="fa-solid fa-play mr-2"></i> 开始测试
          </button>
          <button 
            @click="stopTest" 
            :disabled="!isRunning"
            class="flex-1 md:flex-none flex items-center justify-center px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition shadow-md hover:shadow-lg btn-active disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <i class="fa-solid fa-stop mr-2"></i> 停止
          </button>
        </div>
        
        <div class="flex items-center space-x-4 w-full md:w-auto justify-end">
          <button 
            @click="exportData"
            class="flex items-center px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <i class="fa-solid fa-download mr-2 text-blue-600"></i> 导出测试数据 (DB & Logs)
          </button>
        </div>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Total Runs -->
      <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-sm font-semibold text-gray-400 uppercase tracking-wider">当前运行进度 (Current Run)</p>
            <h3 class="text-5xl font-bold text-gray-800 mt-4">{{ runs }}</h3>
          </div>
          <button 
            :disabled="isRunning"
            @click="resetAndStart"
            class="p-4 bg-blue-50 text-blue-600 rounded-xl border border-blue-200 hover:bg-blue-100 transition disabled:opacity-50 disabled:cursor-not-allowed" 
            title="复位并重新开始"
          >
            <i class="fa-solid fa-rotate text-2xl"></i>
          </button>
        </div>
        <div class="mt-6 w-full bg-gray-200 rounded-full h-2">
          <div 
            class="bg-blue-600 h-2 rounded-full transition-all duration-500" 
            :style="{ width: progressPercent + '%' }"
          ></div>
        </div>
        <p class="text-sm text-gray-500 mt-2">目标: {{ goal }} 次</p>
      </div>

      <!-- Crashes Found -->
      <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-sm font-semibold text-gray-400 uppercase tracking-wider">发现异常 (Exceptions)</p>
            <h3 class="text-5xl font-bold text-red-600 mt-4">{{ exceptions }}</h3>
          </div>
          <div class="p-4 bg-red-50 text-red-600 rounded-xl">
            <i class="fa-solid fa-bug text-2xl"></i>
          </div>
        </div>
        <div class="mt-6 flex space-x-2">
          <span v-if="exceptions > 0" class="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-md">
            发现 {{ exceptions }} 个异常
          </span>
        </div>
      </div>
    </div>

    <!-- Recent Logs Preview -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex-1 flex flex-col min-h-[300px]">
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
        <h3 class="font-semibold text-gray-800">实时系统日志</h3>
        <router-link to="/logs" class="text-blue-600 text-sm hover:underline font-medium">
          查看完整日志 <i class="fa-solid fa-arrow-right ml-1"></i>
        </router-link>
      </div>
      <div 
        class="p-4 bg-slate-900 font-mono text-sm text-gray-300 overflow-y-auto log-console flex-1" 
        style="max-height: 400px;"
      >
        <div v-if="dashboardLogs.length === 0" class="py-1">
          <span class="text-green-400">[INFO]</span> System Ready. Loaded config.
        </div>
        <div v-for="(log, index) in dashboardLogs" :key="index" class="py-1">
          <span :class="logLevelClass(log.level)">[{{ log.level }}]</span> 
          {{ log.time }} - {{ log.message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { controlApi, logsApi, exportApi } from '../api'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()

const runs = computed(() => testStore.state.runs)
const goal = computed(() => testStore.state.goal)
const exceptions = computed(() => testStore.state.exceptions)
const isRunning = computed(() => testStore.state.isRunning)
const dashboardLogs = computed(() => testStore.state.dashboardLogs)

const progressPercent = computed(() => {
  if (!goal.value) return 0
  return Math.min((runs.value / goal.value) * 100, 100)
})

let statusInterval = null
let logInterval = null

const logLevelClass = (level) => {
  const classes = {
    'INFO': 'text-green-400',
    'WARN': 'text-yellow-400',
    'ERROR': 'text-red-500',
    'SYS': 'text-purple-400'
  }
  return classes[level] || 'text-white'
}

const addLog = (level, message) => {
  testStore.addDashboardLog(level, message)
}

const startTest = async () => {
  try {
    const res = await controlApi.start()
    if (res.data.ok !== 1) {
      addLog('ERROR', '启动失败')
      return
    }
    testStore.setRunning(true)
    addLog('INFO', '开始测试')
    startPolling()
  } catch (e) {
    addLog('ERROR', '启动异常: ' + e.message)
  }
}

const stopTest = async () => {
  try {
    const res = await controlApi.stop()
    if (res.data.ok !== 1) {
      addLog('ERROR', '停止失败')
      return
    }
    // 同时设置 isRunning 为 false 和状态为 stopped
    testStore.setRunning(false)
    testStore.setSystemStatus('stopped')
    addLog('WARN', '已停止')
    stopPolling()
  } catch (e) {
    addLog('ERROR', '停止异常: ' + e.message)
  }
}

const resetAndStart = () => {
  if (isRunning.value) return
  testStore.reset()
  startTest()
}

const exportData = async () => {
  try {
    const blob = await exportApi.download()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'test_results.zip'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
    addLog('SYS', '导出完成')
  } catch (e) {
    addLog('ERROR', '导出失败: ' + e.message)
  }
}

const fetchStatus = async () => {
  try {
    const res = await controlApi.getStatus()
    testStore.updateStatus(res.data)
  } catch (e) {
    // 静默处理
  }
}

const fetchLogs = async () => {
  try {
    const res = await logsApi.tail(200)
    const lines = res.data.lines || []
    testStore.setLogs(lines)
    
    // 更新仪表盘最新日志
    if (lines.length > 0) {
      const latest = lines[lines.length - 1]
      if (latest) {
        addLog('INFO', latest)
      }
    }
  } catch (e) {
    // 静默处理
  }
}

const startPolling = () => {
  if (logInterval) clearInterval(logInterval)
  logInterval = setInterval(fetchLogs, 1000)
  
  if (statusInterval) clearInterval(statusInterval)
  statusInterval = setInterval(fetchStatus, 1000)
}

const stopPolling = () => {
  if (logInterval) {
    clearInterval(logInterval)
    logInterval = null
  }
}

onMounted(() => {
  fetchStatus()
  // 每2秒更新一次状态
  statusInterval = setInterval(fetchStatus, 2000)
  // 每3秒获取一次日志
  logInterval = setInterval(fetchLogs, 3000)
})

onUnmounted(() => {
  if (statusInterval) clearInterval(statusInterval)
  if (logInterval) clearInterval(logInterval)
})
</script>
