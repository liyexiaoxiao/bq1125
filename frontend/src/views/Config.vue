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
      
      <form class="p-6 space-y-8" @submit.prevent="saveConfig">
        
        <!-- 1. Environment Config -->
        <div>
          <h4 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 border-b pb-2 text-blue-600">
            <i class="fa-solid fa-server mr-2"></i>Environment Config
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="col-span-1 md:col-span-2">
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">TEST_PALTFORM_URL</label>
              <input 
                v-model="config.testPlatformUrl"
                type="url" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2 font-mono text-sm"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">RUN_TIMES</label>
              <input 
                v-model.number="config.runTimes"
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
          </div>
        </div>

        <!-- 2. Database Config -->
        <div>
          <h4 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 border-b pb-2 text-green-600">
            <i class="fa-solid fa-database mr-2"></i>Database Configuration
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">DATABASE_NAME</label>
              <div class="text-xs text-gray-500 mb-1">数据库名称（仅输入名称，不含后缀）</div>
              <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-500 font-mono">app/</span>
                <input 
                  v-model="config.databaseName"
                  type="text" 
                  placeholder="db"
                  class="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2 font-mono text-sm"
                >
                <span class="text-sm text-gray-500 font-mono">.db</span>
              </div>
              <div class="mt-2 text-xs text-blue-600 font-mono bg-blue-50 p-2 rounded">
                完整路径: app/{{ config.databaseName || 'db' }}.db
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Strategy & Thresholds -->
        <div>
          <h4 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 border-b pb-2 text-purple-600">
            <i class="fa-solid fa-code-branch mr-2"></i>Strategy & Thresholds
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">MODE</label>
              <select 
                v-model="config.mode"
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
                v-model.number="config.readInterval"
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">SIGNAL_TOLERANCE</label>
              <input 
                v-model.number="config.signalTolerance"
                type="number" 
                step="0.01" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">SINGLE_VARIATION_TIME</label>
              <input 
                v-model.number="config.singleVariationTime"
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">MULTIPLE_VARIATION_TIME</label>
              <input 
                v-model.number="config.multipleVariationTime"
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">REPEAT_VARIATION_TIME</label>
              <input 
                v-model.number="config.repeatVariationTime"
                type="number" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
          </div>
        </div>

        <!-- 4. Replay Config -->
        <div 
          class="transition-all duration-300 rounded-lg p-4 border"
          :class="isReplayMode ? 'bg-amber-50 border-amber-200' : 'border-transparent'"
        >
          <h4 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 border-b pb-2 text-amber-600">
            <i class="fa-solid fa-clock-rotate-left mr-2"></i>Replay Configuration
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">REPLAY_START_RUN_ID</label>
              <input 
                v-model.number="config.replayStartRunId"
                type="number" 
                placeholder="None" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-1 font-mono">REPLAY_END_RUN_ID</label>
              <input 
                v-model.number="config.replayEndRunId"
                type="number" 
                placeholder="None" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
              >
            </div>
          </div>

          <!-- Dynamic File Upload for Replay Mode -->
          <div 
            v-if="isReplayMode"
            class="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg"
          >
            <label class="block text-sm font-medium text-amber-900 mb-2">
              <i class="fa-solid fa-database mr-2"></i>Upload Source DB (REPLAY_SOURCE_DATABASE_URI)
            </label>
            <div class="flex items-center space-x-4">
              <input 
                type="file" 
                accept=".db,.sqlite" 
                @change="handleReplayDbUpload"
                class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-amber-100 file:text-amber-700 hover:file:bg-amber-200"
              >
            </div>
          </div>
        </div>

        <div class="flex justify-end pt-4 border-t border-gray-200">
          <button 
            type="submit" 
            :disabled="saving"
            class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-lg transition transform btn-active disabled:opacity-50"
          >
            <i v-if="saving" class="fa-solid fa-spinner fa-spin mr-2"></i>
            <i v-else class="fa-solid fa-floppy-disk mr-2"></i>
            {{ saving ? '保存中...' : 'Save & Apply' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { configApi } from '../api'

const saving = ref(false)

const config = ref({
  testPlatformUrl: 'https://krunapi.vtest.work:8020',
  runTimes: 1000,
  mode: 'MIX',
  readInterval: 100,
  signalTolerance: 0.1,
  singleVariationTime: 10,
  multipleVariationTime: 10,
  repeatVariationTime: 20,
  replayStartRunId: null,
  replayEndRunId: 21,
  databaseName: 'db'
})

const isReplayMode = computed(() => config.value.mode === 'REPLAY')

const handleReplayDbUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    console.log('Replay DB file selected:', file.name)
    // TODO: 处理文件上传
  }
}

const loadConfig = async () => {
  try {
    const res = await configApi.get()
    if (res.data) {
      Object.assign(config.value, res.data)
    }
  } catch (e) {
    console.log('Failed to load config, using defaults')
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    await configApi.save(config.value)
    alert('配置已保存')
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>
