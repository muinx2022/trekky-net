<template>
  <div v-if="categories.length > 0" class="rounded-lg border border-gray-200 bg-white shadow-sm">
    <h3 class="border-b border-gray-100 px-4 py-3 text-sm font-semibold text-gray-800">Danh muc</h3>
    <nav class="flex flex-col gap-1 p-2">
      <NuxtLink to="/" class="flex items-center gap-2.5 rounded-md px-3 py-2.5 text-sm text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900">
        <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-gray-400 text-white">
          <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>
        </span>
        <span class="font-medium">Trang chu</span>
      </NuxtLink>
      <NuxtLink
        v-for="category in categories"
        :key="category.documentId"
        :to="`/c/${category.slug}`"
        class="flex items-center gap-2.5 rounded-md px-3 py-2.5 text-sm text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900"
      >
        <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded text-[10px] font-bold text-white" :class="getColorBySlug(category.slug)">
          {{ category.name[0]?.toUpperCase() }}
        </span>
        <span class="font-medium">{{ category.name }}</span>
      </NuxtLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
import type { Category } from "../../shared/types";

defineProps<{
  categories: Category[];
}>();

const COLOR_CLASSES = ["bg-rose-400", "bg-orange-400", "bg-amber-400", "bg-lime-500", "bg-emerald-500", "bg-cyan-500", "bg-sky-400", "bg-blue-400", "bg-indigo-400", "bg-violet-400", "bg-fuchsia-400", "bg-pink-400"];

function getColorBySlug(slug: string) {
  const hash = Array.from(slug).reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return COLOR_CLASSES[hash % COLOR_CLASSES.length];
}
</script>
