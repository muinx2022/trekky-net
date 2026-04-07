<template>
  <div class="space-y-4">
    <section v-if="homePage" class="overflow-hidden rounded-2xl border border-slate-200 bg-white px-6 py-6 shadow-sm">
      <h1 class="text-2xl font-bold text-slate-900 sm:text-3xl">{{ homePage.title }}</h1>
      <div v-if="homePage.content" class="mt-3">
        <RichTextContent :html="homePage.content" />
      </div>
    </section>

    <InfinitePosts :initial-posts="posts" :initial-total="total" />
  </div>
</template>

<script setup lang="ts">
import { SITE_DESCRIPTION, SITE_KEYWORDS, SITE_NAME, SITE_TITLE } from "~~/shared/seo";
import type { PaginatedResponse, Post, StrapiPage } from "~~/shared/types";

const runtimeConfig = useRuntimeConfig();

const [{ data: postsPayload }, { data: homePage }] = await Promise.all([
  useFetch<PaginatedResponse<Post>>("/api/posts-proxy?page=1&pageSize=10"),
  useFetch<StrapiPage | null>("/api/internal/home-page"),
]);

const posts = computed(() => postsPayload.value?.data ?? []);
const total = computed(() => postsPayload.value?.meta?.pagination?.total ?? 0);

useSeoMeta({
  title: SITE_TITLE,
  ogTitle: SITE_TITLE,
  description: SITE_DESCRIPTION,
  ogDescription: SITE_DESCRIPTION,
  keywords: SITE_KEYWORDS.join(", "),
  ogType: "website",
  ogSiteName: SITE_NAME,
  ogUrl: runtimeConfig.public.siteUrl,
  twitterCard: "summary_large_image",
});
</script>
