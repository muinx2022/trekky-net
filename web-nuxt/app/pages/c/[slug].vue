<template>
  <div v-if="category" class="space-y-4">
    <section class="overflow-hidden rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#e0f2fe_45%,#fff7ed_100%)] shadow-sm dark:border-slate-700 dark:bg-[linear-gradient(135deg,#0f172a_0%,#0b253a_45%,#172033_100%)]">
      <div class="px-6 py-8 sm:px-8 lg:px-10">
        <span class="inline-flex w-fit items-center rounded-full border border-white/70 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 shadow-sm backdrop-blur dark:border-slate-500/60 dark:bg-slate-900/60 dark:text-sky-200">
          Danh mục
        </span>
        <div class="mt-3 space-y-3">
          <h1 class="text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl">{{ category.name }}</h1>
          <div v-if="category.description" class="max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
            <RichTextContent :html="category.description" />
          </div>
          <p v-else class="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
            Tổng hợp các bài viết liên quan đến {{ category.name.toLowerCase() }} trên Trekky.
          </p>
        </div>

        <div v-if="category.children?.length" class="mt-6 border-t border-white/70 pt-5 dark:border-slate-600/70">
          <h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Danh mục con</h2>
          <div class="flex flex-wrap gap-2">
            <NuxtLink
              v-for="child in category.children"
              :key="child.documentId"
              :to="`/c/${child.slug}`"
              class="rounded-full border border-white/80 bg-white/75 px-3 py-1 text-sm text-slate-700 shadow-sm backdrop-blur hover:bg-white dark:border-slate-500/60 dark:bg-slate-900/55 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {{ child.name }}
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <InfinitePosts :initial-posts="posts" :initial-total="total" :category-slug="slug" />
  </div>
</template>

<script setup lang="ts">
import { buildOgImages, SITE_NAME, stripHtml, truncate } from "~~/shared/seo";
import type { Category, PaginatedResponse, Post } from "~~/shared/types";

const route = useRoute();
const config = useRuntimeConfig();
const slug = route.params.slug as string;

const [{ data: categoryData }, { data: postsPayload }] = await Promise.all([
  useFetch<Category | null>(`/api/internal/category/${slug}`),
  useFetch<PaginatedResponse<Post>>(`/api/posts-proxy?page=1&pageSize=10&category=${encodeURIComponent(slug)}`),
]);

const category = computed(() => categoryData.value);
if (!category.value) throw createError({ statusCode: 404, statusMessage: "Category not found" });

const description = computed(() =>
  category.value?.description
    ? truncate(stripHtml(category.value.description), 160)
    : `Bài viết trong danh mục ${category.value?.name} trên ${SITE_NAME}.`,
);

useSeoMeta({
  title: category.value.name,
  description: description.value,
  ogTitle: category.value.name,
  ogDescription: description.value,
  ogImage: buildOgImages(undefined, config.public.siteUrl)[0].url,
});

const posts = computed(() => postsPayload.value?.data ?? []);
const total = computed(() => postsPayload.value?.meta?.pagination?.total ?? 0);
</script>
