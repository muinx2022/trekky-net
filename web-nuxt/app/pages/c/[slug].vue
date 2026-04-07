<template>
  <div v-if="category" class="space-y-4">
    <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white px-6 py-6 shadow-sm">
      <h1 class="text-2xl font-bold text-slate-900 sm:text-3xl">{{ category.name }}</h1>
      <div v-if="category.description" class="mt-3">
        <RichTextContent :html="category.description" />
      </div>

      <div v-if="category.children?.length" class="mt-4 border-t border-slate-200 pt-4">
        <h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Danh muc con</h2>
        <div class="flex flex-wrap gap-2">
          <NuxtLink
            v-for="child in category.children"
            :key="child.documentId"
            :to="`/c/${child.slug}`"
            class="rounded-full border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-100"
          >
            {{ child.name }}
          </NuxtLink>
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
    : `Bai viet trong danh muc ${category.value?.name} tren ${SITE_NAME}.`,
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
