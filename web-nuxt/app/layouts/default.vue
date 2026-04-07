<template>
  <div class="min-h-screen bg-slate-100 text-slate-900">
    <GoogleAnalytics />
    <component
      :is="'script'"
      :src="runtimeConfig.public.trackerScriptUrl"
      :data-tracking-id="runtimeConfig.public.trackerId"
      async
    />
    <SiteShell>
      <slot />
    </SiteShell>
  </div>
</template>

<script setup lang="ts">
const runtimeConfig = useRuntimeConfig();
</script>
