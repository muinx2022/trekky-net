<template>
  <article v-if="post" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div class="px-6 pt-5 pb-5">
      <div v-if="post.categories?.length" class="mb-3 flex flex-wrap items-center gap-1 text-xs text-slate-500">
        <span v-for="(category, index) in post.categories" :key="category.documentId" class="flex items-center gap-1">
          <span v-if="index > 0" class="text-slate-300">·</span>
          <NuxtLink :to="`/c/${category.slug}`" class="font-medium hover:text-slate-800 hover:underline">{{ category.name }}</NuxtLink>
        </span>
      </div>

      <h1 class="text-2xl font-bold leading-snug text-slate-900">{{ post.title }}</h1>

      <div class="mt-3 flex items-center gap-2">
        <img v-if="authorAvatarUrl" :src="authorAvatarUrl" :alt="post.author?.username || 'avatar'" class="h-8 w-8 rounded-full object-cover bg-slate-300" />
        <div v-else class="flex h-8 w-8 items-center justify-center rounded-full bg-slate-300 text-xs font-bold text-slate-600">
          {{ authorInitial }}
        </div>
        <div class="flex items-center gap-1.5 text-sm text-slate-500">
          <NuxtLink :to="post.author?.username ? `/u/${post.author.username}` : '#'" class="font-medium text-slate-700 hover:text-slate-900">
            {{ post.author?.username ?? "Ẩn danh" }}
          </NuxtLink>
          <span v-if="formattedDate">·</span>
          <span v-if="formattedDate">{{ formattedDate }}</span>
        </div>
      </div>
    </div>

    <div v-if="galleryImages.length" class="space-y-3 px-6 pb-5">
      <button type="button" class="block overflow-hidden rounded-2xl bg-slate-100" aria-label="Mở ảnh lớn" @click="lightboxIndex = activeImageIndex">
        <img :src="activeImage.src" :alt="activeImage.alt ?? ''" class="max-h-[540px] w-full object-cover" draggable="false" />
      </button>

      <div v-if="galleryImages.length > 1" class="grid grid-cols-4 gap-2 sm:grid-cols-5 md:grid-cols-6">
        <button
          v-for="(image, index) in galleryImages"
          :key="`${image.src}-${index}`"
          type="button"
          class="aspect-square overflow-hidden rounded-lg border-2 transition"
          :class="index === activeImageIndex ? 'border-slate-900' : 'border-transparent hover:border-slate-300'"
          :aria-label="`Xem ảnh ${index + 1}`"
          @click="activeImageIndex = index"
        >
          <img :src="image.src" :alt="image.alt ?? ''" class="h-full w-full object-cover" draggable="false" />
        </button>
      </div>
    </div>

    <div class="px-6 pb-6">
      <RichTextWithLightbox :html="contentWithoutImages" />
    </div>

    <div v-if="post.tags?.length" class="flex flex-wrap gap-1.5 px-6 pb-5">
      <NuxtLink
        v-for="tag in post.tags"
        :key="tag.documentId"
        :to="`/t/${tag.slug}`"
        class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-500 hover:bg-slate-200 hover:text-slate-700"
      >
        #{{ tag.name }}
      </NuxtLink>
    </div>

    <div class="border-t border-slate-100 px-6">
      <PostActions target-type="post" :target-document-id="post.documentId" />
    </div>

    <div class="px-6 pb-6 pt-5">
      <h2 class="mb-4 text-sm font-semibold text-slate-700">
        Bình luận <span v-if="comments.length" class="font-normal text-slate-400">({{ comments.length }})</span>
      </h2>
      <GenericComments target-type="post" :target-document-id="post.documentId" :initial-comments="comments" />
    </div>
  </article>

  <Lightbox
    v-if="lightboxIndex !== null"
    :images="galleryImages"
    :index="lightboxIndex"
    @close="lightboxIndex = null"
    @navigate="(index) => (lightboxIndex = index)"
  />
</template>

<script setup lang="ts">
import {
  buildArticleSchema,
  buildBreadcrumbSchema,
  buildCanonicalUrl,
  buildOgImages,
  extractImagesFromHtml,
  extractFirstImageFromHtml,
  SITE_NAME,
  stripImagesFromHtml,
  stripHtml,
  toAbsoluteMediaUrl,
  truncate,
} from "~~/shared/seo";
import type { Comment, Post } from "~~/shared/types";

const route = useRoute();
const config = useRuntimeConfig();
const id = route.params.id as string;

