<template>
  <Dropdown :options="dropdownItems">
    <template #default="{ open }">
      <button
        class="flex w-full items-center rounded-lg px-2 py-1.5 transition-colors"
        :class="isCollapsed ? 'justify-center' : ''"
      >
        <div class="flex min-w-0 items-center gap-2.5">
          <div
            class="grid size-8 flex-shrink-0 place-items-center rounded-lg bg-[#C75F2C] font-display text-[15px] font-bold text-[#FFF9EF]"
          >
            I
          </div>
          <div v-if="!isCollapsed" class="min-w-0 text-left leading-tight">
            <p class="font-display truncate text-[16px] font-semibold text-gray-900">Invite</p>
            <p class="truncate text-[11px] text-gray-500">{{ userName }}</p>
          </div>
        </div>
        <FeatherIcon
          v-if="!isCollapsed"
          name="chevron-down"
          class="ml-2 size-4 flex-shrink-0 text-gray-400"
          :class="open ? 'rotate-180' : ''"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import { computed, ref, markRaw, onMounted, inject } from 'vue'
import { Dropdown, FeatherIcon } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'
import { sessionStore } from '@/stores/session'
import { toggleTheme } from '@/stores/theme'
import { showAboutModal, isMobileView } from '@/composables/settings'
import Apps from '@/components/Apps.vue'

const props = defineProps({
  isCollapsed: { type: Boolean, default: undefined },
})
const isCollapsed = computed(() => {
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

const userName = computed(() => fullName.value || user.value || 'User')

const dropdownItems = computed(() => {
  return [
    {
      group: 'Dropdown Items',
      hideLabel: true,
      items: [
        { component: markRaw(Apps) },
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
