<template>
  <div class="h-full flex flex-col fade-in">
    <div class="bg-gray-900 rounded-xl shadow-lg border border-gray-700 flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <div class="px-4 py-3 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
        <div class="flex items-center space-x-4">
          <select 
            v-model="selectedFile" 
            @change="fetchLogContent"
            class="bg-gray-700 text-gray-300 text-sm rounded px-3 py-1 border border-gray-600 focus:border-blue-500"
          >
            <option v-for="file in logFiles" :key="file.filename" :value="file.filename">
              {{ file.filename }} ({{ formatSize(file.size) }})
            </option>
          </select>
          <div class="flex items-center space-x-2">
            <button 
              @click="logType = 'main'" 
              :class="logType === 'main' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'"
              class="px-2 py-1 rounded text-xs"
            >
              Main
            </button>
            <button 
              @click="logType = 'error'" 
              :class="logType === 'error' ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300'"
              class="px-2 py-1 rounded text-xs"
            >
              Error
            </button>
            <button 
              @click="logType = 'warn'" 
              :class="logType === 'warn' ? 'bg-yellow-600 text-white' : 'bg-gray-700 text-gray-300'"
              class="px-2 py-1 rounded text-xs"
            >
              Warn
            </button>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <label class="flex items-center text-gray-400 text-sm">
            <input 
              type="checkbox" 
              v-model="autoRefresh" 
              class="mr-2 rounded"
            >
            自动刷新
          </label>
          <button 
            @click="fetchLogContent" 
            class="text-xs text-gray-400 hover:text-white border border-gray-600 px-2 py-1 rounded"
          >
            <i class="fa-solid fa-refresh mr-1"></i>刷新
          </button>
          <button 
            @click="clearLog" 
            class="text-xs text-gray-400 hover:text-white border border-gray-600 px-2 py-1 rounded"
          >
            Clear
          </button>
        </div>
      </div>

      <!-- Log Content -->
      <div 
        ref="logContainer"
        class="flex-1 p-4 overflow-y-auto log-console text-sm space-y-1"
      >
        <div v-if="loading" class="text-gray-400 text-center py-8">
          <div class="loader mx-auto mb-2"></div>
          加载日志中...
        </div>
        <div v-else-if="logLines.length === 0" class="text-gray-500 text-center py-8">
          暂无日志内容
        </div>
        <div 
          v-else
          v-for="(line, index) in logLines" 
          :key="index" 
          class="font-mono border-b border-gray-800 py-1"
        >
          <span :class="getLogLevelClass(line)" class="font-bold">{{ getLogLevel(line) }}</span>
          <span class="text-gray-300 ml-2">{{ line }}</span>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-4 py-2 bg-gray-800 border-t border-gray-700 text-xs text-gray-500 flex justify-between">
        <span>{{ logLines.length }} 行</span>
        <span>{{ selectedFile }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { logApi } from '../api'

const logFiles = ref([])
const selectedFile = ref('')
const logLines = ref([])
const loading = ref(false)
const autoRefresh = ref(true)
const logType = ref('main')
const logContainer = ref(null)

let refreshInterval = null

async function fetchLogFiles() {
  try {
    const response = await logApi.list(logType.value)
    logFiles.value = response.data.files || []
    if (logFiles.value.length > 0 && !selectedFile.value) {
      selectedFile.value = logFiles.value[0].filename
      await fetchLogContent()
    }
  } catch (error) {
    console.error('Failed to fetch log files:', error)
  }
}

async function fetchLogContent() {
  if (!selectedFile.value) return
  
  loading.value = true
  try {
    const response = await logApi.getContent(selectedFile.value, 1000)
    const content = response.data.content || ''
    logLines.value = content.split('\n').filter(line => line.trim())
    
    // Scroll to bottom
    if (logContainer.value) {
      setTimeout(() => {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }, 100)
    }
  } catch (error) {
    console.error('Failed to fetch log content:', error)
    logLines.value = []
  }
  loading.value = false
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function getLogLevel(line) {
  if (line.includes('ERROR')) return 'ERROR'
  if (line.includes('WARNING') || line.includes('WARN')) return 'WARN'
  if (line.includes('DEBUG')) return 'DEBUG'
  return 'INFO'
}

function getLogLevelClass(line) {
  if (line.includes('ERROR')) return 'text-red-500'
  if (line.includes('WARNING') || line.includes('WARN')) return 'text-yellow-400'
  if (line.includes('DEBUG')) return 'text-gray-500'
  return 'text-green-400'
}

function clearLog() {
  logLines.value = []
}

watch(logType, () => {
  selectedFile.value = ''
  fetchLogFiles()
})

watch(autoRefresh, (val) => {
  if (val) {
    refreshInterval = setInterval(fetchLogContent, 5000)
  } else if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

onMounted(() => {
  fetchLogFiles()
  if (autoRefresh.value) {
    refreshInterval = setInterval(fetchLogContent, 5000)
  }
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
