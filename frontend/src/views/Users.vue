<template>
  <div class="max-w-6xl mx-auto fade-in">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 class="font-semibold text-gray-800 text-lg mb-4">用户管理</h3>
      
      <div v-if="isAdmin" class="mb-8">
        <!-- Add User Form -->
        <div class="mb-8 p-4 bg-gray-50 rounded-lg">
            <h4 class="text-sm font-bold text-gray-700 mb-4">添加新用户</h4>
            <form @submit.prevent="addUser" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                <input v-model="newUser.username" type="text" required 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
                <input v-model="newUser.password" type="password" required 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">姓名</label>
                <input v-model="newUser.name" type="text" 
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2">
            </div>
            <button type="submit" 
                class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition h-10" 
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

        <!-- User List Table -->
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户名</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">姓名</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">创建时间</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="user in users" :key="user.userId">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ user.userName }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ user.nickName }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ user.createTime }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                            <button @click="openEditModal(user)" class="text-indigo-600 hover:text-indigo-900">编辑</button>
                            <button @click="deleteUser(user.userId)" class="text-red-600 hover:text-red-900" :disabled="user.userName === 'admin'">删除</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
      </div>

      <div v-else class="text-center py-12">
        <div class="inline-block p-4 bg-gray-100 rounded-full mb-4">
          <i class="fa-solid fa-lock text-gray-400 text-3xl"></i>
        </div>
        <p class="text-gray-500">Only admin can manage users.</p>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
        <div class="bg-white p-8 rounded-lg shadow-xl w-96">
            <h3 class="text-lg font-semibold mb-4">编辑用户</h3>
            <form @submit.prevent="updateUser" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">用户名</label>
                    <input v-model="editingUser.userName" type="text" disabled
                        class="mt-1 block w-full rounded-md border-gray-300 bg-gray-100 shadow-sm border p-2">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">姓名</label>
                    <input v-model="editingUser.nickName" type="text" 
                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2">
                </div>
                
                <div class="flex justify-end space-x-2 mt-6">
                    <button type="button" @click="showEditModal = false" class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">取消</button>
                    <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">保存</button>
                </div>
            </form>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const newUser = ref({ username: '', password: '', name: '' })
const users = ref([])
const loading = ref(false)
const msg = ref('')
const msgType = ref('')
const isAdmin = ref(false)
const showEditModal = ref(false)
const editingUser = ref({})

const checkAuth = async () => {
    try {
        const res = await fetch('/api/check_auth')
        const data = await res.json()
        if (data.username === 'admin') {
            isAdmin.value = true
            fetchUsers()
        }
    } catch (e) {
        console.error(e)
    }
}

const fetchUsers = async () => {
    try {
        const res = await fetch('/system/user/list')
        const data = await res.json()
        if (data.code === 200) {
            users.value = data.rows
        }
    } catch (e) {
        console.error('Failed to fetch users', e)
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
      fetchUsers()
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

const deleteUser = async (userId) => {
    if (!confirm('确定要删除该用户吗？')) return
    
    try {
        const res = await fetch(`/system/user/${userId}`, {
            method: 'DELETE'
        })
        const data = await res.json()
        if (data.code === 200) {
            fetchUsers()
        } else {
            alert(data.msg || '删除失败')
        }
    } catch (e) {
        alert('删除失败')
    }
}

const openEditModal = (user) => {
    editingUser.value = { ...user }
    showEditModal.value = true
}

const updateUser = async () => {
    try {
        const res = await fetch('/system/user/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: editingUser.value.userId,
                userName: editingUser.value.userName,
                nickName: editingUser.value.nickName
            })
        })
        const data = await res.json()
        if (data.code === 200) {
            showEditModal.value = false
            fetchUsers()
        } else {
            alert(data.msg || '更新失败')
        }
    } catch (e) {
        alert('更新失败')
    }
}

onMounted(() => {
    checkAuth()
})
</script>
