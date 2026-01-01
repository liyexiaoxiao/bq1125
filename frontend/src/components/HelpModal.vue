<template>
  <Teleport to="body">
    <div 
      v-if="visible" 
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
      @click.self="close"
    >
      <div class="bg-white rounded-xl shadow-xl w-11/12 max-w-md p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">帮助</h3>
          <button @click="close" class="text-gray-500 hover:text-gray-700">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
        <div class="text-sm text-gray-600 space-y-2">
          <p>顶部显示系统名称与当前用户/角色信息。</p>
          <p>点击"帮助"按钮可打开此窗口。</p>
          <p class="mt-4 pt-4 border-t border-gray-200">
            <strong>功能说明：</strong>
          </p>
          <ul class="list-disc list-inside space-y-1 ml-2">
            <li><strong>仪表盘</strong> - 查看测试运行状态和实时日志</li>
            <li><strong>批次分析报告</strong> - 分析历史测试数据</li>
            <li><strong>系统配置</strong> - 修改测试参数配置</li>
            <li><strong>运行日志</strong> - 查看完整运行日志</li>
          </ul>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible'])

const close = () => {
  emit('update:visible', false)
}
</script>
