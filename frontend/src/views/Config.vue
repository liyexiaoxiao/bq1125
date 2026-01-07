<template>
  <div class="max-w-5xl mx-auto fade-in">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
        <div>
          <h3 class="font-semibold text-gray-800 text-lg">System Configuration (config.py)</h3>
          <p class="text-sm text-gray-500">Parameters map directly to the backend configuration file.</p>
        </div>
        <span class="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full border border-yellow-200">
          <i class="fa-solid fa-triangle-exclamation mr-1"></i> Restart required on change
        </span>
      </div>
      
      <div v-if="loading" class="p-8 text-center">
        <div class="loader mx-auto mb-4"></div>
        <p class="text-gray-500">加载配置中...</p>
      </div>

      <form v-else class="p-6 space-y-8" @submit.prevent="saveConfig">
        <!-- Environment Config -->
        <div>
          <h4 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 border-b pb-2 text-blue-600">
            <i class="fa-solid fa-server mr-2"></i>Environment Config
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="col-span-1 md:col-span-2">
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">TEST_PALTFORM_URL</label>
              <input 
                v-model="config.TEST_PALTFORM_URL" 
                type="url" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2 font-mono text-sm"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">RUN_TIMES</label>
              <input 
                v-model.number="config.RUN_TIMES" 
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">DIR_NAME</label>
              <input 
                v-model="config.DIR_NAME" 
                type="text" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
          </div>
        </div>

        <!-- Strategy & Thresholds -->
        <div>
          <h4 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 border-b pb-2 text-purple-600">
            <i class="fa-solid fa-code-branch mr-2"></i>Strategy & Thresholds
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">MODE</label>
              <select 
                v-model="config.MODE" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2 font-medium bg-gray-50"
              >
                <option value="MIX">MIX</option>
                <option value="SLEEP">SLEEP</option>
                <option value="WAKE">WAKE</option>
                <option value="REPLAY">REPLAY</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">READ_INTERVAL</label>
              <input 
                v-model.number="config.READ_INTERVAL" 
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">SIGNAL_TOLERANCE</label>
              <input 
                v-model.number="config.SIGNAL_TOLERANCE" 
                type="number" 
                step="0.01" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">SINGLE_VARIATION_TIME</label>
              <input 
                v-model.number="config.SINGLE_VARIATION_TIME" 
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">MULTIPLE_VARIATION_TIME</label>
              <input 
                v-model.number="config.MULTIPLE_VARIATION_TIME" 
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">REPEAT_VARIATION_TIME</label>
              <input 
                v-model.number="config.REPEAT_VARIATION_TIME" 
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
          </div>
        </div>

        <!-- Replay Config -->
        <div 
          class="transition-all duration-300 rounded-lg p-4 border"
          :class="config.MODE === 'REPLAY' ? 'bg-amber-50 border-amber-200' : 'border-transparent'"
        >
          <h4 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 border-b pb-2 text-amber-600">
            <i class="fa-solid fa-clock-rotate-left mr-2"></i>Replay Configuration
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">REPLAY_START_RUN_ID</label>
              <input 
                v-model.number="config.REPLAY_START_RUN_ID" 
                type="number" 
                placeholder="None (从头开始)"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">REPLAY_END_RUN_ID</label>
              <input 
                v-model.number="config.REPLAY_END_RUN_ID" 
                type="number" 
                placeholder="None (到最后)"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
          </div>
          
          <!-- Replay DB Upload -->
          <div v-if="config.MODE === 'REPLAY'" class="mt-6 pt-4 border-t border-amber-200">
            <label class="block text-sm font-bold text-gray-700 mb-2">
              <i class="fa-solid fa-database mr-2"></i>上传回放数据库 (replay.db)
            </label>
            <div class="flex items-center gap-4">
              <input 
                ref="replayFileInput"
                type="file" 
                accept=".db"
                class="hidden"
                @change="handleReplayDbUpload"
              >
              <button 
                type="button"
                @click="$refs.replayFileInput.click()"
                :disabled="uploadingReplayDb"
                class="flex items-center px-4 py-2 bg-amber-600 text-white rounded-lg text-sm font-medium hover:bg-amber-700 transition disabled:opacity-50"
              >
                <span v-if="uploadingReplayDb" class="loader mr-2 inline-block"></span>
                <i v-else class="fa-solid fa-upload mr-2"></i>
                选择 replay.db 文件
              </button>
              <span v-if="replayDbStatus" class="text-sm" :class="replayDbSuccess ? 'text-green-600' : 'text-red-600'">
                {{ replayDbStatus }}
              </span>
            </div>
            <p class="text-xs text-gray-500 mt-2">
              回放模式需要上传包含历史测试数据的 replay.db 文件
            </p>
          </div>
        </div>

        <div v-if="saveMessage" class="p-3 rounded-lg text-sm" :class="saveSuccess ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
          <i :class="saveSuccess ? 'fa-solid fa-check-circle' : 'fa-solid fa-circle-exclamation'" class="mr-2"></i>
          {{ saveMessage }}
        </div>

        <div class="flex justify-end space-x-4 pt-4 border-t border-gray-200">
          <button 
            type="button"
            @click="resetToDefaults"
            class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition"
          >
            <i class="fa-solid fa-rotate-left mr-2"></i>
            恢复默认
          </button>
          <button 
            type="submit" 
            :disabled="saving"
            class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-lg transition transform active:scale-95 disabled:opacity-50"
          >
            <span v-if="saving" class="loader mr-2 inline-block"></span>
            <i v-else class="fa-solid fa-floppy-disk mr-2"></i>
            Save & Apply
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { configApi } from '../api'
import api from '../api'

