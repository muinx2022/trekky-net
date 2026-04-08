<template>
  <div class="space-y-4">
    <PostCard v-for="post in posts" :key="post.documentId" :post="post" />

    <div v-if="posts.length === 0" class="rounded-2xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500">
      Không có bài viết nào.
    </div>

    <div v-if="canLoadMore" class="flex justify-center pt-2">
      <button
        class="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="pending"
        @click="loadMore"
      >
        {{ pending ? "Đang tải..." : "Xem thêm" }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PaginatedResponse, Post } from "../../shared/types";

const props = defineProps<{
  initialPosts: Post[];
  initialTotal: number;
  categorySlug?: string;
  tagSlug?: string;
  authorUsername?: string;
}>();

const feedKey = computed(() => {
  if (props.categorySlug) return `category:${props.categorySlug}`;
  if (props.tagSlug) return `tag:${props.tagSlug}`;
  if (props.authorUsername) return `author:${props.authorUsername}`;
  return "home";
});

const posts = useState<Post[]>(`infinite-posts:${feedKey.value}:items`, () => [...(props.initialPosts ?? [])]);
const total = useState<number>(`infinite-posts:${feedKey.value}:total`, () => props.initialTotal ?? 0);
const page = useState<number>(`infinite-posts:${feedKey.value}:page`, () => 1);
const pending = ref(false);

function resetFromInitial() {
  posts.value = [...(props.initialPosts ?? [])];
  total.value = props.initialTotal ?? 0;
  page.value = 1;
}

watch(
  () => [props.initialPosts, props.initialTotal, feedKey.value],
  () => {
    if (posts.value.length === 0) {
      resetFromInitial();
      return;
    }
    if (page.value <= 1 && posts.value.length <= (props.initialPosts ?? []).length) {
      resetFromInitial();
    }
  },
  { immediate: true },
);

const canLoadMore = computed(() => posts.value.length < total.value);

async function loadMore() {
  pending.value = true;
  const nextPage = page.value + 1;
  const query = new URLSearchParams({
    page: String(nextPage),
    pageSize: "10",
  });
  if (props.categorySlug) query.set("category", props.categorySlug);
  if (props.tagSlug) query.set("tag", props.tagSlug);
  if (props.authorUsername) query.set("author", props.authorUsername);
  const response = await $fetch<PaginatedResponse<Post>>(`/api/posts-proxy?${query.toString()}`).catch(() => null);
  pending.value = false;
  if (!response) return;
  posts.value = [...posts.value, ...(response.data ?? [])];
  total.value = response.meta?.pagination?.total ?? total.value;
  page.value = nextPage;
}
</script>
