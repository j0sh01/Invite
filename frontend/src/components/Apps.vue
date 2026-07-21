<template>
  <Popover placement="right-start" trigger="hover" :hoverDelay="0.1" :leaveDelay="0.1">
    <template #target="{ togglePopover }">
      <button
        :class="[
          'group w-full flex h-7 items-center justify-between rounded px-2 text-base text-ink-gray-6 hover:bg-surface-gray-2',
        ]"
        @click.prevent="togglePopover()"
      >
        <div class="flex gap-2">
          <FeatherIcon name="grid" class="size-4" />
          <span class="whitespace-nowrap">{{ __('Apps') }}</span>
        </div>
        <FeatherIcon name="chevron-right" class="size-4 text-ink-gray-5" />
      </button>
    </template>
    <template #body>
      <div
        class="flex w-fit mx-2 min-w-32 max-w-48 flex-col rounded-lg border border-outline-gray-2 bg-surface-white p-1.5 text-sm text-ink-gray-8 shadow-xl"
      >
        <a
          v-for="app in apps"
          :key="app.name"
          :href="app.route"
          class="flex items-center gap-2 rounded p-1.5 hover:bg-surface-gray-2"
        >
          <img v-if="app.logo" class="size-6" :src="app.logo" />
          <FeatherIcon v-else name="grid" class="size-4 text-ink-gray-5" />
          <span class="max-w-18 w-full truncate">{{ app.title }}</span>
        </a>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Popover } from 'frappe-ui'
import { frappeRequest } from '@/utils/api'

const apps = ref([])

onMounted(async () => {
  try {
    const data = await frappeRequest({
      url: 'frappe.apps.get_apps',
    })
    // Always show Desk first, then other apps
    let _apps = [
      {
        name: 'frappe',
        logo: '/assets/frappe/images/framework.png',
        title: 'Desk',
        route: '/app',
      },
    ]
    ;(data || []).map((app) => {
      if (app.name === 'invite') return
      _apps.push({
        name: app.name,
        logo: app.logo,
        title: app.title,
        route: app.route || `/app/${app.name}`,
      })
    })
    apps.value = _apps
  } catch (e) {
    // Fallback to just Desk
    apps.value = [
      {
        name: 'frappe',
        logo: '/assets/frappe/images/framework.png',
        title: 'Desk',
        route: '/app',
      },
    ]
  }
})
</script>
