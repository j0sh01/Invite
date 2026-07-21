<template>
  <div class="flex h-screen w-screen">
    <div class="h-full border-r bg-surface-menu-bar flex-shrink-0">
      <AppSidebar />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto bg-surface-white">
      <AppHeader @toggle-sidebar="toggleSidebar" />
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { provide, ref, watch } from 'vue'
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'

// Sidebar collapse state (persisted to localStorage)
const isSidebarCollapsed = ref(false)
try {
  const stored = localStorage.getItem('isSidebarCollapsed')
  if (stored !== null) {
    isSidebarCollapsed.value = stored === 'true'
  }
} catch (e) { /* localStorage may not be available */ }

// Persist changes
watch(isSidebarCollapsed, (val) => {
  try {
    localStorage.setItem('isSidebarCollapsed', val)
  } catch (e) { /* localStorage may not be available */ }
})

// Provide state to children (AppSidebar, AppHeader)
provide('isSidebarCollapsed', isSidebarCollapsed)

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
</script>
