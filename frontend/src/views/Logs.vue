<template>
  <div class="h-full flex flex-col fade-in">
    <div class="bg-gray-900 rounded-xl shadow-lg border border-gray-700 flex-1 flex flex-col overflow-hidden">
      <div class="px-4 py-3 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
        <span class="text-gray-300 font-mono text-sm">log_name.log</span>
        <div class="flex space-x-2">
          <button 
            @click="refreshLogs"
            class="text-xs text-gray-400 hover:text-white border border-gray-600 px-2 py-1 rounded"
          >
            <i class="fa-solid fa-refresh mr-1"></i> Refresh
          </button>
          <button 
            @click="clearLogs"
            class="text-xs text-gray-400 hover:text-white border border-gray-600 px-2 py-1 rounded"
          >
            Clear
          </button>
        </div>
      </div>
      <div 
        ref="logContainer"
        class="flex-1 p-4 overflow-y-auto log-console text-sm space-y-1"
      >
        <div v-if="loading" class="text-gray-400">Loading logs...</div>
        <div v-else-if="logs.length === 0" class="text-gray-400">No logs available.</div>
        <div 
          v-for="(line, index) in logs" 
          :key="index"
          class="font-mono border-b border-gray-800 py-1 text-gray-300"
        >
          {{ line }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { logsApi } from '../api'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()
const logContainer = ref(null)
const loading = ref(true)
const localLogs = ref([])

const logs = computed(() => {
  // 优先使用本地日志，如果为空则使用store中的日志
  return localLogs.value.length > 0 ? localLogs.value : testStore.state.logs
})

let logInterval = null

const fetchLogs = async () => {
  try {
    const res = await logsApi.tail(200)
    const lines = res.data.lines || []
    localLogs.value = lines
    testStore.setLogs(lines)
    
    // 自动滚动到底部
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  } catch (e) {
    console.error('Failed to fetch logs:', e)
  } finally {
    loading.value = false
  }
}

const refreshLogs = () => {
  loading.value = true
  fetchLogs()
}

const clearLogs = () => {
  localLogs.value = []
}

onMounted(() => {
  fetchLogs()
  // 每3秒刷新一次日志
  logInterval = setInterval(fetchLogs, 3000)
})

onUnmounted(() => {
  if (logInterval) {
    clearInterval(logInterval)
  }
})
</script>
