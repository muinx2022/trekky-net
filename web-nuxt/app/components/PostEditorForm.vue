<template>
  <div class="space-y-4">
    <div v-if="!auth.isLoggedIn.value" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <p class="text-sm text-slate-600 dark:text-slate-300">Bạn cần đăng nhập để thao tác bài viết.</p>
      <button class="mt-3 rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700" @click="auth.openLoginModal()">Đăng nhập</button>
    </div>

    <form v-else class="overflow-hidden rounded-[1.75rem] border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900" @submit.prevent="submit">
      <p v-if="loadingPost" class="px-5 py-8 text-center text-sm text-gray-500 dark:text-slate-400">Đang tải bài viết...</p>
      <template v-else>
      <div class="border-b border-slate-200 bg-slate-50/80 px-5 py-5 dark:border-slate-700 dark:bg-slate-800/80 sm:px-6">
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 dark:text-sky-300">{{ mode === 'create' ? 'Bản nháp mới' : 'Cập nhật bài viết' }}</p>
          <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-50">{{ mode === 'create' ? 'Thông tin bài viết' : 'Chỉnh sửa bài viết' }}</h2>
          <p class="text-sm text-slate-600 dark:text-slate-300">Nhập tiêu đề, nội dung và danh mục của bài viết. Ảnh sẽ được chèn trực tiếp trong nội dung.</p>
        </div>
      </div>

      <div class="space-y-5 p-5 sm:p-6">
        <fieldset class="space-y-1">
          <div class="flex items-center justify-between gap-3">
            <legend class="block text-sm font-semibold uppercase tracking-[0.18em] text-sky-700 dark:text-sky-300">Danh mục</legend>
            <span class="rounded-full bg-sky-100 px-2.5 py-1 text-[11px] font-semibold text-sky-700 dark:bg-sky-500/15 dark:text-sky-200">Chọn ít nhất 1</span>
          </div>
          <p v-if="loadingCategories" class="text-sm text-gray-500">Đang tải danh mục...</p>
          <div v-else class="relative" ref="categoryMenuEl">
            <button
              type="button"
              class="flex min-h-14 w-full items-center justify-between gap-3 rounded-3xl border px-4 py-3 text-sm text-gray-800 shadow-sm transition dark:text-slate-100"
              :class="fieldErrors.categories ? 'border-red-300 bg-red-50/80 dark:border-red-500/70 dark:bg-red-500/10' : 'border-sky-200 bg-gradient-to-r from-sky-50 via-white to-slate-50 hover:border-sky-300 dark:border-slate-600 dark:from-slate-800 dark:via-slate-900 dark:to-slate-800 dark:hover:border-sky-500/60'"
              @click="categoryMenuOpen = !categoryMenuOpen"
            >
              <span class="flex flex-1 flex-wrap items-center gap-1 text-left">
                <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-sky-600 text-base font-bold text-white shadow-sm dark:bg-sky-500">c/</span>
                <span v-if="selectedCategoryItems.length === 0" class="text-sm font-medium text-gray-500 dark:text-slate-400">Chọn chuyên mục cho bài viết</span>
                <span
                  v-for="item in selectedCategoryItems"
                  :key="item.value"
                  class="inline-flex items-center gap-1 rounded-full bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm dark:bg-sky-500"
                >
                  c/{{ item.label }}
                  <span role="button" tabindex="0" class="inline-flex h-4 w-4 items-center justify-center rounded-full bg-white/20 hover:bg-white/30" @click.stop="selectedCategories = selectedCategories.filter((value) => value !== item.value)">x</span>
                </span>
              </span>
              <span class="rounded-full bg-white/80 px-2 py-1 text-xs font-semibold text-sky-700 shadow-sm dark:bg-slate-700 dark:text-sky-200">{{ categoryMenuOpen ? "Ẩn" : "Chọn" }}</span>
            </button>

            <div v-if="categoryMenuOpen" class="absolute z-30 mt-2 max-h-72 w-full overflow-y-auto rounded-3xl border border-sky-200 bg-white p-2 shadow-xl shadow-sky-100/60 dark:border-slate-600 dark:bg-slate-900 dark:shadow-black/30">
              <button
                v-for="option in categoryTreeOptions"
                :key="option.value"
                type="button"
                class="flex w-full items-center justify-between rounded-2xl px-3 py-2 text-left text-sm transition"
                :class="selectedCategories.includes(option.value) ? 'bg-sky-600 text-white shadow-sm dark:bg-sky-500' : 'text-gray-700 hover:bg-sky-50 dark:text-slate-200 dark:hover:bg-slate-800'"
                :style="{ paddingLeft: `${12 + option.depth * 18}px` }"
                @click="toggleCategory(option.value)"
              >
                <span class="font-medium">{{ option.depth > 0 ? `↳ ${option.label}` : `c/${option.label}` }}</span>
                <span v-if="selectedCategories.includes(option.value)" class="text-xs font-semibold">✓</span>
              </button>
              <p v-if="categoryTreeOptions.length === 0" class="px-3 py-2 text-sm text-gray-500 dark:text-slate-400">Chưa có danh mục</p>
            </div>
          </div>
          <p v-if="fieldErrors.categories" class="text-xs text-red-600">{{ fieldErrors.categories }}</p>
        </fieldset>

        <div class="space-y-1">
          <label for="post-title" class="block text-sm font-medium text-gray-700">Tiêu đề bài viết</label>
          <input
            id="post-title"
            v-model="title"
            maxlength="120"
            :aria-invalid="fieldErrors.title ? 'true' : 'false'"
            class="w-full rounded-2xl border px-4 py-3 text-sm text-gray-800 transition focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
            :class="fieldErrors.title ? 'border-red-300 bg-red-50/70' : 'border-gray-200 bg-gray-50'"
          />
          <div class="flex items-start justify-between gap-3 text-xs">
            <p :class="fieldErrors.title ? 'text-red-600' : 'text-gray-500'">
              {{ fieldErrors.title || 'Nên rõ chủ đề, địa điểm hoặc trải nghiệm chính của bài viết.' }}
            </p>
            <span class="shrink-0 text-gray-400">{{ title.trim().length }}/120</span>
          </div>
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="block text-sm font-medium text-gray-700">Nội dung</label>
            <button type="button" class="text-xs font-medium text-gray-500 hover:text-gray-700 hover:underline" @click="showToolbar = !showToolbar">
              {{ showToolbar ? "Ẩn định dạng" : "Hiển thị định dạng" }}
            </button>
          </div>
          <div class="space-y-2">
            <TiptapEditor v-model="content" :show-toolbar="showToolbar" @media-picked="handleMediaPicked" @media-error="(value) => (error = value ?? '')" />
          </div>
          <div class="flex items-start justify-between gap-3 text-xs">
            <p v-if="fieldErrors.content" class="text-red-600">
              {{ fieldErrors.content }}
            </p>
            <span v-else />
            <span class="shrink-0 text-gray-400">{{ contentCharacterCount }} ký tự</span>
          </div>
        </div>

        <fieldset class="space-y-1">
          <legend class="block text-sm font-medium text-gray-700">Tags</legend>
          <TagCombobox ref="tagComboboxRef" v-model="selectedTags" />
        </fieldset>
      </div>

      <div class="space-y-3 border-t border-slate-200 bg-slate-50/70 px-5 pb-5 pt-4 dark:border-slate-700 dark:bg-slate-800/70 sm:px-6">
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

        <div class="flex gap-2">
          <button type="button" class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700/70" @click="router.push('/my-posts')">
            Hủy
          </button>
          <button type="submit" class="rounded-md bg-gray-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-600 disabled:opacity-60 dark:bg-sky-500 dark:text-slate-950 dark:hover:bg-sky-400" :disabled="pending || uploadingMedia || processingMedia">
            {{ processingMedia ? "Đang xử lý video..." : uploadingMedia ? "Đang tải ảnh trong nội dung..." : pending ? (mode === 'create' ? 'Đang tạo...' : 'Đang lưu...') : mode === 'create' ? 'Tạo bài viết' : 'Lưu thay đổi' }}
          </button>
        </div>
      </div>
      </template>
    </form>
  </div>
