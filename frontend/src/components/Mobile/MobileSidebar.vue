<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" @close="sidebarOpened = false" class="fixed inset-0 z-40">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
        <div
          class="relative z-10 flex h-full w-[260px] flex-col justify-between border-r bg-surface-menu-bar transition-all duration-300 ease-in-out"
        >
          <!-- User Dropdown -->
          <div class="p-2">
            <UserDropdown />
          </div>

          <!-- Navigation -->
          <div class="flex-1 overflow-y-auto px-2">
            <div class="mb-3 flex flex-col">
              <SidebarLink
                id="notifications-btn"
                :label="__('Notifications')"
                icon="bell"
                @click="toggleNotifications"
                class="relative mx-0 my-0.5"
              />
            </div>
            <nav class="flex flex-col gap-0.5">
              <SidebarLink
                v-for="link in navItems"
                :key="link.to"
                :icon="link.icon"
                :label="__(link.label)"
                :to="link.to"
                class="mx-0"
              />
            </nav>
          </div>

          <!-- Bottom section -->
          <div class="m-2 flex flex-col gap-1">
            <SidebarLink
              label="Switch to Desk"
              icon="grid"
              to="/app"
              class="mx-0 my-0.5"
            />
          </div>
        </div>
      </TransitionChild>
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-gray-600 bg-opacity-50" />
      </TransitionChild>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  TransitionRoot,
  TransitionChild,
  Dialog,
} from '@headlessui/vue'
import { FeatherIcon } from 'frappe-ui'
import SidebarLink from '@/components/SidebarLink.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
import { useRoleInfo } from '@/composables/roles'

const { getRoleInfo } = useRoleInfo()
const isFrontdeskOnly = ref(false)

onMounted(async () => {
  const info = await getRoleInfo()
  isFrontdeskOnly.value = info.is_frontdesk_only
})

const allNavItems = [
  { label: 'Dashboard', icon: 'home', to: 'Dashboard' },
  { label: 'Events', icon: 'calendar', to: 'Events' },
  { label: 'Frontdesk', icon: 'camera', to: 'Frontdesk', frontdeskOnly: true },
  { label: 'Audit Log', icon: 'file-text', to: 'GlobalAuditLog', frontdeskOnly: true },
  { label: 'Settings', icon: 'settings', to: 'AppSettings' },
]

const navItems = computed(() => {
  if (isFrontdeskOnly.value) {
    return allNavItems.filter(item => item.frontdeskOnly)
  }
  return allNavItems.filter(item => !item.frontdeskOnly)
})

function toggleNotifications() {
  // Simple notification toggle - can be enhanced later
}
</script>
