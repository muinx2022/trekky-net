<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <img v-if="authorAvatarUrl" :src="authorAvatarUrl" :alt="`${username} avatar`" class="h-16 w-16 rounded-full object-cover bg-slate-300" />
      <div v-else class="flex h-16 w-16 items-center justify-center rounded-full bg-slate-300 text-2xl font-bold text-slate-600">
        {{ username.slice(0, 1).toUpperCase() }}
      </div>
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ username }}</h1>
        <p class="mt-0.5 text-sm text-slate-500">{{ total }} bai viet</p>
      </div>
    </div>

    <InfinitePosts :initial-posts="posts" :initial-total="total" :author-username="username" />
  </div>
</template>

<script setup lang="ts">
import { SITE_NAME } from "~~/shared/seo";
import type { PaginatedResponse, Post } from "~~/shared/types";

const route = useRoute();
const username = route.params.username as string;

const { data } = await useFetch<PaginatedResponse<Post>>(`/api/posts-proxy?page=1&pageSize=10&author=${encodeURIComponent(username)}`);
const posts = computed(() => data.value?.data ?? []);
const total = computed(() => data.value?.meta?.pagination?.total ?? 0);
const authorAvatarUrl = computed(() => posts.value[0]?.author?.avatar?.url ?? "");

useSeoMeta({
  title: username,
  description: `Xem cac bai viet cua ${username} tren ${SITE_NAME}.`,
});
</script>