</template>

<script setup lang="ts">
import type { TagOption } from "~~/shared/types";
import { nameContentFile } from "~~/shared/media-naming";

const props = defineProps<{
  mode: "create" | "edit";
  documentId?: string;
  initialTitle?: string;
  initialContent?: string;
  initialCategories?: string[];
  initialTags?: TagOption[];
  initialImages?: Array<{ id: number; url: string; mime?: string | null; alternativeText?: string | null }>;
}>();

type CategoryOption = { id?: number; document_id: string; name: string; sort_order?: number; parent?: number | string | null };

const auth = useAuth();
const router = useRouter();
const title = ref(props.initialTitle ?? "");
const content = ref(props.initialContent ?? "<p></p>");
const showToolbar = ref(true);
const loadingPost = ref(props.mode === "edit" && !props.initialTitle);
const loadingCategories = ref(false);
const categories = ref<CategoryOption[]>([]);
const selectedCategories = ref<string[]>(props.initialCategories ?? []);
const selectedTags = ref<TagOption[]>(props.initialTags ?? []);
const uploadingMedia = ref(false);
const processingMedia = ref(false);
const categoryMenuOpen = ref(false);
const categoryMenuEl = ref<HTMLElement | null>(null);
const tagComboboxRef = ref<{ commitPending: () => Promise<void> } | null>(null);
const pendingMediaMap: Record<string, File | undefined> = {};
const pending = ref(false);
const error = ref("");
const fieldErrors = ref<{ title?: string; categories?: string; content?: string }>({});
let categoryOutsideHandler: ((event: MouseEvent) => void) | null = null;

