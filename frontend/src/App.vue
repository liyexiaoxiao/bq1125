<template>
  <div class="h-screen flex overflow-hidden bg-gray-100">
    <!-- Sidebar -->
    <Sidebar v-if="!isLoginPage" />
    
    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0 bg-gray-50">
      <!-- Top Header -->
      <Header v-if="!isLoginPage" />
      
      <!-- Content Area -->
      <div class="flex-1 overflow-auto" :class="isLoginPage ? '' : 'p-6'">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
    
    <!-- Help Modal -->
    <HelpModal :visible="showHelp" @update:visible="showHelp = $event" />
  </div>
</template>

<script setup>
import { ref, provide, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import Header from './components/Header.vue'
import HelpModal from './components/HelpModal.vue'

const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')

const showHelp = ref(false)

// 提供全局状态
provide('showHelp', showHelp)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
