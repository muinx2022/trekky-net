<template>
  <div class="space-y-4">
    <div v-if="!auth.isLoggedIn.value" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p class="text-sm text-slate-600">Ban can dang nhap de thao tac bai viet.</p>
      <button class="mt-3 rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700" @click="auth.openLoginModal()">Dang nhap</button>
    </div>

    <form v-else class="rounded-lg border border-gray-200 bg-white" @submit.prevent="submit">
      <p v-if="loadingPost" class="px-5 py-8 text-center text-sm text-gray-500">Dang tai bai viet...</p>
      <template v-else>
      <div class="space-y-1 p-5 pb-0">
        <label for="post-title" class="block text-sm font-medium text-gray-700">Tieu de</label>
        <input
          id="post-title"
          v-model="title"
          required
          class="w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div class="px-5 pt-4">
        <nav class="flex gap-1 rounded-lg bg-gray-100 p-1">
          <button type="button" class="flex-1 rounded-md px-4 py-1.5 text-sm font-semibold transition-all" :class="activeTab === 'content' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'" @click="activeTab = 'content'">
            Noi dung
          </button>
          <button type="button" class="flex-1 rounded-md px-4 py-1.5 text-sm font-semibold transition-all" :class="activeTab === 'images' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'" @click="activeTab = 'images'">
            {{ totalMediaCount > 0 ? `Media (${totalMediaCount})` : "Media" }}
          </button>
        </nav>
      </div>

      <div v-if="activeTab === 'content'" class="space-y-4 p-5">
        <fieldset class="space-y-1">
          <legend class="block text-sm font-medium text-gray-700">Danh muc</legend>
          <p v-if="loadingCategories" class="text-sm text-gray-500">Dang tai danh muc...</p>
          <div v-else class="relative" ref="categoryMenuEl">
            <button
              type="button"
              class="flex min-h-10 w-full items-center justify-between gap-2 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800"
              @click="categoryMenuOpen = !categoryMenuOpen"
            >
              <span class="flex flex-1 flex-wrap items-center gap-1 text-left">
                <span v-if="selectedCategoryItems.length === 0" class="text-gray-500">Chon danh muc</span>
                <span
                  v-for="item in selectedCategoryItems"
                  :key="item.value"
                  class="inline-flex items-center gap-1 rounded bg-gray-200 px-2 py-1 text-xs text-gray-800"
                >
                  {{ item.label }}
                  <span role="button" tabindex="0" class="inline-flex h-4 w-4 items-center justify-center rounded hover:bg-gray-300" @click.stop="selectedCategories = selectedCategories.filter((value) => value !== item.value)">x</span>
                </span>
              </span>
              <span class="text-xs text-gray-500">v</span>
            </button>

            <div v-if="categoryMenuOpen" class="absolute z-30 mt-1 max-h-64 w-full overflow-y-auto rounded-md border border-gray-200 bg-white p-1 shadow-md">
              <button
                v-for="option in categoryTreeOptions"
                :key="option.value"
                type="button"
                class="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm text-gray-700 hover:bg-gray-100"
                :style="{ paddingLeft: `${8 + option.depth * 16}px` }"
                @click="toggleCategory(option.value)"
              >
                <span>{{ option.label }}</span>
                <span v-if="selectedCategories.includes(option.value)" class="text-xs">✓</span>
              </button>
              <p v-if="categoryTreeOptions.length === 0" class="px-2 py-1.5 text-sm text-gray-500">Chua co danh muc</p>
            </div>
          </div>
        </fieldset>

        <fieldset class="space-y-1">
          <legend class="block text-sm font-medium text-gray-700">Tags</legend>
          <TagCombobox ref="tagComboboxRef" v-model="selectedTags" />
        </fieldset>

        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="block text-sm font-medium text-gray-700">Noi dung</label>
            <button type="button" class="text-xs font-medium text-gray-500 hover:text-gray-700 hover:underline" @click="showToolbar = !showToolbar">
              {{ showToolbar ? "An dinh dang" : "Hien thi dinh dang" }}
            </button>
          </div>
          <div class="rounded-md border border-gray-200 bg-gray-50 p-3">
            <TiptapEditor v-model="content" :show-toolbar="showToolbar" @media-picked="handleMediaPicked" @media-error="(value) => (error = value ?? '')" />
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'images'" class="space-y-4 p-5">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm text-gray-500">Anh >1280px tu dong thu nho. Anh toi da 5MB, video toi da 200MB.</p>
          <button type="button" class="rounded-md bg-gray-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-gray-600 disabled:opacity-60" :disabled="processingGallery" @click="openGalleryPicker">
            {{ processingGallery ? "Dang xu ly..." : "+ Them media" }}
          </button>
        </div>

        <input ref="fileInputEl" type="file" accept="image/*,video/*" multiple class="hidden" @change="handleFileSelect" />
        <input ref="cameraFileInputEl" type="file" accept="image/*" capture="environment" class="hidden" @change="handleFileSelect" />

        <button
          v-if="totalMediaCount === 0"
          type="button"
          class="flex w-full flex-col items-center gap-2 rounded-lg border-2 border-dashed border-gray-200 py-12 text-gray-400 transition-colors hover:border-gray-400 hover:text-gray-500"
          @click="openGalleryPicker"
        >
          <span class="text-3xl">+</span>
          <span class="text-sm">Chon anh hoac video de tai len</span>
        </button>
        <div v-else class="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
          <div v-for="item in visibleExistingMedia" :key="item.id" class="group relative aspect-square overflow-hidden rounded-lg border border-gray-200 bg-gray-100">
            <video v-if="item.mime?.startsWith('video/')" :src="resolveMediaUrl(item.url)" class="h-full w-full object-cover" />
            <img v-else :src="resolveMediaUrl(item.url)" :alt="item.alternativeText ?? ''" class="h-full w-full object-cover" />
            <button type="button" class="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-white opacity-0 transition-colors group-hover:opacity-100 hover:bg-red-500" @click="removedMediaIds.add(item.id)">
              x
            </button>
          </div>

          <div v-for="(file, index) in newMediaFiles" :key="`new-${index}`" class="group relative aspect-square overflow-hidden rounded-lg border border-gray-200 bg-gray-100">
            <video v-if="file.type.startsWith('video/')" :src="newMediaPreviews[index]" class="h-full w-full object-cover" />
            <img v-else :src="newMediaPreviews[index]" :alt="file.name" class="h-full w-full object-cover" />
            <button type="button" class="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-white opacity-0 transition-colors group-hover:opacity-100 hover:bg-red-500" @click="newMediaFiles = newMediaFiles.filter((_, itemIndex) => itemIndex !== index)">
              x
            </button>
          </div>

          <button type="button" class="aspect-square rounded-lg border-2 border-dashed border-gray-200 text-gray-400 transition-colors hover:border-gray-400 hover:text-gray-500" @click="openGalleryPicker">
            +
          </button>
        </div>
      </div>

      <div class="space-y-3 px-5 pb-5 pt-2">
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

        <div class="flex gap-2">
          <button type="button" class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="router.push('/my-posts')">
            Huy
          </button>
          <button type="submit" class="rounded-md bg-gray-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-600 disabled:opacity-60" :disabled="pending || uploadingMedia || processingMedia">
            {{ processingMedia ? "Dang xu ly video..." : uploadingMedia ? "Dang tai media..." : pending ? (mode === 'create' ? 'Dang tao...' : 'Dang luu...') : mode === 'create' ? 'Tao bai viet' : 'Luu thay doi' }}
          </button>
        </div>
      </div>
      </template>
    </form>
  </div>
