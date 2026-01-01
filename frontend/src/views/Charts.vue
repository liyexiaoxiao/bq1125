<template>
  <div class="space-y-6 fade-in">
    <!-- 工具栏 -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div class="flex flex-wrap items-center gap-4 w-full lg:w-auto">
          <!-- 导入数据库 -->
          <button 
            @click="triggerDbUpload"
            class="flex items-center px-4 py-2 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-sm font-medium hover:bg-indigo-100 transition"
          >
            <i class="fa-solid fa-upload mr-2"></i> 导入数据库 (.db)
          </button>
          <input 
            ref="dbUploadInput"
            type="file" 
            class="hidden" 
            accept=".db,.sqlite"
            @change="handleDbUpload"
          >
          
          <span v-if="currentDbName" class="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-lg">
            <i class="fa-solid fa-database mr-1 text-indigo-500"></i>
            {{ currentDbName }}
          </span>

          <div class="h-8 w-px bg-gray-300 mx-2 hidden md:block"></div>

          <div class="flex items-center gap-2">
            <label class="font-medium text-gray-700 whitespace-nowrap">选择轮次:</label>
            <select 
              v-model="selectedRound"
              @change="fetchChartData"
              class="form-select rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 py-2 px-3 border bg-white"
            >
              <option value="all">全部轮次</option>
              <option v-for="round in rounds" :key="round" :value="round">
                轮次 #{{ round }}
              </option>
            </select>
          </div>

          <div class="flex items-center gap-2">
            <label class="font-medium text-gray-700 whitespace-nowrap">数据范围:</label>
            <input 
              v-model.number="startIndex" 
              type="number" 
              min="1"
              placeholder="起始"
              class="w-24 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 py-2 px-3 border bg-white"
            />
            <span class="text-gray-500">-</span>
            <input 
              v-model.number="endIndex" 
              type="number" 
              min="1"
              placeholder="结束"
              class="w-24 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 py-2 px-3 border bg-white"
            />
          </div>
        </div>
        
        <button 
          @click="fetchChartData"
          class="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
        >
          <i class="fa-solid fa-sync mr-2"></i> 刷新数据
        </button>
      </div>

      <!-- 信号选择器 -->
      <div class="mt-4 pt-4 border-t border-gray-200">
        <div class="flex flex-wrap items-center gap-4">
          <!-- 查看模式选择 -->
          <div class="flex items-center gap-2">
            <label class="font-medium text-gray-700 whitespace-nowrap">查看模式:</label>
            <div class="flex bg-gray-100 p-1 rounded-lg">
              <button 
                @click="viewMode = 'single'; renderSignalChart()"
                class="px-4 py-1.5 rounded-md text-sm font-medium transition"
                :class="viewMode === 'single' 
                  ? 'bg-white text-gray-800 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'"
              >
                <i class="fa-solid fa-chart-simple mr-1"></i> 单信号
              </button>
              <button 
                @click="viewMode = 'compare'; renderSignalChart()"
                class="px-4 py-1.5 rounded-md text-sm font-medium transition"
                :class="viewMode === 'compare' 
                  ? 'bg-white text-gray-800 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'"
              >
                <i class="fa-solid fa-code-compare mr-1"></i> 对比信号
              </button>
            </div>
          </div>

          <div class="h-8 w-px bg-gray-300 mx-1 hidden md:block"></div>

          <div class="flex items-center gap-2">
            <label class="font-medium text-gray-700 whitespace-nowrap">{{ viewMode === 'single' ? '选择信号:' : '信号1:' }}</label>
            <select 
              v-model="signal1"
              @change="renderSignalChart"
              class="form-select rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 py-2 px-3 border bg-white min-w-[200px]"
            >
              <option value="">-- 选择信号 --</option>
              <option v-for="sig in availableSignals" :key="sig" :value="sig">{{ sig }}</option>
            </select>
          </div>
          <div v-if="viewMode === 'compare'" class="flex items-center gap-2">
            <label class="font-medium text-gray-700 whitespace-nowrap">信号2:</label>
            <select 
              v-model="signal2"
              @change="renderSignalChart"
              class="form-select rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 py-2 px-3 border bg-white min-w-[200px]"
            >
              <option value="">-- 选择信号 --</option>
              <option v-for="sig in availableSignals" :key="sig" :value="sig">{{ sig }}</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <label class="font-medium text-gray-700 whitespace-nowrap">数据源:</label>
            <select 
              v-model="dataSource"
              @change="renderSignalChart"
              class="form-select rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 py-2 px-3 border bg-white"
            >
              <option value="actual_output">实际输出</option>
              <option value="expected_output">预期输出</option>
              <option value="actual_input">实际输入</option>
            </select>
          </div>
          <label v-if="viewMode === 'compare'" class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="showAnomalies" @change="renderSignalChart" class="rounded border-gray-300">
            <span class="text-sm text-gray-700">标记异常</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">总测试次数</p>
            <p class="text-2xl font-bold text-gray-800">{{ stats.total }}</p>
          </div>
          <div class="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <i class="fa-solid fa-list-ol text-xl"></i>
          </div>
        </div>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">正常</p>
            <p class="text-2xl font-bold text-green-600">{{ stats.normal }}</p>
          </div>
          <div class="p-3 bg-green-50 text-green-600 rounded-lg">
            <i class="fa-solid fa-check text-xl"></i>
          </div>
        </div>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">异常</p>
            <p class="text-2xl font-bold text-red-600">{{ stats.error }}</p>
          </div>
          <div class="p-3 bg-red-50 text-red-600 rounded-lg">
            <i class="fa-solid fa-xmark text-xl"></i>
          </div>
        </div>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">{{ viewMode === 'compare' ? '发现异常点' : '数据点数' }}</p>
            <p class="text-2xl font-bold" :class="viewMode === 'compare' ? 'text-orange-600' : 'text-purple-600'">
              {{ viewMode === 'compare' ? anomalyCount : tableData.length }}
            </p>
          </div>
          <div class="p-3 rounded-lg" :class="viewMode === 'compare' ? 'bg-orange-50 text-orange-600' : 'bg-purple-50 text-purple-600'">
            <i :class="viewMode === 'compare' ? 'fa-solid fa-triangle-exclamation' : 'fa-solid fa-chart-simple'" class="text-xl"></i>
          </div>
        </div>
      </div>
    </div>

    <!-- 执行时间趋势图表 -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div class="flex justify-between items-center mb-4">
        <h3 class="font-semibold text-gray-800">
          <i class="fa-solid fa-chart-line mr-2 text-blue-600"></i>
          {{ viewMode === 'single' ? '信号趋势图' : '信号对比图' }}
          <span v-if="signal1" class="text-sm font-normal text-gray-500 ml-2">
            {{ signal1 }} <span v-if="viewMode === 'compare' && signal2">vs {{ signal2 }}</span>
          </span>
        </h3>
        <div v-if="viewMode === 'compare' && anomalyCount > 0" class="text-sm text-red-600">
          <i class="fa-solid fa-exclamation-circle mr-1"></i>
          发现 {{ anomalyCount }} 处异常
        </div>
      </div>
      <div class="h-96">
        <canvas ref="signalChart"></canvas>
      </div>
    </div>

    <!-- 异常数据列表 (仅对比模式显示) -->
    <div v-if="viewMode === 'compare' && anomalies.length > 0" class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-red-50">
        <h3 class="font-semibold text-red-800">
          <i class="fa-solid fa-bug mr-2"></i>
          异常数据详情 (信号值不一致)
        </h3>
        <span class="text-sm text-red-600">共 {{ anomalies.length }} 处</span>
      </div>
      <div class="overflow-x-auto max-h-64">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 sticky top-0">
            <tr>
              <th class="px-4 py-3 text-left font-medium text-gray-600">数据序号</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">Run ID</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">{{ signal1 }} 值</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">{{ signal2 }} 值</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="a in anomalies" :key="a.dataIndex" class="hover:bg-red-50">
              <td class="px-4 py-3 font-mono">第 {{ a.dataIndex }} 个</td>
              <td class="px-4 py-3 font-mono">{{ a.runId }}</td>
              <td class="px-4 py-3">{{ a.value1 }}</td>
              <td class="px-4 py-3">{{ a.value2 }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
        <h3 class="font-semibold text-gray-800">
          <i class="fa-solid fa-table mr-2"></i>
          测试记录
        </h3>
        <span class="text-sm text-gray-500">显示 {{ tableData.length }} 条</span>
      </div>
      <div class="overflow-x-auto max-h-96">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 sticky top-0">
            <tr>
              <th class="px-4 py-3 text-left font-medium text-gray-600">序号</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">Run ID</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">轮次</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">类型</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">状态</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">策略</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">预期时间</th>
              <th class="px-4 py-3 text-left font-medium text-gray-600">实际时间</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="(row, idx) in tableData" :key="row.run_id" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-gray-500">{{ idx + 1 }}</td>
              <td class="px-4 py-3 font-mono">{{ row.run_id }}</td>
              <td class="px-4 py-3">{{ row.round_id }}</td>
              <td class="px-4 py-3">
                <span :class="typeClass(row.type)">{{ typeText(row.type) }}</span>
              </td>
              <td class="px-4 py-3">
                <span :class="statusClass(row.status)">{{ statusText(row.status) }}</span>
              </td>
              <td class="px-4 py-3">
                <span :class="strategyClass(row.strategy)">{{ row.strategy }}</span>
              </td>
              <td class="px-4 py-3">{{ row.expected_duration }}ms</td>
              <td class="px-4 py-3">{{ row.actual_duration }}ms</td>
            </tr>
            <tr v-if="tableData.length === 0">
              <td colspan="8" class="px-4 py-8 text-center text-gray-400">
                <i class="fa-solid fa-database text-2xl mb-2"></i>
                <p>暂无数据，请导入数据库或刷新</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { chartsApi } from '../api'

let Chart = null

const signalChart = ref(null)
const dbUploadInput = ref(null)

const selectedRound = ref('all')
const startIndex = ref(1)
const endIndex = ref(100)
const currentDbName = ref('')

// 查看模式: 'single' 单信号 | 'compare' 对比信号
const viewMode = ref('single')

// 信号相关
const signal1 = ref('')
const signal2 = ref('')
const dataSource = ref('actual_output')
const showAnomalies = ref(true)
const availableSignals = ref([])
const anomalies = ref([])

const rounds = ref([])
const tableData = ref([])
const rawRecords = ref([])
const stats = ref({
  total: 0,
  normal: 0,
  error: 0,
  avgDuration: 0
})

const anomalyCount = computed(() => anomalies.value.length)

let signalChartInstance = null

const statusText = (status) => {
  const map = { 1: '正常', 2: '错误', 3: '卡住', 4: '新状态' }
  return map[status] || '未知'
}

const statusClass = (status) => {
  const map = {
    1: 'px-2 py-1 bg-green-100 text-green-700 rounded text-xs',
    2: 'px-2 py-1 bg-red-100 text-red-700 rounded text-xs',
    3: 'px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs',
    4: 'px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs'
  }
  return map[status] || 'px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs'
}

const typeText = (type) => type === 1 ? '唤醒' : '休眠'

const typeClass = (type) => {
  return type === 1 
    ? 'px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs'
    : 'px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs'
}

const strategyClass = (strategy) => {
  if (strategy < 0) return 'px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-mono'
  return 'px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-mono'
}

const triggerDbUpload = () => {
  dbUploadInput.value?.click()
}

const handleDbUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  currentDbName.value = file.name
  
  // 上传数据库文件到后端
  const formData = new FormData()
  formData.append('db_file', file)
  
  try {
    await chartsApi.uploadDb(formData)
    // 上传成功后刷新数据
    await fetchChartData()
  } catch (e) {
    console.error('上传数据库失败:', e)
    alert('上传数据库失败: ' + e.message)
  }
  
  // 清空 input 以便重复选择同一文件
  event.target.value = ''
}

