<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md fade-in">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-xl mb-4">
          <i class="fa-solid fa-car-burst text-white text-2xl"></i>
        </div>
        <h1 class="text-2xl font-bold text-gray-900">北汽模糊测试系统</h1>
        <p class="text-gray-500 mt-2">Fuzz Test Control Panel</p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
              <i class="fa-solid fa-user"></i>
            </span>
            <input
              v-model="username"
              type="text"
              required
              class="block w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              placeholder="请输入用户名"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
              <i class="fa-solid fa-lock"></i>
            </span>
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              class="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              placeholder="请输入密码"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
            >
              <i :class="showPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye'"></i>
            </button>
          </div>
        </div>

        <div v-if="error" class="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          <i class="fa-solid fa-circle-exclamation mr-2"></i>{{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full flex items-center justify-center py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading" class="loader mr-2"></span>
          <span>{{ loading ? '登录中...' : '登录' }}</span>
        </button>
      </form>

      <!-- Footer -->
      <div class="mt-8 text-center text-sm text-gray-400">
        <p>© 2024 北汽集团 · 模糊测试平台</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''

  const result = await authStore.login(username.value, password.value)

  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error
  }

  loading.value = false
}
</script>