</template>

<script setup lang="ts">
import type { TagOption } from "~~/shared/types";
import { nameContentFile, nameGalleryFile } from "~~/shared/media-naming";

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
type ExistingMedia = { id: number; url: string; mime?: string | null; alternativeText?: string | null };

const auth = useAuth();
const router = useRouter();
const title = ref(props.initialTitle ?? "");
const content = ref(props.initialContent ?? "<p></p>");
const activeTab = ref<"content" | "images">("content");
const showToolbar = ref(true);
const loadingPost = ref(props.mode === "edit" && !props.initialTitle);
const loadingCategories = ref(false);
const categories = ref<CategoryOption[]>([]);
const selectedCategories = ref<string[]>(props.initialCategories ?? []);
const selectedTags = ref<TagOption[]>(props.initialTags ?? []);
const existingMedia = ref<ExistingMedia[]>(props.initialImages ?? []);
const removedMediaIds = ref<Set<number>>(new Set());
const newMediaFiles = ref<File[]>([]);
const newMediaPreviews = ref<string[]>([]);
const uploadingMedia = ref(false);
const processingGallery = ref(false);
const processingMedia = ref(false);
const categoryMenuOpen = ref(false);
const categoryMenuEl = ref<HTMLElement | null>(null);
const fileInputEl = ref<HTMLInputElement | null>(null);
const cameraFileInputEl = ref<HTMLInputElement | null>(null);
const tagComboboxRef = ref<{ commitPending: () => Promise<void> } | null>(null);
const pendingMediaMap: Record<string, File | undefined> = {};
const pending = ref(false);
const error = ref("");
let categoryOutsideHandler: ((event: MouseEvent) => void) | null = null;

