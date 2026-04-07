<template>
  <div class="space-y-4">
    <div v-if="!auth.isLoggedIn.value" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p class="text-sm text-slate-600">Bạn cần đăng nhập để xem bài viết của mình.</p>
      <button class="mt-3 rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700" @click="auth.openLoginModal()">Đăng nhập</button>
    </div>

    <div v-else-if="pending" class="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm">
      Đang tải bài viết...
    </div>

    <div v-else-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
      {{ errorMessage }}
    </div>

    <div v-else class="space-y-3">
      <article v-for="post in posts" :key="post.documentId" class="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div v-if="post.categories?.length" class="mb-2 flex flex-wrap gap-1.5">
              <span v-for="category in post.categories.slice(0, 3)" :key="category.documentId" class="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                {{ category.name }}
              </span>
              <span v-if="(post.categories?.length ?? 0) > 3" class="rounded-full bg-zinc-200 px-2.5 py-0.5 text-xs font-medium text-zinc-700">
                +{{ (post.categories?.length ?? 0) - 3 }}
              </span>
            </div>
            <NuxtLink :to="`/p/${post.slug}--${post.documentId}`" class="text-lg font-medium text-slate-900 hover:text-sky-700">
              {{ post.title }}
            </NuxtLink>
            <div class="mt-3 flex flex-wrap items-center gap-2">
              <span
                class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium"
                :class="post.status === 'published' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'"
              >
                <span class="h-1.5 w-1.5 rounded-full" :class="post.status === 'published' ? 'bg-emerald-500' : 'bg-amber-500'" />
                {{ post.status === "published" ? "Đã xuất bản" : "Bản nháp" }}
              </span>

              <NuxtLink
                v-for="tag in post.tags ?? []"
                :key="tag.documentId"
                :to="`/t/${tag.slug}`"
                class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-500 transition-colors hover:bg-gray-200 hover:text-gray-700"
              >
                #{{ tag.name }}
              </NuxtLink>
            </div>
          </div>
          <div class="flex gap-2">
            <NuxtLink :to="`/my-posts/${post.documentId}/edit`" class="rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">Sửa</NuxtLink>
            <button class="rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50" @click="toggleStatus(post)">
              {{ post.status === 'published' ? 'Bỏ đăng' : 'Đăng bài' }}
            </button>
          </div>
        </div>
      </article>

      <div v-if="posts.length === 0" class="rounded-2xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500">
        Bạn chưa có bài viết nào.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Post } from "../../shared/types";

const auth = useAuth();
const posts = ref<Post[]>([]);
const pending = ref(false);
const errorMessage = ref("");

async function loadPosts() {
  if (!auth.isLoggedIn.value) return;
  pending.value = true;
  errorMessage.value = "";
  const response = await auth.authorizedFetch("/api/my-posts-proxy");
  pending.value = false;
  if (!response.ok) {
    errorMessage.value = "Không thể tải danh sách bài viết.";
    return;
  }
  const payload = await response.json().catch(() => ({}));
  posts.value = payload?.data ?? [];
}

async function toggleStatus(post: Post) {
  const response = await auth.authorizedFetch("/api/my-posts-proxy", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      documentId: post.documentId,
      action: post.status === "published" ? "unpublish" : "publish",
      currentStatus: post.status,
    }),
  });
  if (response.ok) await loadPosts();
}

watch(
  () => [auth.isLoggedIn.value, auth.isHydrated.value],
  (value) => {
    if (value[0]) void loadPosts();
  },
  { immediate: true },
);
</script>