const [{ data: postData }, { data: commentsData }] = await Promise.all([
  useFetch<Post | null>(`/api/internal/post/${encodeURIComponent(id)}`),
  useFetch<Comment[]>(`/api/internal/post-comments/${encodeURIComponent(id)}`),
]);

const post = computed(() => postData.value);
if (!post.value) throw createError({ statusCode: 404, statusMessage: "Post not found" });

const canonicalId = `${post.value.slug}--${post.value.documentId}`;
if (id !== canonicalId) {
  await navigateTo(`/p/${canonicalId}`, { redirectCode: 301, replace: true });
}

const comments = computed(() => commentsData.value ?? []);
const authorAvatarUrl = computed(() => toAbsoluteMediaUrl(post.value?.author?.avatar?.url, config.public.apiUrl) ?? "");
const authorInitial = computed(() => (post.value?.author?.username ?? "?").slice(0, 1).toUpperCase());
const formattedDate = computed(() => {
  const source = post.value?.createdAt || post.value?.publishedAt;
  return source ? new Date(source).toLocaleString("vi-VN") : "";
});
const description = computed(() => truncate(stripHtml(post.value?.content ?? ""), 160));
const contentImages = computed(() => extractImagesFromHtml(post.value?.content ?? "", config.public.apiUrl));
const postGalleryImages = computed(() =>
  (post.value?.images ?? [])
    .filter((item) => item.url && !item.mime?.startsWith("video/"))
    .map((item) => ({
      src: toAbsoluteMediaUrl(item.url, config.public.apiUrl) ?? item.url,
      alt: item.alternativeText ?? undefined,
    })),
);
const galleryImages = computed(() => {
  const seen = new Set<string>();
  return [...contentImages.value, ...postGalleryImages.value].filter((item) => {
    if (!item.src || seen.has(item.src)) return false;
    seen.add(item.src);
    return true;
  });
});
const contentWithoutImages = computed(() => stripImagesFromHtml(post.value?.content ?? ""));
const activeImageIndex = ref(0);
const lightboxIndex = ref<number | null>(null);
const activeImage = computed(() => galleryImages.value[activeImageIndex.value] ?? galleryImages.value[0] ?? { src: "", alt: "" });
const imageUrl = computed(
  () => galleryImages.value[0]?.src ?? extractFirstImageFromHtml(post.value?.content ?? "", config.public.apiUrl),
);
const canonicalUrl = computed(() => buildCanonicalUrl(`/p/${canonicalId}`, config.public.siteUrl));
const ogImage = computed(() => buildOgImages(imageUrl.value, config.public.siteUrl, post.value.title)[0]);
const articleSchema = computed(() =>
  buildArticleSchema({
    title: post.value.title,
    description: description.value,
    canonicalUrl: canonicalUrl.value,
    image: ogImage.value.url,
    publishedTime: post.value.publishedAt ?? post.value.createdAt ?? null,
    modifiedTime: post.value.updatedAt ?? post.value.publishedAt ?? post.value.createdAt ?? null,
    authorName: post.value.author?.username ?? null,
  }),
);
const breadcrumbSchema = computed(() =>
  buildBreadcrumbSchema([
    { name: SITE_NAME, item: buildCanonicalUrl("/", config.public.siteUrl) },
    { name: post.value.title, item: canonicalUrl.value },
  ]),
);

watch(
  galleryImages,
  () => {
    activeImageIndex.value = 0;
    lightboxIndex.value = null;
  },
  { immediate: true },
);

useSeoMeta({
  title: post.value.title,
  description: description.value,
  ogTitle: post.value.title,
  ogDescription: description.value,
  ogType: "article",
  ogSiteName: SITE_NAME,
  ogUrl: canonicalUrl.value,
  ogImage: ogImage.value.url,
  ogImageAlt: ogImage.value.alt,
  twitterCard: "summary_large_image",
  twitterTitle: post.value.title,
  twitterDescription: description.value,
  twitterImage: ogImage.value.url,
  articlePublishedTime: post.value.publishedAt ?? post.value.createdAt,
  articleModifiedTime: post.value.updatedAt ?? post.value.publishedAt ?? post.value.createdAt,
  articleAuthor: post.value.author?.username ?? SITE_NAME,
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
      key: `post-schema-${post.value.documentId}`,
      type: "application/ld+json",
      innerHTML: JSON.stringify([articleSchema.value, breadcrumbSchema.value]),
    },
  ],
});
</script>