const MAX_WIDTH = 1280;
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const MAX_VIDEO_SIZE = 200 * 1024 * 1024;

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
const visibleExistingMedia = computed(() => existingMedia.value.filter((item) => !removedMediaIds.value.has(item.id)));
const totalMediaCount = computed(() => visibleExistingMedia.value.length + newMediaFiles.value.length);

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
watch(
  () => props.initialImages,
  (value) => {
    existingMedia.value = value ?? [];
  },
);

watch(
  newMediaFiles,
  (value, _oldValue, onCleanup) => {
    const urls = value.map((file) => URL.createObjectURL(file));
    newMediaPreviews.value = urls;
    onCleanup(() => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    });
  },
  { immediate: true },
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

function resolveMediaUrl(url: string) {
  return url.startsWith("http://") || url.startsWith("https://") ? url : `${useRuntimeConfig().public.apiUrl}${url}`;
}

function openGalleryPicker() {
  if (window.innerWidth >= 768) {
    fileInputEl.value?.click();
    return;
  }
  cameraFileInputEl.value?.click();
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

async function handleFileSelect(event: Event) {
  const input = event.currentTarget as HTMLInputElement;
  const allFiles = Array.from(input.files ?? []);
  if (fileInputEl.value) fileInputEl.value.value = "";
  if (cameraFileInputEl.value) cameraFileInputEl.value.value = "";

  const valid = allFiles.filter((file) => {
    if (file.type.startsWith("image/")) return file.size <= MAX_IMAGE_SIZE;
    if (file.type.startsWith("video/")) return file.size <= MAX_VIDEO_SIZE;
    return false;
  });
  if (valid.length === 0) return;

  processingGallery.value = true;
  try {
    const processed = await Promise.all(
      valid.map(async (file) => {
        const renamed = nameGalleryFile(file);
        return file.type.startsWith("image/") ? await resizeToMaxWidth(renamed, MAX_WIDTH) : renamed;
      }),
    );
    newMediaFiles.value = [...newMediaFiles.value, ...processed];
  } finally {
    processingGallery.value = false;
  }
}

async function submit() {
  await tagComboboxRef.value?.commitPending();
  pending.value = true;
  error.value = "";
  try {
    let newUploadedIds: number[] = [];
    if (newMediaFiles.value.length > 0) {
      uploadingMedia.value = true;
      const formData = new FormData();
      newMediaFiles.value.forEach((file) => formData.append("files", file, file.name));
      const uploadRes = await auth.authorizedFetch("/api/upload-proxy", { method: "POST", body: formData });
      if (!uploadRes.ok) throw new Error("Tai media len that bai");
      const uploadPayload = (await uploadRes.json().catch(() => [])) as Array<{ id?: number }>;
      newUploadedIds = uploadPayload.map((item) => item.id).filter((id): id is number => typeof id === "number");
      uploadingMedia.value = false;
    }

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
      if (!uploadRes.ok) throw new Error("Tai media len that bai");
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

    const imageIds = props.mode === "edit" ? [...visibleExistingMedia.value.map((item) => item.id), ...newUploadedIds] : newUploadedIds;

    const response = await auth.authorizedFetch("/api/my-posts-proxy", {
      method: props.mode === "create" ? "POST" : "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...(props.mode === "edit" ? { documentId: props.documentId } : {}),
        title: title.value,
        content: submittableContent,
        categories: selectedCategories.value,
        tags: selectedTags.value.map((tag) => tag.documentId),
        imageIds,
      }),
    });

    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body?.error || (props.mode === "create" ? "Tao bai viet that bai" : "Cap nhat bai viet that bai"));
    await router.push("/my-posts");
  } catch (err) {
    error.value = err instanceof Error ? err.message : props.mode === "create" ? "Tao bai viet that bai" : "Cap nhat bai viet that bai";
  } finally {
    pending.value = false;
    uploadingMedia.value = false;
    processingMedia.value = false;
    processingGallery.value = false;
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
