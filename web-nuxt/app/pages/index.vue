<template>
  <div class="space-y-4">
    <section class="overflow-hidden rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#e0f2fe_45%,#fff7ed_100%)] shadow-sm dark:border-slate-700 dark:bg-[linear-gradient(135deg,#0f172a_0%,#0b253a_45%,#172033_100%)]">
      <div class="px-6 py-8 sm:px-8 lg:px-10">
        <span class="inline-flex w-fit items-center rounded-full border border-white/70 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 shadow-sm backdrop-blur dark:border-slate-500/60 dark:bg-slate-900/60 dark:text-sky-200">
          Trekky
        </span>
        <div class="mt-3 space-y-3">
          <h1 class="text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl">
            {{ homePage?.title || "Chia sẻ đam mê, trải nghiệm và góc nhìn riêng" }}
          </h1>
          <div v-if="homePage?.content" class="max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
            <RichTextContent :html="homePage.content" />
          </div>
          <p v-else class="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
            Khám phá những bài viết mới, câu chuyện thật và trải nghiệm được chia sẻ từ cộng đồng Trekky.
          </p>
        </div>
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
