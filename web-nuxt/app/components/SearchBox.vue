<template>
  <div ref="containerRef" class="relative w-full">
    <div :class="searchShellClass">
      <span :class="searchIconClass">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
      </span>
      <input
        v-model="query"
        type="text"
        placeholder="Tìm kiếm..."
        :class="inputClass"
        @keydown.enter.prevent="handleSubmit"
        @focus="hasSuggestions && (showDropdown = true)"
      />
      <button
        type="button"
        class="mr-1 flex items-center gap-1 rounded-full bg-gray-500 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-gray-600"
        aria-label="Tìm kiếm"
        @click="handleSubmit"
      >
        <svg v-if="loading" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        Tìm
      </button>
    </div>

    <div v-if="showDropdown" :class="dropdownClass">
      <div v-if="!hasSuggestions" class="px-4 py-3 text-sm text-gray-400">Không tìm thấy kết quả</div>
      <template v-else>
        <div v-if="suggestions.posts.length">
          <div class="border-b border-gray-100 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">Bài viết</div>
          <button
            v-for="(post, index) in suggestions.posts.slice(0, 4)"
            :key="`post-${post.documentId}-${index}`"
            type="button"
            class="flex w-full items-start gap-2 px-4 py-2.5 text-left hover:bg-gray-50"
            @mousedown.prevent="handleSelect(`/p/${post.slug}--${post.documentId}`)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-gray-800">{{ post.title }}</p>
              <p v-if="post.excerpt" class="truncate text-xs text-gray-400">{{ stripHtml(post.excerpt) }}</p>
            </div>
          </button>
        </div>

        <div v-if="suggestions.tags.length" class="border-t border-gray-100">
          <div class="px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">Tags</div>
          <div class="flex flex-wrap gap-1.5 px-4 pb-3">
            <button
              v-for="(tag, index) in suggestions.tags.slice(0, 5)"
              :key="`tag-${tag.documentId}-${index}`"
              type="button"
              class="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-200"
              @mousedown.prevent="handleSelect(`/t/${tag.slug}`)"
            >
              #{{ tag.name }}
            </button>
          </div>
        </div>

        <div v-if="suggestions.categories.length" class="border-t border-gray-100">
          <div class="px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">Danh mục</div>
          <button
            v-for="(category, index) in suggestions.categories.slice(0, 3)"
            :key="`category-${category.documentId}-${index}`"
            type="button"
            class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
            @mousedown.prevent="handleSelect(`/c/${category.slug}`)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2z" />
            </svg>
            {{ category.name }}
          </button>
        </div>

        <div class="border-t border-gray-100">
          <button
            type="button"
            class="flex w-full items-center justify-center gap-1.5 px-4 py-2.5 text-sm font-medium text-blue-600 hover:bg-blue-50"
            @mousedown.prevent="handleSubmit"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            Xem tất cả kết quả cho "{{ query }}"
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SearchSuggestions } from "~~/shared/types";

const props = defineProps<{
  onSearch?: (query: string) => void;
}>();

const router = useRouter();
const theme = useTheme();
const query = ref("");
const suggestions = ref<SearchSuggestions>({ posts: [], tags: [], categories: [] });
const showDropdown = ref(false);
const loading = ref(false);
const containerRef = ref<HTMLElement | null>(null);
let outsideHandler: ((event: MouseEvent) => void) | null = null;

const hasSuggestions = computed(
  () => suggestions.value.posts.length > 0 || suggestions.value.tags.length > 0 || suggestions.value.categories.length > 0,
);
const searchShellClass = computed(() =>
  theme.isDark.value
    ? "flex items-center rounded-full border border-slate-500/70 bg-slate-900/80 transition-all focus-within:border-sky-400 focus-within:bg-slate-950 focus-within:ring-2 focus-within:ring-sky-500/30"
    : "flex items-center rounded-full border border-gray-300 bg-gray-100 transition-all focus-within:border-blue-400 focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-500",
);
const searchIconClass = computed(() => (theme.isDark.value ? "pointer-events-none pl-3 text-slate-400" : "pointer-events-none pl-3 text-gray-400"));
const inputClass = computed(() =>
  theme.isDark.value
    ? "flex-1 bg-transparent py-2 pl-2 pr-1 text-sm text-slate-100 placeholder-slate-400 focus:outline-none"
    : "flex-1 bg-transparent py-2 pl-2 pr-1 text-sm text-gray-700 placeholder-gray-500 focus:outline-none",
);
const dropdownClass = computed(() =>
  theme.isDark.value
    ? "absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-lg"
    : "absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg",
);

function stripHtml(html: string) {
  return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function handleSubmit() {
  const nextQuery = query.value.trim();
  if (!nextQuery) return;
  showDropdown.value = false;
  if (props.onSearch) {
    props.onSearch(nextQuery);
    return;
  }
  router.push(`/search?q=${encodeURIComponent(nextQuery)}`);
}

function handleSelect(href: string) {
  showDropdown.value = false;
  router.push(href);
}

watch(
  query,
  (value, _oldValue, onCleanup) => {
    const trimmed = value.trim();
    if (trimmed.length < 2) {
      suggestions.value = { posts: [], tags: [], categories: [] };
      showDropdown.value = false;
      return;
    }

    const timer = window.setTimeout(async () => {
      loading.value = true;
      try {
        const payload = await $fetch<SearchSuggestions>(`/api/search-proxy?q=${encodeURIComponent(trimmed)}`);
        suggestions.value = payload ?? { posts: [], tags: [], categories: [] };
        showDropdown.value = true;
      } catch {
        suggestions.value = { posts: [], tags: [], categories: [] };
      } finally {
        loading.value = false;
      }
    }, 300);

    onCleanup(() => window.clearTimeout(timer));
  },
  { flush: "post" },
);

onMounted(() => {
  outsideHandler = (event: MouseEvent) => {
    if (!containerRef.value || containerRef.value.contains(event.target as Node)) return;
    showDropdown.value = false;
  };
  document.addEventListener("mousedown", outsideHandler);
});

onBeforeUnmount(() => {
  if (outsideHandler) document.removeEventListener("mousedown", outsideHandler);
});
</script>
