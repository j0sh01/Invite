<template>
  <div class="relative flex h-full flex-col">
    <!-- User menu (Apps / Desk / theme / settings / about) — kept on top -->
    <div class="p-3 pb-2">
      <UserDropdown :isCollapsed="isSidebarCollapsed" />
    </div>

    <!-- Notifications trigger -->
    <div v-if="!isSidebarCollapsed" class="px-3">
      <button
        id="notifications-btn"
        class="flex w-full items-center justify-between rounded-lg px-3 py-2 text-[13px] font-medium text-gray-600 transition-colors hover:bg-[#F3ECE0] hover:text-gray-900"
        @click="toggleNotificationPanel"
      >
        <span class="flex items-center gap-2.5">
          <FeatherIcon name="bell" class="size-4 text-gray-400" />
          Notifications
        </span>
        <span
          v-if="unreadNotificationsCount"
          class="grid min-w-[18px] place-items-center rounded-full bg-[#C75F2C] px-1.5 py-0.5 text-[10px] font-semibold text-white"
        >
          {{ unreadNotificationsCount }}
        </span>
      </button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto px-3 py-3">
      <template v-for="group in navGroups" :key="group.label">
        <p
          v-if="!isSidebarCollapsed && group.items.length"
          class="px-3 pb-1.5 pt-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-gray-400"
        >
          {{ group.label }}
        </p>
        <div class="flex flex-col gap-0.5">
          <SidebarLink
            v-for="link in group.items"
            :key="link.to"
            :icon="link.icon"
            :label="link.label"
            :to="link.to"
            :isCollapsed="isSidebarCollapsed"
          />
        </div>
      </template>
    </nav>

    <!-- Footer: collapse toggle -->
    <div class="border-t border-hairline p-2">
      <button
        class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-gray-500 transition-colors hover:bg-[#F3ECE0] hover:text-gray-900"
        @click="isSidebarCollapsed = !isSidebarCollapsed"
        :class="isSidebarCollapsed ? 'justify-center' : ''"
        :title="isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <FeatherIcon
          :name="isSidebarCollapsed ? 'chevrons-right' : 'chevrons-left'"
          class="size-4"
        />
        <span v-if="!isSidebarCollapsed">Collapse</span>
      </button>
    </div>

    <Notifications v-if="!isSidebarCollapsed" />

    <!-- About Modal -->
    <Dialog :options="{ title: 'About Invite' }" v-model="showAboutModal">
      <template #body-content>
        <div class="py-4 text-center">
          <img
            :src="'/assets/invite/images/logo.svg'"
            alt="Invite"
            class="mx-auto mb-4 size-16 rounded-2xl"
          />
          <h3 class="font-display text-lg text-gray-900">Invite</h3>
          <p class="mt-1 text-sm text-gray-500">Event Management System</p>
          <p class="mt-1 text-xs text-gray-400">v0.0.1</p>
          <p class="mt-4 text-xs text-gray-400">Built for KiliGrid Technology</p>
        </div>
      </template>
      <template #actions>
        <Button @click="showAboutModal = false" variant="solid">
          {{ __('Close') }}
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, inject, provide, computed, onMounted } from 'vue'
import { FeatherIcon, Dialog, Button } from 'frappe-ui'
import SidebarLink from '@/components/SidebarLink.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import Notifications from '@/components/Notifications.vue'
import { showAboutModal } from '@/composables/settings'
import { useRoleInfo } from '@/composables/roles'
import {
  unreadNotificationsCount,
  toggle as toggleNotificationPanel,
} from '@/stores/notifications'

const isSidebarCollapsed = inject('isSidebarCollapsed', ref(false))
provide('isSidebarCollapsed', isSidebarCollapsed)

const { getRoleInfo } = useRoleInfo()
const isFrontdeskOnly = ref(false)

onMounted(async () => {
  const info = await getRoleInfo()
  isFrontdeskOnly.value = info.is_frontdesk_only
})

const allGroups = [
  {
    label: 'Workspace',
    items: [
      { label: 'Dashboard', icon: 'home', to: 'Dashboard', frontdeskOnly: false },
      { label: 'Events', icon: 'calendar', to: 'Events', frontdeskOnly: false },
    ],
  },
  {
    label: 'Operations',
    items: [
      { label: 'Frontdesk', icon: 'camera', to: 'Frontdesk', frontdeskOnly: true },
      {
        label: 'Audit Log',
        icon: 'clipboard',
        to: 'GlobalAuditLog',
        frontdeskOnly: null, // visible to everyone
      },
      { label: 'Templates', icon: 'layout', to: 'Templates', frontdeskOnly: false },
      { label: 'Settings', icon: 'settings', to: 'AppSettings', frontdeskOnly: false },
    ],
  },
]

const navGroups = computed(() => {
  return allGroups
    .map((group) => ({
      label: group.label,
      items: group.items.filter((item) => {
        if (item.frontdeskOnly === null) return true
        if (item.frontdeskOnly) return isFrontdeskOnly.value
        return !isFrontdeskOnly.value
      }),
    }))
    .filter((group) => group.items.length)
})
</script>
