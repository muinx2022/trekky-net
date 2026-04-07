<template>
  <div v-if="images.length" class="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
    <div v-for="image in images" :key="image.id" class="aspect-square overflow-hidden rounded-lg border border-gray-200 bg-gray-100">
      <img :src="image.url" :alt="image.alternativeText ?? ''" class="h-full w-full object-cover" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Media } from "~~/shared/types";

defineProps<{
  images: Media[];
}>();
</script>
