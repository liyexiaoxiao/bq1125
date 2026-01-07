<template>
  <div class="space-y-6 fade-in">
    <!-- Control Bar -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div class="flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center space-x-4 w-full md:w-auto">
          <button 
            @click="startTest" 
            :disabled="processRunning || startLoading"
            class="flex-1 md:flex-none flex items-center justify-center px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition shadow-md hover:shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="startLoading" class="loader mr-2"></span>
            <i v-else class="fa-solid fa-play mr-2"></i>
            开始测试
          </button>
          <button 
            @click="stopTest" 
            :disabled="!processRunning || stopLoading"
            class="flex-1 md:flex-none flex items-center justify-center px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition shadow-md hover:shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="stopLoading" class="loader mr-2"></span>
            <i v-else class="fa-solid fa-stop mr-2"></i>
            停止
          </button>
        </div>
        
        <div class="flex items-center space-x-4 w-full md:w-auto justify-end">
          <button 
            @click="exportData" 
            class="flex items-center px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg text-sm font-medium transition shadow-sm"
          >
            <i class="fa-solid fa-download mr-2 text-blue-600"></i>
            导出测试数据 (DB & Logs)
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
          <div class="p-4 bg-blue-50 text-blue-600 rounded-xl">
            <i class="fa-solid fa-rotate text-2xl" :class="{ 'animate-spin': processRunning }"></i>
          </div>
        </div>
        <div class="mt-6 w-full bg-gray-200 rounded-full h-2">
          <div 
            class="bg-blue-600 h-2 rounded-full transition-all duration-500" 
            :style="{ width: progressPercent + '%' }"
          ></div>
        </div>
        <p class="text-sm text-gray-500 mt-2">目标: {{ totalRuns }} 次</p>
      </div>

      <!-- Process Status -->
      <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-sm font-semibold text-gray-400 uppercase tracking-wider">进程状态 (Process)</p>
            <h3 class="text-3xl font-bold mt-4" :class="processRunning ? 'text-blue-600' : 'text-gray-600'">
              {{ processRunning ? '运行中' : '已停止' }}
            </h3>
          </div>
          <div class="p-4 rounded-xl" :class="processRunning ? 'bg-blue-50 text-blue-600' : 'bg-gray-50 text-gray-400'">
            <i class="fa-solid fa-server text-2xl"></i>
          </div>
        </div>
        <div class="mt-6 flex space-x-2">
          <span v-if="processPid" class="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-md">
            PID: {{ processPid }}
          </span>
          <span class="px-2 py-1 text-xs rounded-md" :class="processRunning ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'">
            {{ processMessage }}
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
      <div class="p-4 bg-slate-900 font-mono text-sm text-gray-300 overflow-y-auto log-console flex-1" style="max-height: 400px;">
        <div v-for="(line, index) in logLines" :key="index" class="py-1">
          <span :class="getLogLevelClass(line)">{{ getLogLevel(line) }}</span> {{ getLogContent(line) }}
        </div>
        <div v-if="logLines.length === 0" class="text-gray-500">
          暂无日志...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { processApi, logApi, configApi } from '../api'

const processRunning = ref(false)
const processPid = ref(null)
const processMessage = ref('进程未启动')
const startLoading = ref(false)
const stopLoading = ref(false)
const runs = ref(0)
const totalRuns = ref(1000)
const logLines = ref([])

let statusInterval = null
let logsInterval = null

const progressPercent = computed(() => {
  if (totalRuns.value === 0) return 0
  return Math.min(100, (runs.value / totalRuns.value) * 100)
})

async function checkProcessStatus() {
  try {
    const response = await processApi.status()
    processRunning.value = response.data.running
    processPid.value = response.data.pid
    processMessage.value = response.data.message
    
    // Update progress from status
    if (response.data.current_round !== undefined) {
      runs.value = response.data.current_round
    }
    if (response.data.total_rounds !== undefined && response.data.total_rounds > 0) {
      totalRuns.value = response.data.total_rounds
    }
  } catch (error) {
    console.error('Failed to check process status:', error)
  }
}

async function fetchLatestLogs() {
  try {
    const response = await logApi.getLatest(50)
    const content = response.data.content || ''
    logLines.value = content.split('\n').filter(line => line.trim()).reverse().slice(0, 20)
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  }
}

async function fetchConfig() {
  try {
    const response = await configApi.get()
    // Helper to fallback if status API hasn't returned it yet
    if (totalRuns.value === 1000) {
        totalRuns.value = response.data.config.RUN_TIMES || 1000
    }
  } catch (error) {
    console.error('Failed to fetch config:', error)
  }
}

async function startTest() {
  startLoading.value = true
  try {
    const response = await processApi.start()
    processRunning.value = response.data.running
    processPid.value = response.data.pid
    processMessage.value = response.data.message
    // Force immediate status update
    checkProcessStatus()
  } catch (error) {
    alert(error.response?.data?.detail || '启动失败')
  }
  startLoading.value = false
}

async function stopTest() {
  stopLoading.value = true
  try {
    const response = await processApi.stop()
    processRunning.value = response.data.running
    processPid.value = response.data.pid
    processMessage.value = response.data.message
    checkProcessStatus()
  } catch (error) {
    alert(error.response?.data?.detail || '停止失败')
  }
  stopLoading.value = false
}

async function exportData() {
  try {
    const response = await processApi.export()
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'test_results.db')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Export failed:', error)
    alert('导出失败 (后端可能未找到 db.db 文件)')
  }
}

function getLogLevel(line) {
  if (line.includes('ERROR')) return '[ERROR]'
  if (line.includes('WARNING') || line.includes('WARN')) return '[WARN]'
  if (line.includes('DEBUG')) return '[DEBUG]'
  return '[INFO]'
}

function getLogLevelClass(line) {
  if (line.includes('ERROR')) return 'text-red-500'
  if (line.includes('WARNING') || line.includes('WARN')) return 'text-yellow-400'
  if (line.includes('DEBUG')) return 'text-gray-500'
  return 'text-green-400'
}

function getLogContent(line) {
  // Remove the log level prefix from the line
  return line.replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+\s+-\s+(INFO|ERROR|WARNING|DEBUG)\s+-\s+/, '')
}

onMounted(() => {
  checkProcessStatus()
  fetchLatestLogs()
  fetchConfig()
  
  statusInterval = setInterval(checkProcessStatus, 3000)
  logsInterval = setInterval(fetchLatestLogs, 5000)
})

onUnmounted(() => {
  if (statusInterval) clearInterval(statusInterval)
  if (logsInterval) clearInterval(logsInterval)
})
</script>
