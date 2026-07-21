<template>
  <div
    v-if="visible"
    ref="target"
    class="absolute z-20 h-screen bg-surface-white transition-all duration-300 ease-in-out"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '350px',
      'min-width': '350px',
      left: 'calc(100% + 1px)',
      top: 0,
    }"
  >
    <div class="flex h-screen flex-col text-ink-gray-9">
      <div
        class="z-20 flex items-center justify-between border-b bg-surface-white px-5 py-2.5"
      >
        <div class="text-base font-medium">{{ __('Notifications') }}</div>
        <div class="flex gap-1">
          <FeatherIcon
            name="check"
            class="h-4 w-4 cursor-pointer text-gray-500 hover:text-gray-700"
            :tooltip="__('Mark all as read')"
            @click="markAllAsRead"
          />
          <FeatherIcon
            name="x"
            class="h-4 w-4 cursor-pointer text-gray-500 hover:text-gray-700"
            @click="toggle()"
          />
        </div>
      </div>
      <div
        v-if="notifications.data?.length"
        class="divide-y divide-outline-gray-modals overflow-auto text-base flex-1"
      >
        <div
          v-for="n in notifications.data"
          :key="n.name"
          class="flex cursor-pointer items-start gap-2.5 px-4 py-2.5 hover:bg-surface-gray-2"
          @click="markAsRead(n.name)"
        >
          <div class="mt-1 flex items-center gap-2.5">
            <div
              class="size-[5px] rounded-full flex-shrink-0"
              :class="[n.read ? 'bg-transparent' : 'bg-blue-500']"
            />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm mb-1" v-html="n.notification_text || n.subject" />
            <div class="text-xs text-gray-500">
              <span class="font-medium">{{ n.from_user?.full_name || n.from_user }}</span>
              <span v-if="n.reference_doctype">
                · {{ n.reference_doctype }}: {{ n.reference_name }}
              </span>
            </div>
            <div class="text-xs text-gray-400 mt-0.5">
              {{ timeAgo(n.creation) }}
            </div>
          </div>
        </div>
      </div>
      <div
        v-else
        class="flex flex-1 flex-col items-center justify-center gap-2"
      >
        <FeatherIcon name="bell" class="h-16 w-16 text-gray-300" />
        <div class="text-base font-medium text-gray-400">
          {{ __('No new notifications') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import {
  visible,
  notifications,
  toggle,
  mark_doc_as_read,
  mark_as_read,
} from '@/stores/notifications'
import { onClickOutside } from '@vueuse/core'

const target = ref(null)

onClickOutside(
  target,
  () => {
    if (visible.value) toggle()
  },
  {
    ignore: ['#notifications-btn'],
  },
)

function markAsRead(doc) {
  mark_doc_as_read(doc)
}

function markAllAsRead() {
  mark_as_read()
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const now = new Date()
  const date = new Date(dateStr)
  const seconds = Math.floor((now - date) / 1000)

  if (seconds < 60) return __('Just now')
  if (seconds < 3600) return __('{0}m ago', [Math.floor(seconds / 60)])
  if (seconds < 86400) return __('{0}h ago', [Math.floor(seconds / 3600)])
  if (seconds < 604800) return __('{0}d ago', [Math.floor(seconds / 86400)])
  return date.toLocaleDateString()
}
</script>
