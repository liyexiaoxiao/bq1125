<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="bg-white p-8 rounded-lg shadow-md w-96 fade-in">
      <h2 class="text-2xl font-bold mb-6 text-center text-gray-800">系统登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="username">用户名</label>
          <input
            v-model="username"
            type="text"
            id="username"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="请输入用户名"
            required
          />
        </div>
        <div class="mb-6">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="password">密码</label>
          <input
            v-model="password"
            type="password"
            id="password"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="请输入密码"
            required
          />
        </div>
        <div v-if="errorMsg" class="mb-4 text-red-500 text-sm text-center">
          {{ errorMsg }}
        </div>
        <div class="flex items-center justify-between">
          <button
            type="submit"
            class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 btn-active"
            :disabled="loading"
          >
            <span v-if="loading" class="loader inline-block align-middle mr-2 w-4 h-4"></span>
            <span v-else>登录</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  errorMsg.value = ''
  
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })
    
    // Check if response is valid JSON
    const contentType = response.headers.get("content-type");
    let data = {};
    if (contentType && contentType.indexOf("application/json") !== -1) {
        data = await response.json();
    } else {
        throw new Error("Invalid response from server");
    }
    
    if (response.ok && data.code === 200) {
      localStorage.setItem('isAuthenticated', 'true')
      // Store user info if available
      if (data.msg === '登录成功') {
          // nothing else to store currently
      }
      router.push('/dashboard')
    } else {
      errorMsg.value = data.msg || '登录失败'
    }
  } catch (error) {
    errorMsg.value = '请求出错，请稍后重试'
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>
