<template>
  <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg border animate-slide-in"
      :class="toast.type === 'error' ? 'bg-red-50 border-red-200 text-red-800' : 'bg-green-50 border-green-200 text-green-800'"
    >
      <FeatherIcon
        :name="toast.type === 'error' ? 'alert-circle' : 'check-circle'"
        class="h-5 w-5 flex-shrink-0 mt-0.5"
        :class="toast.type === 'error' ? 'text-red-500' : 'text-green-500'"
      />
      <p class="text-sm flex-1">{{ toast.message }}</p>
      <button @click="dismissToast(toast.id)" class="flex-shrink-0 text-gray-400 hover:text-gray-600">
        <FeatherIcon name="x" class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'
import { useNotifications } from '@/composables/notifications'

const { toasts, dismissToast } = useNotifications()
</script>

<style scoped>
@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.animate-slide-in {
  animation: slideIn 0.3s ease-out;
}
</style>
