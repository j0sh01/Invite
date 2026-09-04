<template>
  <div class="card flex flex-col items-center justify-center px-6 py-14 text-center">
    <div
      class="mb-5 grid size-16 place-items-center rounded-2xl border border-[#E9DFCB] bg-[#FAF5EA]"
    >
      <FeatherIcon :name="icon" class="size-7 text-[#B9A887]" />
    </div>
    <h3 class="font-display text-xl text-gray-900">{{ title }}</h3>
    <p v-if="message" class="mt-2 max-w-sm text-sm leading-relaxed text-gray-500">
      {{ message }}
    </p>
    <div v-if="$slots.action" class="mt-6">
      <slot name="action" />
    </div>
    <slot />
  </div>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({
  icon: { type: String, default: 'inbox' },
  title: { type: String, required: true },
  message: { type: String, default: '' },
})
</script>
