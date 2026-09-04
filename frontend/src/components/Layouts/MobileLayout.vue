<template>
  <div class="flex h-screen w-screen overflow-hidden bg-canvas">
    <MobileSidebar />
    <div class="flex h-full min-w-0 flex-1 flex-col">
      <MobileAppHeader />
      <main class="flex-1 overflow-y-auto">
        <div class="mx-auto w-full max-w-page px-4 py-5">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import MobileSidebar from '@/components/Mobile/MobileSidebar.vue'
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
</script>
