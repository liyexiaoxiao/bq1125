import { reactive, readonly } from 'vue'

// 简单的响应式状态管理
const state = reactive({
  systemStatus: 'ready', // 'ready' | 'running' | 'stopped'
  runs: 0,
  goal: 1000,
  exceptions: 0,
  isRunning: false,
  logs: [],
  dashboardLogs: []
})

export function useTestStore() {
  const setSystemStatus = (status) => {
    state.systemStatus = status
  }

  const setRunning = (running) => {
    state.isRunning = running
    if (running) {
      state.systemStatus = 'running'
    }
  }

  const updateStatus = (data) => {
    if (typeof data.runs === 'number') state.runs = data.runs
    if (typeof data.goal === 'number') state.goal = data.goal
    if (typeof data.exceptions === 'number') state.exceptions = data.exceptions
    state.isRunning = !!data.running
    
    if (data.running) {
      state.systemStatus = 'running'
    } else if (state.systemStatus === 'running') {
      state.systemStatus = 'stopped'
    }
  }

  const setLogs = (logs) => {
    state.logs = logs
  }

  const addDashboardLog = (level, message) => {
    const time = new Date().toLocaleTimeString()
    state.dashboardLogs.unshift({ level, message, time })
    // 保留最新的100条
    if (state.dashboardLogs.length > 100) {
      state.dashboardLogs.pop()
    }
  }

  const clearDashboardLogs = () => {
    state.dashboardLogs = []
  }

  const reset = () => {
    state.runs = 0
    state.exceptions = 0
    state.systemStatus = 'ready'
    state.isRunning = false
  }

  return {
    // 状态（只读）
    systemStatus: readonly(state).systemStatus,
    runs: readonly(state).runs,
    goal: readonly(state).goal,
    exceptions: readonly(state).exceptions,
    isRunning: readonly(state).isRunning,
    logs: readonly(state).logs,
    dashboardLogs: readonly(state).dashboardLogs,
    
    // 直接访问state用于computed
    state,
    
    // 方法
    setSystemStatus,
    setRunning,
    updateStatus,
    setLogs,
    addDashboardLog,
    clearDashboardLogs,
    reset
  }
}
