<template>
  <div
    class="flex h-12 flex-shrink-0 items-center justify-between gap-3 border-b border-[#E7DCC7] bg-canvas/70 px-4 backdrop-blur-sm sm:px-6"
  >
    <div class="flex min-w-0 items-center gap-2">
      <button
        @click="$emit('toggle-sidebar')"
        class="grid size-8 place-items-center rounded-lg text-gray-600 transition-colors hover:bg-white hover:shadow-sm"
        :title="isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <FeatherIcon :name="'menu'" class="size-[18px]" />
      </button>
    </div>

    <div class="flex flex-shrink-0 items-center gap-1.5">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
import { inject, ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'

defineEmits(['toggle-sidebar'])

const isSidebarCollapsed = inject('isSidebarCollapsed', ref(false))
</script>