const MAX_WIDTH = 1280;
const MIN_TITLE_LENGTH = 8;
const MAX_TITLE_LENGTH = 120;
const MIN_CONTENT_LENGTH = 30;

const categoryTreeOptions = computed(() => {
  const byParent: Record<string, CategoryOption[]> = {};
  const rootKey = "__root__";
  categories.value.forEach((item) => {
    const key = item.parent != null ? String(item.parent) : rootKey;
    byParent[key] ??= [];
    byParent[key].push(item);
  });
  Object.values(byParent).forEach((bucket) => bucket.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0)));
  const flattened: Array<{ value: string; label: string; depth: number }> = [];
  const visit = (parentId: string | null, depth: number) => {
    const key = parentId ?? rootKey;
    (byParent[key] ?? []).forEach((node) => {
      flattened.push({ value: node.document_id, label: node.name, depth });
      visit(node.document_id, depth + 1);
    });
  };
  visit(null, 0);
  return flattened;
});

const selectedCategoryItems = computed(() => categoryTreeOptions.value.filter((item) => selectedCategories.value.includes(item.value)));
const contentPlainText = computed(() => content.value.replace(/<[^>]*>/g, " ").replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim());
const contentCharacterCount = computed(() => contentPlainText.value.length);

watch(title, () => {
  if (fieldErrors.value.title) validateField("title");
});
watch(selectedCategories, () => {
  if (fieldErrors.value.categories) validateField("categories");
});
watch(contentPlainText, () => {
  if (fieldErrors.value.content) validateField("content");
});

watch(
  () => props.initialTitle,
  (value) => {
    if (typeof value === "string") {
      title.value = value;
      loadingPost.value = false;
    }
  },
);
watch(
  () => props.initialContent,
  (value) => {
    if (typeof value === "string") content.value = value;
  },
);
watch(
  () => props.initialCategories,
  (value) => {
    selectedCategories.value = value ?? [];
  },
);
watch(
  () => props.initialTags,
  (value) => {
    selectedTags.value = value ?? [];
  },
);
async function loadCategories() {
  loadingCategories.value = true;
  try {
    const payload = await $fetch<{ results?: CategoryOption[] } | CategoryOption[]>("/api/categories", { cache: "no-store" });
    categories.value = Array.isArray(payload) ? payload : payload.results ?? [];
  } finally {
    loadingCategories.value = false;
  }
}

function toggleCategory(documentId: string) {
  if (selectedCategories.value.includes(documentId)) {
    selectedCategories.value = selectedCategories.value.filter((item) => item !== documentId);
    categoryMenuOpen.value = false;
    return;
  }
  selectedCategories.value = [...selectedCategories.value, documentId];
  categoryMenuOpen.value = false;
}

function handleMediaPicked(blobUrl: string, file: File) {
  pendingMediaMap[blobUrl] = file;
}

async function resizeToMaxWidth(file: File, maxWidth: number): Promise<File> {
  return await new Promise((resolve) => {
    const image = new Image();
    const objectUrl = URL.createObjectURL(file);
    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      const needsResize = image.naturalWidth > maxWidth;
      const width = needsResize ? maxWidth : image.naturalWidth;
      const height = needsResize ? Math.round(image.naturalHeight * (maxWidth / image.naturalWidth)) : image.naturalHeight;
      const outputType = file.type === "image/png" ? "image/png" : "image/jpeg";
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) {
        resolve(file);
        return;
      }
      context.drawImage(image, 0, 0, width, height);
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            resolve(file);
            return;
          }
          if (blob.size >= file.size && !needsResize) {
            resolve(file);
            return;
          }
          resolve(new File([blob], file.name.replace(/\.[^.]+$/, outputType === "image/jpeg" ? ".jpg" : ".png"), { type: outputType }));
        },
        outputType,
        outputType === "image/jpeg" ? 0.85 : undefined,
      );
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(file);
    };
    image.src = objectUrl;
  });
}

