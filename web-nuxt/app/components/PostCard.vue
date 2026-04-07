<template>
  <article class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
    <img v-if="heroImage" :src="heroImage" :alt="post.title" class="h-64 w-full object-cover" />
    <div class="p-5">
      <div v-if="post.categories?.length" class="mb-3 flex flex-wrap gap-2">
        <NuxtLink
          v-for="category in post.categories"
          :key="category.documentId"
          :to="`/c/${category.slug}`"
          class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200"
        >
          {{ category.name }}
        </NuxtLink>
      </div>

      <NuxtLink :to="`/p/${post.slug}--${post.documentId}`" class="block">
        <h2 class="text-xl font-semibold text-slate-900 hover:text-sky-700">{{ post.title }}</h2>
      </NuxtLink>

      <p v-if="post.author?.username || dateLabel" class="mt-2 text-sm text-slate-500">
        <span v-if="post.author?.username">{{ post.author.username }}</span>
        <span v-if="post.author?.username && dateLabel"> · </span>
        <span v-if="dateLabel">{{ dateLabel }}</span>
      </p>

      <div v-if="excerptHtml" class="mt-3 line-clamp-3 text-sm leading-6 text-slate-600" v-html="excerptHtml" />

      <div v-if="post.tags?.length" class="mt-4 flex flex-wrap gap-2">
        <NuxtLink
          v-for="tag in post.tags"
          :key="tag.documentId"
          :to="`/t/${tag.slug}`"
          class="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:bg-slate-50"
        >
          #{{ tag.name }}
        </NuxtLink>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { sanitizeRichHtml } from "../../shared/seo";
import type { Post } from "../../shared/types";

const props = defineProps<{
  post: Post;
}>();

const config = useRuntimeConfig();
const heroImage = computed(() => props.post.images?.[0]?.url ?? "");
const dateLabel = computed(() => {
  const source = props.post.publishedAt || props.post.createdAt;
  return source ? new Date(source).toLocaleDateString("vi-VN") : "";
});
const excerptHtml = computed(() => sanitizeRichHtml(props.post.excerpt ?? "", config.public.apiUrl));
</script>