const loadChartJs = () => {
  return new Promise((resolve, reject) => {
    if (window.Chart) {
      Chart = window.Chart
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js'
    script.onload = () => {
      Chart = window.Chart
      resolve()
    }
    script.onerror = reject
    document.head.appendChild(script)
  })
}

const fetchChartData = async () => {
  try {
    const roundParam = selectedRound.value === 'all' ? null : selectedRound.value
    const res = await chartsApi.getData(roundParam, startIndex.value, endIndex.value)
    const data = res.data

    rounds.value = data.rounds || []
    tableData.value = data.records || []
    rawRecords.value = data.records || []
    stats.value = data.stats || { total: 0, normal: 0, error: 0, avgDuration: 0 }
    
    // 提取可用信号列表
    extractSignals(data.records || [])

    await nextTick()
    renderSignalChart()
  } catch (e) {
    console.error('Failed to fetch chart data:', e)
  }
}

const extractSignals = (records) => {
  const signalSet = new Set()
  
  for (const record of records) {
    const sources = ['actual_output', 'expected_output', 'actual_input']
    for (const src of sources) {
      const jsonData = record[src]
      if (jsonData && typeof jsonData === 'object') {
        const dataList = jsonData.data || []
        if (Array.isArray(dataList)) {
          for (const item of dataList) {
            if (item.name) signalSet.add(item.name)
          }
        }
      }
    }
  }
  
  availableSignals.value = Array.from(signalSet).sort()
  
  // 默认选择前两个信号
  if (availableSignals.value.length > 0 && !signal1.value) {
    signal1.value = availableSignals.value[0]
  }
  if (availableSignals.value.length > 1 && !signal2.value) {
    signal2.value = availableSignals.value[1]
  }
}

const renderSignalChart = () => {
  if (!Chart || !signal1.value) return
  
  const ctx = signalChart.value?.getContext('2d')
  if (!ctx) return
  
  if (signalChartInstance) {
    signalChartInstance.destroy()
  }
  
  const records = rawRecords.value
  const labels = []
  const data1 = []
  const data2 = []
  anomalies.value = []
  
  records.forEach((record, idx) => {
    const runId = record.run_id
    const jsonData = record[dataSource.value]
    
    if (!jsonData || typeof jsonData !== 'object') return
    
    const dataList = jsonData.data || []
    if (!Array.isArray(dataList)) return
    
    let val1 = null
    let val2 = null
    
    for (const item of dataList) {
      if (item.name === signal1.value) val1 = item.value
      if (viewMode.value === 'compare' && signal2.value && item.name === signal2.value) val2 = item.value
    }
    
    if (val1 !== null) {
      labels.push(runId)
      data1.push(val1)
      data2.push(val2)
      
      // 对比模式下检测异常（两个信号值不同）
      if (viewMode.value === 'compare' && signal2.value && val2 !== null && val1 !== val2) {
        anomalies.value.push({
          dataIndex: idx + 1,
          runId: runId,
          value1: val1,
          value2: val2
        })
      }
    }
  })
  
  const datasets = [{
    label: signal1.value,
    data: data1,
    borderColor: 'rgb(59, 130, 246)',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    fill: viewMode.value === 'single',
    tension: 0.2,
    pointRadius: 3
  }]
  
  // 对比模式下添加第二个信号
  if (viewMode.value === 'compare' && signal2.value) {
    datasets.push({
      label: signal2.value,
      data: data2,
      borderColor: 'rgb(34, 197, 94)',
      backgroundColor: 'rgba(34, 197, 94, 0.1)',
      fill: false,
      tension: 0.2,
      pointRadius: 3,
      borderDash: [5, 5]
    })
  }
  
  // 对比模式下添加异常标记
  if (viewMode.value === 'compare' && showAnomalies.value && anomalies.value.length > 0) {
    const anomalyData = labels.map((label, idx) => {
      const isAnomaly = anomalies.value.some(a => a.dataIndex === label)
      return isAnomaly ? Math.max(data1[idx] || 0, data2[idx] || 0) : null
    })
    
    datasets.push({
      label: '异常点',
      data: anomalyData,
      borderColor: 'rgb(239, 68, 68)',
      backgroundColor: 'rgb(239, 68, 68)',
      pointRadius: 8,
      pointStyle: 'triangle',
      showLine: false
    })
  }
  
  signalChartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            title: (items) => `run_id: ${items[0].label}`
          }
        }
      },
      scales: {
        x: { 
          title: { display: true, text: 'run_id' }
        },
        y: { 
          title: { display: true, text: '信号值' }
        }
      }
    }
  })
}

onMounted(async () => {
  await loadChartJs()
  await fetchChartData()
})

onUnmounted(() => {
  if (signalChartInstance) signalChartInstance.destroy()
})
</script>
