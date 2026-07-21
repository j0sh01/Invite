<template>
  <div class="flex flex-col items-center justify-center min-h-[60vh]">
    <FeatherIcon name="alert-triangle" class="h-16 w-16 text-amber-500 mb-4" />
    <h1 class="text-2xl font-semibold text-gray-900 mb-2">Page Not Found</h1>
    <p class="text-gray-500 mb-6">The page you're looking for doesn't exist.</p>
    <Button @click="$router.push('/dashboard')" variant="solid">Go to Dashboard</Button>
  </div>
</template>
