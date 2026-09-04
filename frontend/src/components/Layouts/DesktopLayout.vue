<template>
  <div class="flex h-screen w-screen overflow-hidden bg-canvas">
    <aside
      class="flex h-full flex-shrink-0 flex-col border-r border-hairline bg-paper transition-[width] duration-300 ease-in-out"
      :class="isSidebarCollapsed ? 'w-[64px]' : 'w-[236px]'"
    >
      <AppSidebar />
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <AppHeader @toggle-sidebar="toggleSidebar" />
      <main class="flex-1 overflow-y-auto">
        <div class="mx-auto w-full max-w-page px-4 py-6 sm:px-7 sm:py-8">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { provide, ref, watch } from 'vue'
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'

const isSidebarCollapsed = ref(false)
try {
  const stored = localStorage.getItem('isSidebarCollapsed')
  if (stored !== null) {
    isSidebarCollapsed.value = stored === 'true'
  }
} catch (e) { /* localStorage may not be available */ }

watch(isSidebarCollapsed, (val) => {
  try {
    localStorage.setItem('isSidebarCollapsed', val)
  } catch (e) { /* localStorage may not be available */ }
})

provide('isSidebarCollapsed', isSidebarCollapsed)

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
</script>
