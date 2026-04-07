<template>
  <div class="space-y-4">
    <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white px-6 py-6 shadow-sm">
      <h1 class="text-2xl font-bold text-slate-900 sm:text-3xl">{{ query ? "Kết quả tìm kiếm" : "Tìm kiếm" }}</h1>
      <p v-if="query" class="mt-1 text-sm text-slate-600">
        {{ totalResults > 0 ? `${totalResults} kết quả cho "${query}"` : `Không tìm thấy kết quả nào cho "${query}"` }}
      </p>
    </section>

    <div v-if="!query" class="rounded-2xl border border-slate-200 bg-white px-6 py-10 text-center shadow-sm">
      <p class="text-slate-500">Nhập từ khóa vào ô tìm kiếm để bắt đầu.</p>
    </div>

    <div v-else-if="totalResults === 0" class="rounded-2xl border border-slate-200 bg-white px-6 py-10 text-center shadow-sm">
      <p class="text-slate-500">Không tìm thấy kết quả phù hợp.</p>
    </div>

    <section v-if="results.posts?.length" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="border-b border-slate-100 px-5 py-3">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-500">Bài viết ({{ results.posts.length }})</h2>
      </div>
      <ul class="divide-y divide-slate-100">
        <li v-for="post in results.posts" :key="post.documentId">
          <NuxtLink :to="`/p/${post.slug}--${post.documentId}`" class="block px-5 py-4 hover:bg-slate-50">
            <p class="font-medium text-slate-900">{{ post.title }}</p>
            <div v-if="post.excerpt" class="mt-1 line-clamp-2 text-sm text-slate-600" v-html="sanitize(post.excerpt)" />
          </NuxtLink>
        </li>
      </ul>
    </section>

    <section v-if="results.tags?.length" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="border-b border-slate-100 px-5 py-3">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-500">Tags ({{ results.tags.length }})</h2>
      </div>
      <ul class="flex flex-wrap gap-2 p-5">
        <li v-for="tag in results.tags" :key="tag.documentId">
          <NuxtLink :to="`/t/${tag.slug}`" class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-200">
            #{{ tag.name }}
          </NuxtLink>
        </li>
      </ul>
    </section>

    <section v-if="results.categories?.length" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="border-b border-slate-100 px-5 py-3">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-500">Danh mục ({{ results.categories.length }})</h2>
      </div>
      <ul class="divide-y divide-slate-100">
        <li v-for="category in results.categories" :key="category.documentId">
          <NuxtLink :to="`/c/${category.slug}`" class="block px-5 py-4 hover:bg-slate-50">
            <p class="font-medium text-slate-900">{{ category.name }}</p>
            <p v-if="category.description" class="mt-0.5 text-sm text-slate-600">{{ category.description }}</p>
          </NuxtLink>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
import { sanitizeRichHtml } from "~~/shared/seo";

type SearchResults = {
  posts: Array<{ documentId: string; title: string; slug: string; excerpt?: string }>;
  tags: Array<{ documentId: string; name: string; slug: string; description?: string }>;
  categories: Array<{ documentId: string; name: string; slug: string; description?: string }>;
};

const route = useRoute();
const config = useRuntimeConfig();
const query = computed(() => (typeof route.query.q === "string" ? route.query.q.trim() : ""));
const { data: resultsData } = await useFetch<SearchResults>(() => (query.value ? `/api/search-proxy?q=${encodeURIComponent(query.value)}` : "/api/search-proxy"));
const results = computed(() => resultsData.value ?? { posts: [], tags: [], categories: [] });
const totalResults = computed(() => (results.value.posts?.length ?? 0) + (results.value.tags?.length ?? 0) + (results.value.categories?.length ?? 0));

function sanitize(html: string) {
  return sanitizeRichHtml(html, config.public.apiUrl);
}

useSeoMeta({
  title: query.value ? `Tìm kiếm: ${query.value}` : "Tìm kiếm",
  description: query.value ? `Kết quả tìm kiếm cho "${query.value}"` : "Tìm kiếm bài viết, tag và danh mục",
  robots: "noindex,nofollow",
});
</script>