// Default configuration values (initial settings)
const defaultConfig = {
  TEST_PALTFORM_URL: 'https://krunapi.vtest.work:8020',
  RUN_TIMES: 1000,
  DIR_NAME: 'test001',
  MODE: 'MIX',
  READ_INTERVAL: 100,
  SIGNAL_TOLERANCE: 0.1,
  SINGLE_VARIATION_TIME: 10,
  MULTIPLE_VARIATION_TIME: 10,
  REPEAT_VARIATION_TIME: 20,
  REPLAY_START_RUN_ID: null,
  REPLAY_END_RUN_ID: 21
}

const loading = ref(true)
const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)
const config = ref({})

// Replay DB upload state
const replayFileInput = ref(null)
const uploadingReplayDb = ref(false)
const replayDbStatus = ref('')
const replayDbSuccess = ref(false)

async function fetchConfig() {
  loading.value = true
  try {
    const response = await configApi.get()
    config.value = response.data.config || { ...defaultConfig }
  } catch (error) {
    console.error('Failed to fetch config:', error)
    // Use default config if fetch fails
    config.value = { ...defaultConfig }
  }
  loading.value = false
}

function resetToDefaults() {
  if (confirm('确定要恢复默认配置吗？这将覆盖当前的所有设置。')) {
    config.value = { ...defaultConfig }
    saveMessage.value = '已恢复默认配置，请点击保存按钮应用更改。'
    saveSuccess.value = true
    setTimeout(() => { saveMessage.value = '' }, 5000)
  }
}

async function handleReplayDbUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  
  uploadingReplayDb.value = true
  replayDbStatus.value = ''
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/config/upload-replay-db', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    replayDbStatus.value = `上传成功: ${response.data.filename}`
    replayDbSuccess.value = true
  } catch (error) {
    replayDbStatus.value = error.response?.data?.detail || '上传失败'
    replayDbSuccess.value = false
  }
  
  uploadingReplayDb.value = false
  event.target.value = ''
  
  setTimeout(() => { replayDbStatus.value = '' }, 5000)
}

async function saveConfig() {
  saving.value = true
  saveMessage.value = ''
  try {
    await configApi.update(config.value)
    saveMessage.value = '配置已保存成功！重启测试后生效。'
    saveSuccess.value = true
  } catch (error) {
    saveMessage.value = error.response?.data?.detail || '保存失败'
    saveSuccess.value = false
  }
  saving.value = false
  
  // Clear message after 5 seconds
  setTimeout(() => {
    saveMessage.value = ''
  }, 5000)
}

onMounted(fetchConfig)
</script>

