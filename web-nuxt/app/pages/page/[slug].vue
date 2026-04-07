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
import { buildBreadcrumbSchema, buildCanonicalUrl, buildOgImages, SITE_NAME, stripHtml, truncate } from "~~/shared/seo";
import type { StrapiPage } from "~~/shared/types";

const route = useRoute();
const config = useRuntimeConfig();
const slug = route.params.slug as string;
const { data } = await useFetch<StrapiPage | null>(`/api/internal/page/${slug}`);
const page = computed(() => data.value);
if (!page.value) throw createError({ statusCode: 404, statusMessage: "Page not found" });

const description = computed(() => (page.value?.content ? truncate(stripHtml(page.value.content), 160) : `${page.value?.title} - ${SITE_NAME}`));
const canonicalUrl = computed(() => buildCanonicalUrl(`/page/${slug}`, config.public.siteUrl));
const ogImage = computed(() => buildOgImages(undefined, config.public.siteUrl, page.value.title)[0]);
const breadcrumbSchema = computed(() =>
  buildBreadcrumbSchema([
    { name: SITE_NAME, item: buildCanonicalUrl("/", config.public.siteUrl) },
    { name: page.value?.title ?? "Page", item: canonicalUrl.value },
  ]),
);

useSeoMeta({
  title: page.value.title,
  description: description.value,
  ogTitle: page.value.title,
  ogDescription: description.value,
  ogUrl: canonicalUrl.value,
  ogType: "article",
  ogImage: ogImage.value.url,
  ogImageAlt: ogImage.value.alt,
  twitterCard: "summary_large_image",
  twitterTitle: page.value.title,
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
      key: `page-schema-${page.value.documentId}`,
      type: "application/ld+json",
      innerHTML: JSON.stringify(breadcrumbSchema.value),
    },
  ],
});
</script>