function getTitleError() {
  const trimmed = title.value.trim();
  if (!trimmed) return "Vui lòng nhập tiêu đề bài viết.";
  if (trimmed.length < MIN_TITLE_LENGTH) return `Tiêu đề cần ít nhất ${MIN_TITLE_LENGTH} ký tự.`;
  if (trimmed.length > MAX_TITLE_LENGTH) return `Tiêu đề không được vượt quá ${MAX_TITLE_LENGTH} ký tự.`;
  return "";
}

function getCategoriesError() {
  if (selectedCategories.value.length === 0) return "Hãy chọn ít nhất một danh mục.";
  return "";
}

function getContentError() {
  if (!contentPlainText.value) return "Vui lòng nhập nội dung bài viết.";
  if (contentCharacterCount.value < MIN_CONTENT_LENGTH) return `Nội dung cần ít nhất ${MIN_CONTENT_LENGTH} ký tự.`;
  return "";
}

function validateField(field: "title" | "categories" | "content") {
  const nextErrors = { ...fieldErrors.value };
  if (field === "title") nextErrors.title = getTitleError() || undefined;
  if (field === "categories") nextErrors.categories = getCategoriesError() || undefined;
  if (field === "content") nextErrors.content = getContentError() || undefined;
  fieldErrors.value = nextErrors;
}

function validateForm() {
  fieldErrors.value = {
    title: getTitleError() || undefined,
    categories: getCategoriesError() || undefined,
    content: getContentError() || undefined,
  };
  return !fieldErrors.value.title && !fieldErrors.value.categories && !fieldErrors.value.content;
}

async function submit() {
  await tagComboboxRef.value?.commitPending();
  if (!validateForm()) {
    error.value = "Vui lòng sửa các trường được đánh dấu trước khi lưu bài viết.";
    return;
  }
  pending.value = true;
  error.value = "";
  try {
    let submittableContent = content.value;
    const blobMatches = [...new Set([...submittableContent.matchAll(/blob:[^"'\s)>]+/g)].map((match) => match[0]))];
    const mediaEntries = blobMatches.map((url) => [url, pendingMediaMap[url]] as [string, File | undefined]).filter((entry): entry is [string, File] => !!entry[1]);
    if (mediaEntries.length > 0) {
      uploadingMedia.value = true;
      const formData = new FormData();
      for (const [, file] of mediaEntries) {
        const processed = file.type.startsWith("image/") ? await resizeToMaxWidth(file, MAX_WIDTH) : file;
        const named = nameContentFile(processed);
        formData.append("files", named, named.name);
      }
      const uploadRes = await auth.authorizedFetch("/api/upload-proxy", { method: "POST", body: formData });
      if (!uploadRes.ok) throw new Error("Tải media lên thất bại");
      const uploadPayload = (await uploadRes.json().catch(() => [])) as Array<{ url?: string }>;
      for (let index = 0; index < mediaEntries.length; index += 1) {
        const [blobUrl] = mediaEntries[index];
        const url = uploadPayload[index]?.url;
        if (!url) continue;
        const fullUrl = url.startsWith("http") ? url : `${useRuntimeConfig().public.apiUrl}${url}`;
        submittableContent = submittableContent.replaceAll(blobUrl, fullUrl);
        delete pendingMediaMap[blobUrl];
      }
      uploadingMedia.value = false;
    }

    const response = await auth.authorizedFetch("/api/my-posts-proxy", {
      method: props.mode === "create" ? "POST" : "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...(props.mode === "edit" ? { documentId: props.documentId } : {}),
        title: title.value.trim(),
        content: submittableContent,
        categories: selectedCategories.value,
        tags: selectedTags.value.map((tag) => tag.documentId),
      }),
    });

    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body?.error || (props.mode === "create" ? "Tạo bài viết thất bại" : "Cập nhật bài viết thất bại"));
    await router.push("/my-posts");
  } catch (err) {
    error.value = err instanceof Error ? err.message : props.mode === "create" ? "Tạo bài viết thất bại" : "Cập nhật bài viết thất bại";
  } finally {
    pending.value = false;
    uploadingMedia.value = false;
    processingMedia.value = false;
  }
}

onMounted(() => {
  void loadCategories();
  categoryOutsideHandler = (event: MouseEvent) => {
    if (event.target instanceof Element && !categoryMenuEl.value?.contains(event.target)) {
      categoryMenuOpen.value = false;
    }
  };
  document.addEventListener("mousedown", categoryOutsideHandler);
});

onBeforeUnmount(() => {
  if (categoryOutsideHandler) document.removeEventListener("mousedown", categoryOutsideHandler);
});
</script>
