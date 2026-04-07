<template>
  <article class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div class="p-5">
      <div v-if="post.categories?.length" class="mb-3 flex flex-wrap gap-2">
        <NuxtLink
          v-for="category in post.categories"
          :key="category.documentId"
          :to="`/c/${category.slug}`"
          class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200"
        >
          {{ category.name }}
        </NuxtLink>
      </div>

      <NuxtLink :to="`/p/${post.slug}--${post.documentId}`" class="block">
        <h2 class="text-xl font-semibold text-slate-900 hover:text-sky-700">{{ post.title }}</h2>
      </NuxtLink>

      <p v-if="post.author?.username || dateLabel" class="mt-2 text-sm text-slate-500">
        <span v-if="post.author?.username">{{ post.author.username }}</span>
        <span v-if="post.author?.username && dateLabel"> · </span>
        <span v-if="dateLabel">{{ dateLabel }}</span>
      </p>

      <div v-if="preview.kind !== 'none'" class="relative mt-4 overflow-hidden rounded-2xl">
        <img v-if="preview.kind === 'image'" :src="preview.src" :alt="post.title" class="h-64 w-full object-cover" />
        <video
          v-else-if="preview.kind === 'video'"
          :src="preview.src"
          class="h-64 w-full bg-slate-950 object-cover"
          muted
          playsinline
          preload="metadata"
          controls
        />
        <iframe
          v-else-if="preview.kind === 'embed'"
          :src="preview.src"
          class="h-64 w-full bg-slate-950"
          loading="lazy"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowfullscreen
        />

        <span
          v-if="preview.badge"
          class="absolute left-4 top-4 inline-flex items-center rounded-full bg-black/65 px-3 py-1 text-xs font-medium text-white backdrop-blur"
        >
          {{ preview.badge }}
        </span>
      </div>

      <div v-if="displaySummary" class="mt-3 line-clamp-4 text-sm leading-6 text-slate-600">
        {{ displaySummary }}
      </div>

      <div v-if="post.tags?.length" class="mt-4 flex flex-wrap gap-2">
        <NuxtLink
          v-for="tag in post.tags"
          :key="tag.documentId"
          :to="`/t/${tag.slug}`"
          class="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:bg-slate-50"
        >
          #{{ tag.name }}
        </NuxtLink>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { stripHtml } from "../../shared/seo";
import type { Post } from "../../shared/types";

const props = defineProps<{
  post: Post;
}>();

const dateLabel = computed(() => {
  const source = props.post.publishedAt || props.post.createdAt;
  return source ? formatRelativePostTime(source) : "";
});

type Preview =
  | { kind: "image"; src: string; badge?: string }
  | { kind: "video"; src: string; badge?: string }
  | { kind: "embed"; src: string; badge?: string }
  | { kind: "none"; badge?: string };

const preview = computed<Preview>(() => {
  const galleryImages = (props.post.images ?? []).filter((item) => item.url && !item.mime?.startsWith("video/"));
  if (galleryImages.length > 0) {
    return {
      kind: "image",
      src: galleryImages[0].url,
      badge: galleryImages.length > 1 ? `Gallery ${galleryImages.length}` : undefined,
    };
  }

  const galleryVideo = (props.post.images ?? []).find((item) => item.url && item.mime?.startsWith("video/"));
  if (galleryVideo) {
    return { kind: "video", src: galleryVideo.url, badge: "Video" };
  }

  const contentVideo = extractContentVideo(props.post.content);
  if (contentVideo) {
    return contentVideo;
  }

  const contentImage = extractContentImage(props.post.content);
  if (contentImage) {
    return { kind: "image", src: contentImage };
  }

  return { kind: "none" };
});

const displaySummary = computed(() => {
  const excerptText = toPlainText(props.post.excerpt ?? "");
  if (excerptText) return excerptText;
  return truncateWords(toPlainText(props.post.content ?? ""), 100);
});

function toPlainText(value: string) {
  return stripHtml(value).replace(/\s+/g, " ").trim();
}

function truncateWords(value: string, maxWords: number) {
  if (!value) return "";
  const words = value.split(/\s+/).filter(Boolean);
  if (words.length <= maxWords) return words.join(" ");
  return `${words.slice(0, maxWords).join(" ")} ...`;
}

function formatRelativePostTime(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  if (Number.isNaN(diff) || diff < 0) return "";

  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days = Math.floor(hours / 24);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);

  if (mins < 1) return "vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  if (hours < 24) return `${hours} giờ trước`;
  if (days < 30) return `${days} ngày trước`;
  if (days < 365) return `${Math.max(months, 1)} tháng trước`;
  return `${Math.max(years, 1)} năm trước`;
}

function extractContentVideo(html: string): Preview | null {
  if (!html) return null;

  const iframeMatch = html.match(/<iframe[^>]+src=["']([^"']+)["']/i);
  if (iframeMatch?.[1]) {
    return { kind: "embed", src: iframeMatch[1], badge: "Video" };
  }

  const videoMatch = html.match(/<video[^>]+src=["']([^"']+)["']/i) ?? html.match(/<source[^>]+src=["']([^"']+)["'][^>]*type=["']video\//i);
  if (videoMatch?.[1]) {
    return { kind: "video", src: videoMatch[1], badge: "Video" };
  }

  return null;
}

function extractContentImage(html: string) {
  if (!html) return "";
  const match = html.match(/<img[^>]+src=["']([^"']+)["']/i);
  return match?.[1] ?? "";
}
</script>
