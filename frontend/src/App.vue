<template>
  <FrappeUIProvider>
    <ToastNotification />
    <Layout v-if="session.isLoggedIn">
      <router-view :key="$route.fullPath" />
    </Layout>
    <div v-else class="flex h-screen items-center justify-center bg-gray-50">
      <div class="text-center">
        <h1 class="text-2xl font-bold text-gray-900 mb-4">Invite - Event Management</h1>
        <Button @click="redirectToLogin" variant="solid">Login to Continue</Button>
      </div>
    </div>
  </FrappeUIProvider>
</template>

<script setup>
import { defineAsyncComponent, computed, onMounted } from 'vue'
import { FrappeUIProvider, setConfig } from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import ToastNotification from '@/components/ToastNotification.vue'
import { isMobileView, initViewportListener } from '@/composables/settings'

const session = sessionStore()

const MobileLayout = defineAsyncComponent(
  () => import('./components/Layouts/MobileLayout.vue'),
)
const DesktopLayout = defineAsyncComponent(
  () => import('./components/Layouts/DesktopLayout.vue'),
)

// Reactive: follows window width live, so rotating a phone or resizing the
// window switches between the mobile and desktop shell without a reload.
const Layout = computed(() => {
  if (isMobileView.value) {
    return MobileLayout
  } else {
    return DesktopLayout
  }
})

onMounted(() => {
  initViewportListener()
  setConfig('systemTimezone', window.timezone?.system || null)
  setConfig('localTimezone', window.timezone?.user || null)
})

function redirectToLogin() {
  window.location.href = '/login?redirect-to=/invite'
}
</script>
