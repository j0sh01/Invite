<template>
  <div class="flex items-center pr-3 border-b">
    <div class="z-20 ml-2 flex items-center justify-center">
      <Button
        class="size-7"
        variant="ghosted"
        @click="sidebarOpened = !sidebarOpened"
      >
        <FeatherIcon name="menu" class="h-5 w-5 text-ink-gray-9" />
      </Button>
    </div>
    <div id="app-header" class="flex-1" />
  </div>
</template>

<script setup>
import { FeatherIcon, Button } from 'frappe-ui'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
</script>
