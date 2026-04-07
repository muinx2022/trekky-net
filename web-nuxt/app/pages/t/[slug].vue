<template>
  <div v-if="tag" class="space-y-4">
    <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white px-6 py-6 shadow-sm">
      <h1 class="text-2xl font-bold text-slate-900 sm:text-3xl">#{{ tag.name }}</h1>
      <div v-if="tag.description" class="mt-3">
        <RichTextContent :html="tag.description" />
      </div>
    </section>

    <InfinitePosts :initial-posts="posts" :initial-total="total" :tag-slug="slug" />
  </div>
</template>

<script setup lang="ts">
import { buildOgImages, SITE_NAME, stripHtml, truncate } from "~~/shared/seo";
import type { PaginatedResponse, Post, Tag } from "~~/shared/types";

const route = useRoute();
const config = useRuntimeConfig();
const slug = route.params.slug as string;

const [{ data: tagData }, { data: postsPayload }] = await Promise.all([
  useFetch<Tag | null>(`/api/internal/tag/${slug}`),
  useFetch<PaginatedResponse<Post>>(`/api/posts-proxy?page=1&pageSize=10&tag=${encodeURIComponent(slug)}`),
]);

const tag = computed(() => tagData.value);
if (!tag.value) throw createError({ statusCode: 404, statusMessage: "Tag not found" });

const description = computed(() =>
  tag.value?.description
    ? truncate(stripHtml(tag.value.description), 160)
    : `Bai viet duoc gan the #${tag.value?.name} tren ${SITE_NAME}.`,
);

useSeoMeta({
  title: `#${tag.value.name}`,
  description: description.value,
  ogTitle: `#${tag.value.name}`,
  ogDescription: description.value,
  ogImage: buildOgImages(undefined, config.public.siteUrl)[0].url,
});

const posts = computed(() => postsPayload.value?.data ?? []);
const total = computed(() => postsPayload.value?.meta?.pagination?.total ?? 0);
</script>
