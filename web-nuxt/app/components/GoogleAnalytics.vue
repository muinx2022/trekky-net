<template>
  <template v-if="measurementId">
    <component :is="'script'" async :src="`https://www.googletagmanager.com/gtag/js?id=${measurementId}`" />
    <component :is="'script'">
      {{ inlineScript }}
    </component>
  </template>
</template>

<script setup lang="ts">
const config = useRuntimeConfig();
const measurementId = config.public.ga4MeasurementId;
const inlineScript = `
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '${measurementId}', { page_path: window.location.pathname });
`;
</script>
