<template>
  <button
    class="group relative flex w-full cursor-pointer items-center rounded-lg text-[13px] font-medium text-gray-600 outline-none transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-[#C75F2C]/60"
    :class="
      isActive
        ? 'bg-[#FBF2EC] text-[#8F3B1C]'
        : 'hover:bg-[#F3ECE0] hover:text-gray-900'
    "
    @click="handleClick"
  >
    <span
      v-if="isActive && !isCollapsed"
      class="absolute left-0 top-1/2 h-4 w-[3px] -translate-y-1/2 rounded-r-full bg-[#C75F2C]"
    />
    <div
      class="flex w-full items-center justify-between px-3 py-[7px]"
      :class="{ 'justify-center px-0': isCollapsed }"
    >
      <div class="flex min-w-0 items-center">
        <span class="grid flex-shrink-0 place-items-center">
          <FeatherIcon
            v-if="typeof icon === 'string'"
            :name="icon"
            class="size-[17px]"
            :class="isActive ? 'text-[#B04C21]' : 'text-gray-400 group-hover:text-gray-500'"
          />
          <component v-else :is="icon" class="size-[17px]" />
        </span>
        <span
          v-if="!isCollapsed"
          class="ml-3 flex-1 flex-shrink-0 truncate text-left"
        >
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
import { FeatherIcon } from 'frappe-ui'

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
      router.push(props.to)
    } else {
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
