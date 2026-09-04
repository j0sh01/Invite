<template>
  <div class="card flex items-center gap-4 p-4 sm:p-5">
    <div
      class="grid size-10 sm:size-11 flex-shrink-0 place-items-center rounded-xl"
      :class="chipClass"
    >
      <FeatherIcon :name="icon" class="size-5 text-current" />
    </div>
    <div class="min-w-0">
      <p class="truncate text-xs font-medium uppercase tracking-[0.08em] text-gray-500">
        {{ label }}
      </p>
      <p class="font-display mt-0.5 truncate text-2xl text-gray-900">
        {{ value ?? '—' }}
      </p>
      <p v-if="hint" class="truncate text-xs text-gray-400">{{ hint }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: null },
  icon: { type: String, default: 'circle' },
  hint: { type: String, default: '' },
  // tone chips: accent (terracotta), green, amber, violet, red, gray, ink
  tone: { type: String, default: 'accent' },
})

const chipClass = computed(() => {
  const tones = {
    accent: 'bg-[#FBF2EC] text-[#B04C21]',
    green: 'bg-[#F0F7F2] text-[#166534]',
    amber: 'bg-[#FDF6E3] text-[#92400E]',
    violet: 'bg-[#FAF3FF] text-[#6B21A8]',
    red: 'bg-[#FEF1F1] text-[#991B1B]',
    gray: 'bg-[#F3EDE1] text-[#5E503B]',
    ink: 'bg-[#ECE4D2] text-[#322A1E]',
  }
  return tones[props.tone] || tones.accent
})
</script>
