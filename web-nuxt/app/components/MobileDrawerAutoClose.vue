<template>
  <div>
    <slot />
  </div>
</template>

<script setup lang="ts">
const route = useRoute();
const { closeDrawer } = useDrawer();

watch(
  () => route.fullPath,
  () => {
    closeDrawer();
  },
);
</script>
