<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium leading-none"
    :class="classes.pill"
  >
    <span class="size-1.5 rounded-full" :class="classes.dot" />
    <span class="whitespace-nowrap">{{ status }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { toneClasses } from '@/utils/status'

const props = defineProps({
  status: { type: String, default: '' },
})

const classes = computed(() => toneClasses(props.status))
</script>
