import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request interceptor - add JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor - handle 401 errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// Auth APIs
export const authApi = {
    login: (username, password) => {
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)
        return api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
    },
    getMe: () => api.get('/auth/me')
}

// User APIs
export const userApi = {
    list: () => api.get('/users'),
    create: (data) => api.post('/users', data),
    delete: (id) => api.delete(`/users/${id}`)
}

// Config APIs
export const configApi = {
    get: () => api.get('/config'),
    update: (config) => api.put('/config', { config })
}

// Process APIs
export const processApi = {
    status: () => api.get('/process/status'),
    start: () => api.post('/process/start'),
    stop: () => api.post('/process/stop'),
    export: () => api.get('/process/export', { responseType: 'blob' })
}

// Log APIs
export const logApi = {
    list: (logType = null) => api.get('/logs', { params: { log_type: logType } }),
    getLatest: (lines = 100, logType = 'main') =>
        api.get('/logs/latest', { params: { lines, log_type: logType } }),
    getContent: (filename, lines = 500) =>
        api.get(`/logs/${filename}`, { params: { lines } })
}

// Chart APIs
export const chartApi = {
    getSignals: () => api.get('/charts/signals'),
    generateTrends: (batchSize = 100, batchNum = null) =>
        api.post('/charts/signal-trends', { batch_size: batchSize, batch_num: batchNum }),
    generateComparison: (signal1, signal2, batchSize = 100, batchNum = null) =>
        api.post('/charts/comparison', {
            signal_name1: signal1,
            signal_name2: signal2,
            batch_size: batchSize,
            batch_num: batchNum
        }),
    uploadDb: (file) => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/charts/upload-db', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },
    resetDb: () => api.post('/charts/reset-db'),
    getDataSource: () => api.get('/charts/data-source')
}

export default api
