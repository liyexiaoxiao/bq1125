<template>
  <div class="max-w-4xl mx-auto fade-in">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 class="font-semibold text-gray-800 text-lg mb-4">用户管理</h3>
      
      <div v-if="isAdmin" class="mb-8">
        <h4 class="text-sm font-bold text-gray-700 mb-2">添加新用户</h4>
        <form @submit.prevent="addUser" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">用户名</label>
            <input v-model="newUser.username" type="text" required 
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">密码</label>
            <input v-model="newUser.password" type="password" required 
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">姓名</label>
            <input v-model="newUser.name" type="text" 
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2">
          </div>
          <button type="submit" 
            class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition" 
            :disabled="loading">
            {{ loading ? '添加中...' : '添加用户' }}
          </button>
        </form>
        <p v-if="msg" class="mt-4 p-2 rounded text-sm" 
           :class="msgType === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
           <i :class="msgType === 'success' ? 'fa-solid fa-check-circle' : 'fa-solid fa-circle-exclamation'" class="mr-2"></i>
           {{ msg }}
        </p>
      </div>

      <div v-else class="text-center py-12">
        <div class="inline-block p-4 bg-gray-100 rounded-full mb-4">
          <i class="fa-solid fa-lock text-gray-400 text-3xl"></i>
        </div>
        <p class="text-gray-500">Only admin can manage users.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const newUser = ref({ username: '', password: '', name: '' })
const loading = ref(false)
const msg = ref('')
const msgType = ref('')
const isAdmin = ref(false)

const checkAuth = async () => {
    try {
        const res = await fetch('/api/check_auth')
        const data = await res.json()
        if (data.username === 'admin') {
            isAdmin.value = true
        }
    } catch (e) {
        console.error(e)
    }
}

const addUser = async () => {
  loading.value = true
  msg.value = ''
  try {
    const res = await fetch('/api/user/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newUser.value)
    })
    const data = await res.json()
    if (data.code === 200) {
      msg.value = '用户添加成功'
      msgType.value = 'success'
      newUser.value = { username: '', password: '', name: '' }
    } else {
      msg.value = data.msg || '操作失败'
      msgType.value = 'error'
    }
  } catch (e) {
    msg.value = '请求失败，请稍后重试'
    msgType.value = 'error'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
    checkAuth()
})
</script>
