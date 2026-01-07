<template>
  <div class="space-y-6 fade-in">
    <!-- Data Source Card -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div class="flex flex-col md:flex-row justify-between items-center gap-4">
        <div class="flex items-center gap-4">
          <div class="flex items-center">
            <i class="fa-solid fa-database text-gray-400 mr-2"></i>
            <span class="font-medium text-gray-700">数据源:</span>
            <span 
              class="ml-2 px-2 py-1 rounded text-sm font-medium"
              :class="dataSource.is_custom ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-700'"
            >
              {{ dataSource.current_source }}
            </span>
            <span 
              v-if="dataSource.is_custom" 
              class="ml-2 text-xs text-indigo-600"
            >
              (已上传自定义数据库)
            </span>
          </div>
        </div>
        
        <div class="flex items-center gap-3">
          <input 
            ref="fileInput"
            type="file" 
            accept=".db"
            class="hidden"
            @change="handleFileUpload"
          >
          <button 
            @click="$refs.fileInput.click()"
            :disabled="uploading"
            class="flex items-center px-4 py-2 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-sm font-medium hover:bg-indigo-100 transition disabled:opacity-50"
          >
            <span v-if="uploading" class="loader mr-2 inline-block"></span>
            <i v-else class="fa-solid fa-upload mr-2"></i>
            上传数据库 (.db)
          </button>
          <button 
            v-if="dataSource.is_custom"
            @click="resetDataSource"
            class="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
          >
            <i class="fa-solid fa-rotate-left mr-2"></i>
            恢复默认
          </button>
        </div>
      </div>
      
      <div v-if="uploadMessage" class="mt-3 p-2 rounded text-sm" :class="uploadSuccess ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
        {{ uploadMessage }}
      </div>
    </div>

    <!-- Toolbar -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col md:flex-row justify-between items-center gap-4">
      <div class="flex items-center gap-4 w-full md:w-auto">
        <label class="font-medium text-gray-700 whitespace-nowrap">批次大小:</label>
        <select 
          v-model.number="batchSize" 
          class="form-select rounded-md border-gray-300 shadow-sm py-2 px-3 border bg-white"
        >
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
        </select>
        
        <label class="font-medium text-gray-700 whitespace-nowrap">批次编号:</label>
        <input 
          v-model.number="batchNum" 
          type="number" 
          min="1" 
          placeholder="全部"
          class="w-20 rounded-md border-gray-300 shadow-sm py-2 px-3 border bg-white"
        >
      </div>
      
      <div class="flex bg-gray-100 p-1 rounded-lg w-full md:w-auto">
        <button 
          @click="activeTab = 'single'" 
          :class="activeTab === 'single' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          class="flex-1 md:flex-none px-6 py-1.5 rounded-md text-sm font-medium transition"
        >
          单信号趋势
        </button>
        <button 
          @click="activeTab = 'compare'" 
          :class="activeTab === 'compare' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          class="flex-1 md:flex-none px-6 py-1.5 rounded-md text-sm font-medium transition"
        >
          对比分析
        </button>
      </div>
    </div>

    <!-- Single Signal Tab -->
    <div v-if="activeTab === 'single'" class="space-y-4">
      <div class="flex items-center gap-4">
        <button 
          @click="generateTrends" 
          :disabled="loadingTrends"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50"
        >
          <span v-if="loadingTrends" class="loader mr-2 inline-block"></span>
          <i v-else class="fa-solid fa-chart-line mr-2"></i>
          生成趋势图
        </button>
        <span class="text-sm text-gray-500">共 {{ trendCharts.length }} 张图表</span>
      </div>

      <div v-if="loadingTrends" class="text-center py-12">
        <div class="loader mx-auto mb-4" style="width: 40px; height: 40px;"></div>
        <p class="text-gray-500">正在生成图表，请稍候...</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div 
          v-for="chart in trendCharts" 
          :key="chart.name + chart.batch_num"
          class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 transition hover:shadow-md"
        >
          <h4 class="font-medium text-gray-700 mb-3 border-b pb-2">
            {{ chart.name }} (批次 {{ chart.batch_num }})
          </h4>
          <img 
            :src="'data:image/png;base64,' + chart.image_base64" 
            :alt="chart.name"
            class="w-full rounded-lg"
          >
        </div>
      </div>
    </div>

    <!-- Comparison Tab -->
    <div v-if="activeTab === 'compare'" class="space-y-4">
      <div class="flex flex-wrap items-center gap-4">
        <select 
          v-model="signal1" 
          class="rounded-md border-gray-300 shadow-sm py-2 px-3 border bg-white min-w-[200px]"
        >
          <option value="">选择信号1</option>
          <option v-for="sig in signals" :key="sig" :value="sig">{{ sig }}</option>
        </select>
        
        <span class="text-gray-400">vs</span>
        
        <select 
          v-model="signal2" 
          class="rounded-md border-gray-300 shadow-sm py-2 px-3 border bg-white min-w-[200px]"
        >
          <option value="">选择信号2</option>
          <option v-for="sig in signals" :key="sig" :value="sig">{{ sig }}</option>
        </select>
        
        <button 
          @click="generateComparison" 
          :disabled="loadingComparison || !signal1 || !signal2"
          class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition disabled:opacity-50"
        >
          <span v-if="loadingComparison" class="loader mr-2 inline-block"></span>
          <i v-else class="fa-solid fa-code-compare mr-2"></i>
          生成对比图
        </button>
      </div>

      <div v-if="loadingComparison" class="text-center py-12">
        <div class="loader mx-auto mb-4" style="width: 40px; height: 40px;"></div>
        <p class="text-gray-500">正在生成对比图表，请稍候...</p>
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div 
          v-for="chart in comparisonCharts" 
          :key="chart.name + chart.batch_num"
          class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 transition hover:shadow-md border-l-4 border-l-blue-500"
        >
          <h4 class="font-medium text-gray-700 mb-3 border-b pb-2 flex justify-between">
            <span>{{ chart.name }} (批次 {{ chart.batch_num }})</span>
            <span 
              v-if="chart.anomaly_count > 0" 
              class="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded"
            >
              异常: {{ chart.anomaly_count }}处
            </span>
          </h4>
          <img 
            :src="'data:image/png;base64,' + chart.image_base64" 
            :alt="chart.name"
            class="w-full rounded-lg"
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { chartApi } from '../api'

