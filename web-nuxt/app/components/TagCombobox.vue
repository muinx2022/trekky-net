<template>
  <div ref="containerEl" class="relative">
    <div class="flex min-h-10 flex-wrap items-center gap-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
      <span
        v-for="tag in model"
        :key="tag.documentId"
        class="inline-flex items-center gap-1 rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-800"
      >
        {{ tag.name }}
        <button type="button" :aria-label="`Xoa tag ${tag.name}`" class="inline-flex h-4 w-4 items-center justify-center rounded hover:bg-gray-300" @click="removeTag(tag.documentId)">
          ×
        </button>
      </span>

      <input
        ref="inputEl"
        v-model="query"
        type="text"
        class="min-w-[120px] flex-1 bg-transparent text-sm text-gray-800 outline-none placeholder:text-gray-400"
        :placeholder="model.length === 0 ? 'Go de tim hoac tao tag...' : 'Them tag...'"
        @focus="trimmedQuery && (open = true)"
        @blur="handleCommitCurrent"
        @keydown="handleKeyDown"
      />

      <svg v-if="searching || pendingCount > 0" class="h-4 w-4 animate-spin text-gray-400" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
      </svg>
    </div>

    <div v-if="isDropdownVisible" class="absolute z-30 mt-1 w-full overflow-hidden rounded-md border border-gray-200 bg-white shadow-md">
      <button
        v-for="tag in suggestions"
        :key="tag.documentId"
        type="button"
        class="flex w-full items-center px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
        @mousedown.prevent="addTag(tag)"
      >
        {{ tag.name }}
      </button>

      <button
        v-if="showCreateOption"
        type="button"
        class="flex w-full items-center gap-1.5 px-3 py-2 text-left text-sm text-blue-600 hover:bg-gray-100 disabled:opacity-60"
        :disabled="pendingCount > 0"
        @mousedown.prevent="createTagAndAdd(trimmedQuery)"
      >
        <span class="font-medium">+ Tao tag</span>
        <span class="truncate">"{{ trimmedQuery }}"</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TagOption } from "~~/shared/types";

const model = defineModel<TagOption[]>({ default: [] });
const auth = useAuth();
const query = ref("");
const suggestions = ref<TagOption[]>([]);
const open = ref(false);
const searching = ref(false);
const pendingCount = ref(0);
const containerEl = ref<HTMLElement | null>(null);
const inputEl = ref<HTMLInputElement | null>(null);
let outsideHandler: ((event: MouseEvent | TouchEvent) => void) | null = null;

const trimmedQuery = computed(() => query.value.trim());
const exactMatch = computed(() => suggestions.value.some((tag) => tag.name.toLowerCase() === trimmedQuery.value.toLowerCase()));
const alreadySelected = computed(() => model.value.some((tag) => tag.name.toLowerCase() === trimmedQuery.value.toLowerCase()));
const showCreateOption = computed(() => trimmedQuery.value.length > 0 && !exactMatch.value && !alreadySelected.value);
const isDropdownVisible = computed(() => open.value && (suggestions.value.length > 0 || showCreateOption.value));

function resetInput() {
  query.value = "";
  suggestions.value = [];
  open.value = false;
  inputEl.value?.focus();
}

function addTag(tag: TagOption) {
  if (model.value.some((item) => item.documentId === tag.documentId)) return;
  model.value = [...model.value, tag];
  resetInput();
}

function removeTag(documentId: string) {
  model.value = model.value.filter((tag) => tag.documentId !== documentId);
}

async function createTagAndAdd(name: string) {
  pendingCount.value += 1;
  try {
    const response = await auth.authorizedFetch("/api/tags-proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (response.status === 401) {
      auth.openLoginModal();
      return;
    }
    if (!response.ok) return;
    const payload = (await response.json().catch(() => ({}))) as {
      data?: TagOption;
      document_id?: string;
      documentId?: string;
      name?: string;
      slug?: string;
    };
    const created = payload.data ?? {
      documentId: payload.document_id ?? payload.documentId ?? "",
      name: payload.name ?? "",
      slug: payload.slug,
    };
    if (created.documentId && created.name && !model.value.some((item) => item.documentId === created.documentId)) {
      addTag(created);
    }
  } finally {
    pendingCount.value -= 1;
  }
}

async function commitPending() {
  const name = query.value.trim();
  if (!name) return;
  const matched = suggestions.value.find((tag) => tag.name.toLowerCase() === name.toLowerCase());
  if (matched && !model.value.some((tag) => tag.documentId === matched.documentId)) {
    addTag(matched);
    return;
  }
  if (!model.value.some((tag) => tag.name.toLowerCase() === name.toLowerCase())) {
    await createTagAndAdd(name);
  }
}

function handleCommitCurrent() {
  void commitPending();
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === "," || event.key === "Enter") {
    event.preventDefault();
    handleCommitCurrent();
  } else if (event.key === "Backspace" && query.value === "" && model.value.length > 0) {
    model.value = model.value.slice(0, -1);
  }
}

watch(
  trimmedQuery,
  (nextValue, _prev, onCleanup) => {
    if (!nextValue) {
      suggestions.value = [];
      open.value = false;
      return;
    }

    const timer = window.setTimeout(async () => {
      searching.value = true;
      try {
        const payload = await $fetch<{ data?: TagOption[] }>(`/api/tags-proxy?q=${encodeURIComponent(nextValue)}`, { cache: "no-store" });
        suggestions.value = (payload.data ?? []).filter((tag) => !model.value.some((item) => item.documentId === tag.documentId));
        open.value = true;
      } finally {
        searching.value = false;
      }
    }, 300);

    onCleanup(() => window.clearTimeout(timer));
  },
  { flush: "post" },
);

onMounted(() => {
  outsideHandler = (event: MouseEvent | TouchEvent) => {
    if (!(event.target instanceof Node)) return;
    if (!containerEl.value?.contains(event.target)) {
      open.value = false;
    }
  };
  document.addEventListener("mousedown", outsideHandler);
  document.addEventListener("touchstart", outsideHandler);
});

onBeforeUnmount(() => {
  if (outsideHandler) {
    document.removeEventListener("mousedown", outsideHandler);
    document.removeEventListener("touchstart", outsideHandler);
  }
});

defineExpose({ commitPending });
</script>
