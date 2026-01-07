<template>
  <div class="max-w-4xl mx-auto fade-in">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <!-- Header -->
      <div class="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
        <div>
          <h3 class="font-semibold text-gray-800 text-lg">用户管理</h3>
          <p class="text-sm text-gray-500">管理系统用户账户（仅管理员可见）</p>
        </div>
        <button 
          @click="showAddModal = true"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
        >
          <i class="fa-solid fa-plus mr-2"></i>添加用户
        </button>
      </div>

      <!-- User List -->
      <div class="p-6">
        <div v-if="loading" class="text-center py-8">
          <div class="loader mx-auto mb-4"></div>
          <p class="text-gray-500">加载用户列表...</p>
        </div>

        <table v-else class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="text-left px-4 py-3 text-sm font-semibold text-gray-600">用户名</th>
              <th class="text-left px-4 py-3 text-sm font-semibold text-gray-600">角色</th>
              <th class="text-left px-4 py-3 text-sm font-semibold text-gray-600">状态</th>
              <th class="text-left px-4 py-3 text-sm font-semibold text-gray-600">创建时间</th>
              <th class="text-right px-4 py-3 text-sm font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
              <td class="px-4 py-4">
                <div class="flex items-center">
                  <div class="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mr-3">
                    <i class="fa-solid fa-user text-sm"></i>
                  </div>
                  <span class="font-medium text-gray-900">{{ user.username }}</span>
                </div>
              </td>
              <td class="px-4 py-4">
                <span 
                  class="px-2 py-1 rounded-full text-xs font-medium"
                  :class="user.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'"
                >
                  {{ user.role === 'admin' ? '管理员' : '普通用户' }}
                </span>
              </td>
              <td class="px-4 py-4">
                <span 
                  class="px-2 py-1 rounded-full text-xs font-medium"
                  :class="user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                >
                  {{ user.is_active ? '正常' : '禁用' }}
                </span>
              </td>
              <td class="px-4 py-4 text-sm text-gray-500">
                {{ formatDate(user.created_at) }}
              </td>
              <td class="px-4 py-4 text-right">
                <button 
                  v-if="user.username !== 'admin'"
                  @click="deleteUser(user)"
                  class="text-red-500 hover:text-red-700 text-sm"
                >
                  <i class="fa-solid fa-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add User Modal -->
    <div 
      v-if="showAddModal" 
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
      @click.self="showAddModal = false"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-800">添加新用户</h3>
          <button @click="showAddModal = false" class="text-gray-500 hover:text-gray-700">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <form @submit.prevent="addUser" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <input 
              v-model="newUser.username" 
              type="text" 
              required
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <input 
              v-model="newUser.password" 
              type="password" 
              required
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">角色</label>
            <select 
              v-model="newUser.role"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
            >
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>

          <div v-if="addError" class="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {{ addError }}
          </div>

          <div class="flex justify-end space-x-3 pt-4">
            <button 
              type="button"
              @click="showAddModal = false"
              class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              取消
            </button>
            <button 
              type="submit"
              :disabled="addLoading"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <span v-if="addLoading" class="loader mr-2 inline-block"></span>
              添加
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { userApi } from '../api'

const users = ref([])
const loading = ref(true)
const showAddModal = ref(false)
const addLoading = ref(false)
const addError = ref('')

const newUser = ref({
  username: '',
  password: '',
  role: 'user'
})

async function fetchUsers() {
  loading.value = true
  try {
    const response = await userApi.list()
    users.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch users:', error)
  }
  loading.value = false
}

async function addUser() {
  addLoading.value = true
  addError.value = ''
  try {
    await userApi.create(newUser.value)
    showAddModal.value = false
    newUser.value = { username: '', password: '', role: 'user' }
    await fetchUsers()
  } catch (error) {
    addError.value = error.response?.data?.detail || '添加用户失败'
  }
  addLoading.value = false
}

async function deleteUser(user) {
  if (!confirm(`确定要删除用户 "${user.username}" 吗？`)) return
  
  try {
    await userApi.delete(user.id)
    await fetchUsers()
  } catch (error) {
    alert(error.response?.data?.detail || '删除用户失败')
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(fetchUsers)
</script>