const activeTab = ref('single')
const batchSize = ref(100)
const batchNum = ref(null)

const signals = ref([])
const signal1 = ref('')
const signal2 = ref('')

const trendCharts = ref([])
const comparisonCharts = ref([])
const loadingTrends = ref(false)
const loadingComparison = ref(false)

// Data source state
const dataSource = ref({ current_source: 'replay.db', is_custom: false })
const uploading = ref(false)
const uploadMessage = ref('')
const uploadSuccess = ref(false)
const fileInput = ref(null)

async function fetchDataSource() {
  try {
    const response = await chartApi.getDataSource()
    dataSource.value = response.data
  } catch (error) {
    console.error('Failed to fetch data source:', error)
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  
  uploading.value = true
  uploadMessage.value = ''
  
  try {
    const response = await chartApi.uploadDb(file)
    uploadMessage.value = `${response.data.message} - ${response.data.records} 条记录`
    uploadSuccess.value = true
    await fetchDataSource()
    await fetchSignals()  // Refresh signals for new database
  } catch (error) {
    uploadMessage.value = error.response?.data?.detail || '上传失败'
    uploadSuccess.value = false
  }
  
  uploading.value = false
  event.target.value = ''  // Reset file input
  
  setTimeout(() => { uploadMessage.value = '' }, 5000)
}

async function resetDataSource() {
  try {
    await chartApi.resetDb()
    await fetchDataSource()
    await fetchSignals()
    uploadMessage.value = '已恢复使用默认数据库'
    uploadSuccess.value = true
    setTimeout(() => { uploadMessage.value = '' }, 3000)
  } catch (error) {
    uploadMessage.value = error.response?.data?.detail || '恢复失败'
    uploadSuccess.value = false
  }
}

async function fetchSignals() {
  try {
    const response = await chartApi.getSignals()
    signals.value = response.data.signals || []
  } catch (error) {
    console.error('Failed to fetch signals:', error)
  }
}

async function generateTrends() {
  loadingTrends.value = true
  trendCharts.value = []
  try {
    const response = await chartApi.generateTrends(batchSize.value, batchNum.value || null)
    trendCharts.value = response.data.charts || []
  } catch (error) {
    console.error('Failed to generate trends:', error)
    alert(error.response?.data?.detail || '生成图表失败')
  }
  loadingTrends.value = false
}

async function generateComparison() {
  if (!signal1.value || !signal2.value) return
  
  loadingComparison.value = true
  comparisonCharts.value = []
  try {
    const response = await chartApi.generateComparison(
      signal1.value, 
      signal2.value, 
      batchSize.value, 
      batchNum.value || null
    )
    comparisonCharts.value = response.data.charts || []
  } catch (error) {
    console.error('Failed to generate comparison:', error)
    alert(error.response?.data?.detail || '生成对比图失败')
  }
  loadingComparison.value = false
}

onMounted(() => {
  fetchDataSource()
  fetchSignals()
})
</script>
