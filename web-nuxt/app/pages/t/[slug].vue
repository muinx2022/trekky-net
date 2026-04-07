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
import { buildBreadcrumbSchema, buildCanonicalUrl, buildOgImages, SITE_NAME, stripHtml, truncate } from "~~/shared/seo";
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

const posts = computed(() => postsPayload.value?.data ?? []);
const total = computed(() => postsPayload.value?.meta?.pagination?.total ?? 0);
const description = computed(() =>
  tag.value?.description ? truncate(stripHtml(tag.value.description), 160) : `Bài viết được gắn thẻ #${tag.value?.name} trên ${SITE_NAME}.`,
);
const canonicalUrl = computed(() => buildCanonicalUrl(`/t/${slug}`, config.public.siteUrl));
const ogImage = computed(() => buildOgImages(undefined, config.public.siteUrl, `#${tag.value.name}`)[0]);
const breadcrumbSchema = computed(() =>
  buildBreadcrumbSchema([
    { name: SITE_NAME, item: buildCanonicalUrl("/", config.public.siteUrl) },
    { name: `#${tag.value?.name ?? "tag"}`, item: canonicalUrl.value },
  ]),
);

useSeoMeta({
  title: `#${tag.value.name}`,
  description: description.value,
  ogTitle: `#${tag.value.name}`,
  ogDescription: description.value,
  ogUrl: canonicalUrl.value,
  ogType: "website",
  ogImage: ogImage.value.url,
  ogImageAlt: ogImage.value.alt,
  twitterCard: "summary_large_image",
  twitterTitle: `#${tag.value.name}`,
  twitterDescription: description.value,
  twitterImage: ogImage.value.url,
});

useHead({
  link: [
    {
      rel: "canonical",
      href: canonicalUrl.value,
    },
  ],
  script: [
    {
      key: `tag-schema-${tag.value.documentId}`,
      type: "application/ld+json",
      innerHTML: JSON.stringify(breadcrumbSchema.value),
    },
  ],
});
</script>
