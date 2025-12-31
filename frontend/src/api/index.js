import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 10000
})

// 控制接口
export const controlApi = {
  // 启动测试
  start: () => api.post('/control/start'),
  
  // 停止测试
  stop: () => api.post('/control/stop'),
  
  // 获取状态
  getStatus: () => api.get('/control/status')
}

// 日志接口
export const logsApi = {
  // 获取最新日志
  tail: (lines = 200) => api.get('/logs/tail', { params: { lines } })
}

// 导出接口
export const exportApi = {
  // 导出测试数据
  download: async () => {
    const response = await api.get('/export', { responseType: 'blob' })
    return response.data
  }
}

// 配置接口
export const configApi = {
  // 获取配置
  get: () => api.get('/config'),
  
  // 保存配置
  save: (config) => api.post('/config', config)
}

// 图表数据接口
export const chartsApi = {
  // 获取图表数据
  getData: (roundId = null, start = 1, end = 100) => {
    const params = { start, end }
    if (roundId) params.round_id = roundId
    return api.get('/charts/data', { params })
  },
  
  // 上传数据库文件
  uploadDb: (formData) => {
    return api.post('/charts/upload-db', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    })
  }
}

export default api
