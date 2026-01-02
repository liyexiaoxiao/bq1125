import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

// 导入页面组件
import Dashboard from './views/Dashboard.vue'
import Config from './views/Config.vue'
import Logs from './views/Logs.vue'
import Login from './views/Login.vue'
import Users from './views/Users.vue'
import Charts from './views/Charts.vue'

// 路由配置
const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'login', component: Login, meta: { title: '用户登录' } },
  { path: '/dashboard', name: 'dashboard', component: Dashboard, meta: { title: '系统仪表盘' } },
  { path: '/charts', name: 'charts', component: Charts, meta: { title: '数据图表' } },
  { path: '/config', name: 'config', component: Config, meta: { title: '系统配置' } },
  { path: '/logs', name: 'logs', component: Logs, meta: { title: '详细运行日志' } },
  { path: '/users', name: 'users', component: Users, meta: { title: '用户管理' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title + ' - 系统'
  }

  if (to.path === '/login') {
    next()
    return
  }

  const isAuth = localStorage.getItem('isAuthenticated')
  if (!isAuth) {
    next('/login')
    return
  }

  next()
})

const app = createApp(App)
app.use(router)
app.mount('#app')
