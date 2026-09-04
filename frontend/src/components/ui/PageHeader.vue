<template>
  <header class="mb-8">
    <p v-if="eyebrow || eyebrowText" class="eyebrow text-gray-500 mb-2">
      {{ eyebrow || eyebrowText }}
    </p>
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div class="min-w-0">
        <h1
          class="font-display text-3xl sm:text-[2.15rem] leading-tight text-gray-900"
        >
          {{ title }}
        </h1>
        <p v-if="subtitle" class="mt-2 max-w-2xl text-sm text-gray-500">
          {{ subtitle }}
        </p>
      </div>
      <div v-if="$slots.actions" class="flex flex-shrink-0 items-center gap-2">
        <slot name="actions" />
      </div>
    </div>
    <div v-if="$slots.default" class="mt-6">
      <slot />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  eyebrow: { type: String, default: '' },
  eyebrowText: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})
</script>
