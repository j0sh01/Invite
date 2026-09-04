<template>
  <div
    class="flex h-12 flex-shrink-0 items-center gap-2 border-b border-[#E7DCC7] bg-canvas px-3"
  >
    <button
      class="grid size-9 place-items-center rounded-lg text-gray-700 transition-colors hover:bg-white"
      @click="sidebarOpened = !sidebarOpened"
    >
      <FeatherIcon name="menu" class="size-5" />
    </button>
    <div class="flex items-center gap-2">
      <div
        class="grid size-6 place-items-center rounded-md bg-[#C75F2C] font-display text-[11px] font-bold text-[#FFF9EF]"
      >
        I
      </div>
      <span class="font-display text-base font-semibold text-gray-900">Invite</span>
    </div>
    <div class="flex-1" />
  </div>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
</script>
