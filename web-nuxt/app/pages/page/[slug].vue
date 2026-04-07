<template>
  <article v-if="page" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div class="border-b border-slate-100 px-6 py-5">
      <h1 class="text-2xl font-bold text-slate-900">{{ page.title }}</h1>
    </div>
    <div class="px-6 py-6">
      <RichTextWithLightbox :html="page.content ?? ''" />
    </div>
  </article>
</template>

<script setup lang="ts">
import { buildOgImages, SITE_NAME, stripHtml, truncate } from "~~/shared/seo";
import type { StrapiPage } from "~~/shared/types";

const route = useRoute();
const config = useRuntimeConfig();
const slug = route.params.slug as string;
const { data } = await useFetch<StrapiPage | null>(`/api/internal/page/${slug}`);
const page = computed(() => data.value);
if (!page.value) throw createError({ statusCode: 404, statusMessage: "Page not found" });

const description = computed(() =>
  page.value?.content ? truncate(stripHtml(page.value.content), 160) : `${page.value?.title} - ${SITE_NAME}`,
);

useSeoMeta({
  title: page.value.title,
  description: description.value,
  ogTitle: page.value.title,
  ogDescription: description.value,
  ogImage: buildOgImages(undefined, config.public.siteUrl)[0].url,
});
</script>
