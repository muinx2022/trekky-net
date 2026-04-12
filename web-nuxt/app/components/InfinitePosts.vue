<template>
  <div class="space-y-4">
    <PostCard v-for="post in posts" :key="post.documentId" :post="post" />

    <div v-if="posts.length === 0" class="rounded-2xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500">
      Không có bài viết nào.
    </div>

    <div
      v-if="canLoadMore || pending"
      ref="loadTrigger"
      class="flex min-h-16 items-center justify-center pt-2 text-sm text-slate-500"
      aria-live="polite"
    >
      <span v-if="pending">Đang tải thêm bài viết...</span>
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
const route = useRoute();

type StoredFeedState = {
  posts: Post[];
  total: number;
  page: number;
  historyPosition?: number;
};

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
const loadTrigger = ref<HTMLElement | null>(null);
const storageKey = computed(() => `trekky:infinite-posts:${feedKey.value}`);
const scrollStorageKey = computed(() => `trekky:scroll:${route.fullPath}`);
let loadObserver: IntersectionObserver | null = null;

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

function restoreFromSession() {
  if (!import.meta.client) return;
  const raw = window.sessionStorage.getItem(storageKey.value);
  if (!raw) return;
  try {
    const stored = JSON.parse(raw) as StoredFeedState;
    if (!Array.isArray(stored.posts) || typeof stored.total !== "number" || typeof stored.page !== "number") return;
    const currentPosition = (window.history.state as { position?: number } | null)?.position ?? 0;
    if (stored.historyPosition !== undefined && stored.historyPosition !== currentPosition) {
      window.sessionStorage.removeItem(storageKey.value);
      window.sessionStorage.removeItem(scrollStorageKey.value);
      window.sessionStorage.removeItem("trekky:feed-restore-needed");
      return;
    }
    posts.value = stored.posts;
    total.value = stored.total;
    page.value = stored.page;
  } catch {
    window.sessionStorage.removeItem(storageKey.value);
  }
}

function saveScrollPosition() {
  if (!import.meta.client) return;
  window.sessionStorage.setItem(scrollStorageKey.value, String(window.scrollY));
}

function restoreScrollPosition() {
  if (!import.meta.client) return;
  const raw = window.sessionStorage.getItem(scrollStorageKey.value);
  if (!raw) return;
  const top = Number(raw);
  if (!Number.isFinite(top) || top <= 0) return;
  window.scrollTo({ top, behavior: "auto" });
}

watch(
  () => [posts.value, total.value, page.value, storageKey.value],
  () => {
    if (!import.meta.client) return;
    const payload: StoredFeedState = {
      posts: posts.value,
      total: total.value,
      page: page.value,
      historyPosition: (window.history.state as { position?: number } | null)?.position ?? 0,
    };
    window.sessionStorage.setItem(storageKey.value, JSON.stringify(payload));
    if (page.value > 1) {
      window.sessionStorage.setItem("trekky:feed-restore-needed", "1");
    } else {
      window.sessionStorage.removeItem("trekky:feed-restore-needed");
    }
  },
  { deep: true },
);

const canLoadMore = computed(() => posts.value.length < total.value);

function teardownLoadObserver() {
  loadObserver?.disconnect();
  loadObserver = null;
}

function setupLoadObserver() {
  if (!import.meta.client) return;
  teardownLoadObserver();
  if (!loadTrigger.value || !("IntersectionObserver" in window) || !canLoadMore.value) return;
  loadObserver = new IntersectionObserver(
    (entries) => {
      const entry = entries[0];
      if (!entry?.isIntersecting || pending.value || !canLoadMore.value) return;
      void loadMore();
    },
    {
      rootMargin: "0px 0px 320px 0px",
    },
  );
  loadObserver.observe(loadTrigger.value);
}

watch(loadTrigger, async () => {
  await nextTick();
  setupLoadObserver();
});

watch(canLoadMore, async (value) => {
  if (!value) {
    teardownLoadObserver();
    return;
  }
  await nextTick();
  setupLoadObserver();
});

onMounted(async () => {
  restoreFromSession();
  await nextTick();
  restoreScrollPosition();
  requestAnimationFrame(() => {
    restoreScrollPosition();
    requestAnimationFrame(() => {
      delete document.documentElement.dataset.scrollRestoring;
      window.sessionStorage.removeItem("trekky:feed-restore-needed");
    });
  });
  window.addEventListener("scroll", saveScrollPosition, { passive: true });
  window.addEventListener("pagehide", saveScrollPosition);
  setupLoadObserver();
});

onBeforeUnmount(() => {
  saveScrollPosition();
  window.removeEventListener("scroll", saveScrollPosition);
  window.removeEventListener("pagehide", saveScrollPosition);
  teardownLoadObserver();
});

async function loadMore() {
  if (pending.value || !canLoadMore.value) return;

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

  await nextTick();
  setupLoadObserver();
}
</script>
