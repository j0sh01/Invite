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

  <!-- Settings Modal -->
  <Dialog :options="{ title: 'Settings', size: 'lg' }" v-model="showSettings">
    <template #body-content>
      <div class="space-y-4 py-2">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormControl label="Default Currency" type="select" v-model="settingsForm.default_currency" :options="currencyOptions" />
          <FormControl label="Default Event Type" type="select" v-model="settingsForm.default_event_type" :options="eventTypeOptions" />
        </div>
        <FormControl label="Default Reminder Days Before" type="number" v-model="settingsForm.default_reminder_days" />
        <hr class="my-2" />
        <FormControl label="App Name" v-model="settingsForm.app_name" />
        <FormControl label="Default Invitation Message" type="textarea" v-model="settingsForm.default_invitation_message" />
        <FormControl label="Default Thank You Template" type="textarea" v-model="settingsForm.default_thank_you_template" />
      </div>
    </template>
    <template #actions>
      <Button @click="showSettings = false" variant="ghost">Cancel</Button>
      <Button @click="saveSettings" variant="solid" :loading="savingSettings">Save</Button>
    </template>
  </Dialog>

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
import { ref, watch, computed, inject, provide } from 'vue'
import { FeatherIcon, Badge, Dialog, FormControl, Button } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'
import SidebarLink from '@/components/SidebarLink.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import Notifications from '@/components/Notifications.vue'
import { showAboutModal, showSettings } from '@/composables/settings'
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
  { label: 'Committee', icon: 'users', to: 'CommitteeMembers' },
]

// Settings form
const savingSettings = ref(false)
const eventTypesList = ref([])
const settingsForm = ref({
  default_currency: 'TZS',
  default_event_type: '',
  default_reminder_days: 3,
  app_name: 'Invite',
  default_invitation_message: '',
  default_thank_you_template: '',
})

const eventTypeOptions = computed(() => {
  return [{ label: 'None', value: '' }, ...(eventTypesList.value || []).map(t => ({ label: t.event_type_name, value: t.event_type_name }))]
})

const currencyOptions = [
  { label: 'TZS (Tanzanian Shilling)', value: 'TZS' },
  { label: 'USD (US Dollar)', value: 'USD' },
  { label: 'KES (Kenyan Shilling)', value: 'KES' },
  { label: 'UGX (Ugandan Shilling)', value: 'UGX' },
]

// Load settings and event types when dialog opens
watch(showSettings, async (val) => {
  if (val) {
    try {
      const [settings, types] = await Promise.all([
        frappeRequest({ url: 'invite.invite.doctype.event_settings.event_settings.get_event_settings' }),
        frappeRequest({ url: 'frappe.client.get_list', params: { doctype: 'Event Type', fields: ['event_type_name'] } }).catch(() => []),
      ])
      eventTypesList.value = types || []
      if (settings) {
        settingsForm.value = {
          default_currency: settings.default_currency || 'TZS',
          default_event_type: settings.default_event_type || '',
          default_reminder_days: settings.default_reminder_days || 3,
          app_name: settings.app_name || 'Invite',
          default_invitation_message: settings.default_invitation_message || '',
          default_thank_you_template: settings.default_thank_you_template || '',
        }
      }
    } catch (e) {
      console.error('Failed to load settings:', e)
    }
  }
})

async function saveSettings() {
  savingSettings.value = true
  try {
    await frappeRequest({
      url: 'frappe.client.save',
      params: {
        doc: JSON.stringify({
          doctype: 'Event Settings',
          name: 'Event Settings',
          ...settingsForm.value,
        }),
      },
    })
    showSettings.value = false
  } catch (e) {
    console.error('Failed to save settings:', e)
  } finally {
    savingSettings.value = false
  }
}
</script>
