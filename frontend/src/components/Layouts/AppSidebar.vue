<template>
  <div
    class="relative flex h-full flex-col justify-between transition-all duration-300 ease-in-out"
    :class="isSidebarCollapsed ? 'w-12' : 'w-[220px]'"
  >
    <div class="p-2">
      <UserDropdown :isCollapsed="isSidebarCollapsed" />
    </div>
    <div class="flex-1 overflow-y-auto">
      <div class="mb-3 flex flex-col">
        <SidebarLink
          id="notifications-btn"
          :label="__('Notifications')"
          icon="bell"
          :isCollapsed="isSidebarCollapsed"
          @click="() => toggleNotificationPanel()"
          class="relative mx-2 my-0.5"
        >
          <template #right>
            <Badge
              v-if="!isSidebarCollapsed && unreadNotificationsCount"
              :label="unreadNotificationsCount"
              variant="subtle"
            />
            <div
              v-else-if="unreadNotificationsCount"
              class="absolute -left-1.5 top-1 z-20 h-[5px] w-[5px] translate-x-6 translate-y-1 rounded-full bg-surface-gray-6 ring-1 ring-white"
            />
          </template>
        </SidebarLink>
      </div>
      <nav class="flex flex-col gap-0.5">
        <SidebarLink
          v-for="link in navItems"
          :key="link.to"
          :icon="link.icon"
          :label="link.label"
          :to="link.to"
          :isCollapsed="isSidebarCollapsed"
          class="mx-2 my-0.5"
        />
      </nav>
    </div>
    <div class="m-2 flex flex-col gap-1">
      <SidebarLink
        :label="isSidebarCollapsed ? __('Expand') : __('Collapse')"
        icon="chevrons-left"
        :isCollapsed="isSidebarCollapsed"
        @click="isSidebarCollapsed = !isSidebarCollapsed"
        class="mx-2 my-0.5"
      />
    </div>
    <Notifications />
  </div>


  <!-- About Modal -->
  <Dialog :options="{ title: 'About Invite' }" v-model="showAboutModal">
    <template #body-content>
      <div class="text-center py-4">
        <div class="h-16 w-16 mx-auto mb-4 rounded-xl bg-blue-100 flex items-center justify-center">
          <FeatherIcon name="calendar" class="h-8 w-8 text-blue-600" />
        </div>
        <h3 class="text-lg font-semibold text-ink-gray-9">{{ __('Invite') }}</h3>
        <p class="text-sm text-ink-gray-7 mt-1">{{ __('Event Management System') }}</p>
        <p class="text-xs text-ink-gray-5 mt-2">v0.0.1</p>
        <p class="text-xs text-ink-gray-5 mt-4">{{ __('Built for KiliGrid Technology') }}</p>
      </div>
    </template>
    <template #actions>
      <Button @click="showAboutModal = false" variant="solid">{{ __('Close') }}</Button>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, inject, provide } from 'vue'
import { FeatherIcon, Badge, Dialog, Button } from 'frappe-ui'
import SidebarLink from '@/components/SidebarLink.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import Notifications from '@/components/Notifications.vue'
import { showAboutModal } from '@/composables/settings'
import {
  unreadNotificationsCount,
  toggle as toggleNotificationPanel,
} from '@/stores/notifications'

// Sidebar collapse state is owned by DesktopLayout and injected here
const isSidebarCollapsed = inject('isSidebarCollapsed', ref(false))
// Re-provide to children (SidebarLink, UserDropdown)
provide('isSidebarCollapsed', isSidebarCollapsed)

const navItems = [
  { label: 'Dashboard', icon: 'home', to: 'Dashboard' },
  { label: 'Events', icon: 'calendar', to: 'Events' },
  { label: 'Frontdesk', icon: 'camera', to: 'Frontdesk' },
  { label: 'Audit Log', icon: 'file-text', to: 'GlobalAuditLog' },
  { label: 'Settings', icon: 'settings', to: 'AppSettings' },
]
</script>
