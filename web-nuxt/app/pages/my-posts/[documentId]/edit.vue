<template>
  <section class="space-y-5">
    <div class="overflow-hidden rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#e0f2fe_45%,#fff7ed_100%)] shadow-sm dark:border-slate-700 dark:bg-[linear-gradient(135deg,#0f172a_0%,#0b253a_45%,#172033_100%)]">
      <div class="px-6 py-8 sm:px-8 lg:px-10">
        <span class="inline-flex w-fit items-center rounded-full border border-white/70 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700 shadow-sm backdrop-blur dark:border-slate-500/60 dark:bg-slate-900/60 dark:text-sky-200">
          Chỉnh sửa bài viết
        </span>
        <div class="mt-3 space-y-2">
          <h1 class="text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl">Hoàn thiện bài viết của bạn</h1>
          <p class="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
            Cập nhật nội dung, danh mục và media trước khi đăng lại hoặc lưu bản nháp.
          </p>
        </div>
      </div>
    </div>

    <PostEditorForm
      mode="edit"
      :document-id="documentId"
      :initial-title="post?.title ?? ''"
      :initial-content="post?.content ?? '<p></p>'"
      :initial-categories="initialCategories"
      :initial-tags="initialTags"
      :initial-images="initialImages"
    />
  </section>
</template>

<script setup lang="ts">
const route = useRoute();
const documentId = route.params.documentId as string;
const auth = useAuth();
const post = ref<Record<string, any> | null>(null);

if (import.meta.client) {
  watchEffect(async () => {
    if (!auth.isLoggedIn.value) return;
    const response = await auth.authorizedFetch(`/api/my-posts-proxy?documentId=${encodeURIComponent(documentId)}`);
    if (!response.ok) return;
    const payload = await response.json().catch(() => ({}));
    post.value = payload?.data ?? null;
  });
}

const initialCategories = computed(() => (post.value?.categories ?? []).map((item: { documentId?: string }) => item.documentId).filter(Boolean));
const initialTags = computed(() => (post.value?.tags ?? []).map((item: { documentId?: string; name?: string; slug?: string }) => ({ documentId: item.documentId ?? "", name: item.name ?? "", slug: item.slug })));
const initialImages = computed(() => (post.value?.images ?? []).map((item: { id?: number; url?: string; mime?: string | null; alternativeText?: string | null }) => ({ id: item.id ?? 0, url: item.url ?? "", mime: item.mime ?? null, alternativeText: item.alternativeText ?? null })));
</script>
