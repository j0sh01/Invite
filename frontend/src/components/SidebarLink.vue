<template>
  <button
    class="flex h-7 w-full cursor-pointer items-center rounded text-ink-gray-7 duration-300 ease-in-out focus:outline-none focus:transition-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-outline-gray-3"
    :class="isActive ? 'bg-surface-selected shadow-sm' : 'hover:bg-surface-gray-2'"
    @click="handleClick"
  >
    <div
      class="flex w-full items-center justify-between duration-300 ease-in-out px-2 py-1"
    >
      <div class="flex items-center truncate">
        <span class="grid flex-shrink-0 place-items-center">
          <FeatherIcon
            v-if="typeof icon === 'string'"
            :name="icon"
            class="size-4 text-ink-gray-7"
          />
          <component v-else :is="icon" class="size-4 text-ink-gray-7" />
        </span>
        <span v-show="!isCollapsed" class="ml-2 flex-1 flex-shrink-0 truncate text-sm">
          {{ label }}
        </span>
      </div>
      <slot name="right" />
    </div>
  </button>
</template>

<script setup>
import { computed, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const props = defineProps({
  icon: {
    type: [Object, String],
    default: 'circle',
  },
  label: {
    type: String,
    default: '',
  },
  to: {
    type: [Object, String],
    default: null,
  },
  isCollapsed: {
    type: Boolean,
    default: undefined,
  },
})

const isCollapsed = computed(() => {
  return props.isCollapsed !== undefined
    ? props.isCollapsed
    : inject('isSidebarCollapsed', false)
})

const emit = defineEmits(['click'])

function handleClick() {
  if (props.to) {
    if (typeof props.to === 'object') {
      router.push(props.to)
    } else if (props.to.startsWith('/')) {
      // Absolute path - navigate directly
      router.push(props.to)
    } else {
      // Route name
      router.push({ name: props.to })
    }
  }
  emit('click')
}

const isActive = computed(() => {
  if (!props.to) return false
  if (typeof props.to === 'string') {
    if (props.to.startsWith('/')) {
      return route.path === props.to || route.path.startsWith(props.to + '/')
    }
    return route.name === props.to || route.path.startsWith('/' + props.to.toLowerCase())
  }
  return false
})
</script>
