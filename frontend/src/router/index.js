import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/analysis',
        name: 'Analysis',
        component: () => import('../views/Charts.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/config',
        name: 'Config',
        component: () => import('../views/Config.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/logs',
        name: 'Logs',
        component: () => import('../views/Logs.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { requiresAuth: true, requiresAdmin: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    const user = JSON.parse(localStorage.getItem('user') || '{}')

    if (to.meta.requiresAuth && !token) {
        next('/login')
    } else if (to.meta.requiresAdmin && user.role !== 'admin') {
        next('/')
    } else if (to.path === '/login' && token) {
        next('/')
    } else {
        next()
    }
})

export default router
