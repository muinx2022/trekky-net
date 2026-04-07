<template>
  <PostEditorForm
    mode="edit"
    :document-id="documentId"
    :initial-title="post?.title ?? ''"
    :initial-content="post?.content ?? '<p></p>'"
    :initial-categories="initialCategories"
    :initial-tags="initialTags"
    :initial-images="initialImages"
  />
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
