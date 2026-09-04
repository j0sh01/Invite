<template>
  <button
    type="button"
    class="card flex w-full items-start gap-4 p-5 text-left"
    :class="disabled ? 'cursor-not-allowed opacity-60' : 'card-hover cursor-pointer'"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <span
      class="grid size-11 flex-shrink-0 place-items-center rounded-xl"
      :class="chipClass"
    >
      <FeatherIcon :name="icon" class="size-5" />
    </span>
    <span class="min-w-0">
      <span class="block text-[15px] font-medium text-gray-900">{{ title }}</span>
      <span class="mt-1 block text-xs leading-relaxed text-gray-500">
        {{ disabled && disabledText ? disabledText : text }}
      </span>
    </span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  icon: { type: String, default: 'circle' },
  title: { type: String, required: true },
  text: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  disabledText: { type: String, default: '' },
  tone: { type: String, default: 'accent' },
})

defineEmits(['click'])

const chipClass = computed(() => {
  const tones = {
    accent: 'bg-[#FBF2EC] text-[#B04C21]',
    green: 'bg-[#F0F7F2] text-[#166534]',
    violet: 'bg-[#FAF3FF] text-[#6B21A8]',
    amber: 'bg-[#FDF6E3] text-[#92400E]',
    gray: 'bg-[#F3EDE1] text-[#5E503B]',
  }
  return tones[props.tone] || tones.accent
})
</script>
