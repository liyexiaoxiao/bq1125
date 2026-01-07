import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
    const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
    const token = ref(localStorage.getItem('token') || null)

    const isLoggedIn = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')
    const username = computed(() => user.value?.username || '')

    async function login(usernameVal, password) {
        try {
            const response = await authApi.login(usernameVal, password)
            token.value = response.data.access_token
            localStorage.setItem('token', token.value)

            // Get user info
            const userResponse = await authApi.getMe()
            user.value = userResponse.data
            localStorage.setItem('user', JSON.stringify(user.value))

            return { success: true }
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || '登录失败'
            }
        }
    }

    function logout() {
        token.value = null
        user.value = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
    }

    return {
        user,
        token,
        isLoggedIn,
        isAdmin,
        username,
        login,
        logout
    }
})
