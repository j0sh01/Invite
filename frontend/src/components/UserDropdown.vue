<template>
  <Dropdown :options="dropdownItems">
    <template #default="{ open }">
      <button
        class="flex h-12 items-center rounded-md py-2 duration-300 ease-in-out px-2"
        :class="[
          isCollapsed ? 'w-10 justify-center' : 'w-52',
          open
            ? 'bg-surface-white shadow-sm'
            : 'hover:bg-surface-gray-3'
        ]"
      >
        <div class="h-8 w-8 flex-shrink-0 rounded bg-gray-100 flex items-center justify-center">
          <FeatherIcon name="calendar" class="h-5 w-5 text-blue-600" />
        </div>
        <div v-show="!isCollapsed" class="ml-2 flex flex-1 flex-col text-left truncate">
          <div class="text-base font-medium leading-none text-ink-gray-9 truncate">
            {{ __('Invite') }}
          </div>
          <div class="mt-1 text-sm leading-none text-ink-gray-7 truncate">
            {{ userName }}
          </div>
        </div>
        <div v-show="!isCollapsed" class="ml-2 w-auto">
          <FeatherIcon name="chevron-down" class="size-4 text-ink-gray-5" />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import { computed, ref, markRaw, onMounted, inject } from 'vue'
import { Dropdown } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'
import { sessionStore } from '@/stores/session'
import { toggleTheme } from '@/stores/theme'
import { showAboutModal, isMobileView } from '@/composables/settings'
import Apps from '@/components/Apps.vue'

const props = defineProps({
  isCollapsed: { type: Boolean, default: undefined },
})
const isCollapsed = computed(() => {
  // If the isCollapsed prop is explicitly provided, use it.
  // Otherwise fall back to the injected value from the parent.
  return props.isCollapsed !== undefined ? props.isCollapsed : inject('isSidebarCollapsed', false)
})
const { logout, user } = sessionStore()
const fullName = ref('')

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: 'invite.api.session.get_current_user_info',
    })
    fullName.value = data?.full_name || user.value || 'User'
  } catch (e) {
    fullName.value = user.value || 'User'
  }
})

const userName = computed(() => {
  return fullName.value || user.value || 'User'
})

const dropdownItems = computed(() => {
  return [
    {
      group: 'Dropdown Items',
      hideLabel: true,
      items: [
        {
          component: markRaw(Apps),
        },
        {
          label: 'Toggle theme',
          icon: 'moon',
          onClick: toggleTheme,
        },
        {
          label: 'Settings',
          icon: 'settings',
          onClick: () => { window.location.href = '/invite/settings' },
          condition: () => !isMobileView.value,
        },
        {
          label: 'About',
          icon: 'info',
          onClick: () => { showAboutModal.value = true },
        },
      ],
    },
    {
      group: '',
      hideLabel: true,
      items: [
        {
          label: 'Log out',
          icon: 'log-out',
          onClick: () => logout.submit(),
        },
      ],
    },
  ]
})
</script>
