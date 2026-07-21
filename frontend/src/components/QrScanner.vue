<template>
  <div class="relative">
    <!-- Camera feed -->
    <div
      class="rounded-lg overflow-hidden bg-gray-900 relative"
      :class="{ 'opacity-50': !cameraActive }"
    >
      <QrcodeStream
        v-if="cameraEnabled"
        :paused="!cameraActive"
        @detect="onDetect"
        @camera-on="onCameraOn"
        @error="onCameraError"
        class="w-full"
        :style="{ minHeight: '280px' }"
      />
      <!-- Fallback when camera is off -->
      <div
        v-else
        class="flex flex-col items-center justify-center py-16 text-gray-400"
      >
        <FeatherIcon name="camera-off" class="h-16 w-16 mb-3" />
        <p class="text-sm font-medium">Camera is off</p>
        <p class="text-xs mt-1">Click the button below to turn it on</p>
      </div>
    </div>

    <!-- Scanning overlay -->
    <div
      v-if="cameraActive"
      class="absolute inset-0 pointer-events-none flex items-center justify-center"
    >
      <div class="w-48 h-48 border-2 border-white/60 rounded-lg">
        <div
          class="absolute top-0 left-0 w-1/3 h-1 border-t-4 border-l-4 border-emerald-400 rounded-tl-lg"
        ></div>
        <div
          class="absolute top-0 right-0 w-1/3 h-1 border-t-4 border-r-4 border-emerald-400 rounded-tr-lg"
        ></div>
        <div
          class="absolute bottom-0 left-0 w-1/3 h-1 border-b-4 border-l-4 border-emerald-400 rounded-bl-lg"
        ></div>
        <div
          class="absolute bottom-0 right-0 w-1/3 h-1 border-b-4 border-r-4 border-emerald-400 rounded-br-lg"
        ></div>
      </div>
      <!-- Scan line animation -->
      <div class="absolute scan-line"></div>
    </div>

    <!-- Status indicator -->
    <div
      v-if="statusMessage"
      class="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
      :class="statusType === 'error' ? 'bg-red-50 text-red-700' : statusType === 'success' ? 'bg-green-50 text-green-700' : 'bg-blue-50 text-blue-700'"
    >
      <FeatherIcon
        :name="statusType === 'error' ? 'alert-triangle' : statusType === 'success' ? 'check-circle' : 'info'"
        class="h-4 w-4 flex-shrink-0"
      />
      <span>{{ statusMessage }}</span>
      <button v-if="statusType === 'error' && cameraEnabled" @click="clearStatus" class="ml-auto text-gray-400 hover:text-gray-600">
        <FeatherIcon name="x" class="h-3.5 w-3.5" />
      </button>
    </div>

    <!-- Controls -->
    <div class="mt-3 flex items-center justify-center gap-3">
      <Button
        @click="toggleCamera"
        :variant="cameraActive ? 'solid' : 'ghost'"
        size="sm"
        class="flex items-center gap-1.5"
      >
        <FeatherIcon :name="cameraActive ? 'camera' : 'camera-off'" class="h-4 w-4" />
        {{ cameraActive ? 'Stop Camera' : 'Start Camera' }}
      </Button>

      <Button
        @click="$emit('switch-to-manual')"
        variant="ghost"
        size="sm"
        class="flex items-center gap-1.5"
      >
        <FeatherIcon name="edit" class="h-4 w-4" />
        Manual Entry
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { QrcodeStream } from 'vue-qrcode-reader'

const emit = defineEmits(['detected', 'switch-to-manual'])

const cameraActive = ref(false)
const cameraEnabled = ref(false)
const statusMessage = ref('')
const statusType = ref('info')
const scanTimeout = ref(null)

onMounted(() => {
  // Check if camera access is available
  if (navigator.mediaDevices?.getUserMedia) {
    cameraEnabled.value = true
  } else {
    statusMessage.value = 'Camera not available on this device/browser.'
    statusType.value = 'error'
  }
})

defineExpose({
  pauseCamera,
  clearStatus,
})

onUnmounted(() => {
  if (scanTimeout.value) {
    clearTimeout(scanTimeout.value)
  }

})

function toggleCamera() {
  cameraActive.value = !cameraActive.value
  if (!cameraActive.value) {
    clearStatus()
  }
}

function pauseCamera() {
  cameraActive.value = false
  clearStatus()
}

function onCameraOn() {
  cameraActive.value = true
  statusMessage.value = 'Camera is ready — point at a QR code.'
  statusType.value = 'info'
}

function onCameraError(err) {
  cameraActive.value = false
  if (err.name === 'NotAllowedError') {
    statusMessage.value = 'Camera access denied. Please allow camera permissions and try again.'
  } else if (err.name === 'NotFoundError') {
    statusMessage.value = 'No camera device found on this device.'
  } else {
    statusMessage.value = `Camera error: ${err.message || 'Unknown error'}`
  }
  statusType.value = 'error'
}

function onDetect(detectedCodes) {
  if (!detectedCodes?.length) return

  const rawValue = detectedCodes[0]?.rawValue
  if (!rawValue) return

  // Debounce: prevent rapid re-scans
  if (scanTimeout.value) return

  // Brief pause to prevent double-scanning
  scanTimeout.value = setTimeout(() => {
    scanTimeout.value = null
  }, 2000)

  emit('detected', rawValue)
  statusMessage.value = 'QR code detected! Processing...'
  statusType.value = 'success'
}

function clearStatus() {
  statusMessage.value = ''
  statusType.value = 'info'
}
</script>

<style scoped>
.scan-line {
  width: 70%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #34d399, transparent);
  animation: scanMove 2s ease-in-out infinite;
  top: 30%;
}

@keyframes scanMove {
  0%, 100% {
    top: 30%;
  }
  50% {
    top: 65%;
  }
}
</style>
