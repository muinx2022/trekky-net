<template>
  <div v-if="posts.length" class="space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-gray-800">{{ title }}</h3>
      <div v-if="posts.length > 1" class="flex gap-2">
        <button type="button" class="rounded-full border border-gray-300 p-2 text-gray-600 hover:bg-gray-50" @click="move(-1)">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m15 18-6-6 6-6" /></svg>
        </button>
        <button type="button" class="rounded-full border border-gray-300 p-2 text-gray-600 hover:bg-gray-50" @click="move(1)">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m9 18 6-6-6-6" /></svg>
        </button>
      </div>
    </div>

    <PostCard :post="posts[index]" />
  </div>
</template>

<script setup lang="ts">
import type { Post } from "~~/shared/types";

const props = withDefaults(
  defineProps<{
    posts: Post[];
    title?: string;
  }>(),
  {
    title: "Bài viết",
  },
);

const index = ref(0);

watch(
  () => props.posts,
  () => {
    index.value = 0;
  },
);

function move(delta: number) {
  index.value = (index.value + delta + props.posts.length) % props.posts.length;
}
</script>
