<template>
  <div :data-drawer-open="drawer.drawerOpen.value ?? undefined">
    <SiteHeader />
    <LoginModal />

    <div class="mobile-left-drawer md:hidden" :class="{ 'pointer-events-auto': drawer.drawerOpen.value === 'left' }">
      <button type="button" class="mobile-left-overlay" :class="{ 'opacity-100': drawer.drawerOpen.value === 'left' }" aria-label="Đóng menu" @click="drawer.closeDrawer()" />
      <aside class="mobile-left-panel" :class="{ 'translate-x-0': drawer.drawerOpen.value === 'left' }">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-base font-semibold text-gray-800">Danh mục</h3>
          <button type="button" class="rounded-md p-2 text-gray-500 hover:bg-gray-100" aria-label="Đóng" @click="drawer.closeDrawer()">×</button>
        </div>
        <MobileDrawerAutoClose>
          <LeftSidebar :categories="categories" />
        </MobileDrawerAutoClose>
      </aside>
    </div>

    <MobileRightDrawer>
      <RightSidebar :categories="categories" :footer-pages="footerPages" :top-posts="topPosts" :top-tags="topTags" />
    </MobileRightDrawer>

    <div class="container mx-auto flex-1 px-4 py-6">
      <div class="grid grid-cols-1 gap-6 md:grid-cols-12">
        <main class="space-y-4 md:col-span-8">
          <slot />
        </main>

        <aside class="hidden md:col-span-4 md:block md:h-[calc(100vh-7.25rem)] md:self-start md:sticky md:top-20">
          <RightSidebar :categories="categories" :footer-pages="footerPages" :top-posts="topPosts" :top-tags="topTags" />
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Category, Post, StrapiPage, Tag } from "../../shared/types";

type CategoryPayload = {
  document_id: string;
  name: string;
  slug: string;
  description?: string;
  parent?: string | number | { document_id?: string; documentId?: string } | null;
};

const { data } = await useAsyncData("site-shell-data", async () => {
  const [categoriesPayload, footerPayload, sidebarPayload] = await Promise.all([
    $fetch<
      | CategoryPayload[]
      | { results?: CategoryPayload[] }
    >("/api/categories"),
    $fetch<StrapiPage[]>("/api/internal/footer-pages"),
    $fetch<{ topPosts?: Post[]; topTags?: Tag[] }>("/api/internal/sidebar-data"),
  ]);

  const categoryRows = Array.isArray(categoriesPayload) ? categoriesPayload : (categoriesPayload.results ?? []);

  const categories: Category[] = Array.from(
    new Map(
      categoryRows
        .map((item) => ({
          ...item,
          parentDocumentId: resolveParentDocumentId(item.parent),
        }))
        .filter((item) => !item.parentDocumentId)
        .filter((item) => item.document_id && item.name && item.slug)
        .map((item) => [
          item.document_id,
          {
            id: 0,
            documentId: item.document_id,
            name: item.name,
            slug: item.slug,
            description: item.description,
            parent: null,
          } satisfies Category,
        ]),
    ).values(),
  );

  return {
    categories,
    footerPages: footerPayload ?? [],
    topPosts: sidebarPayload.topPosts ?? [],
    topTags: (sidebarPayload.topTags ?? []).filter((tag) => tag.slug),
  };
});

const categories = computed(() => data.value?.categories ?? []);
const footerPages = computed(() => data.value?.footerPages ?? []);
const topPosts = computed(() => data.value?.topPosts ?? []);
const topTags = computed(() => data.value?.topTags ?? []);
const drawer = useDrawer();

function resolveParentDocumentId(parent: CategoryPayload["parent"]) {
  if (parent == null) return null;
  if (typeof parent === "string" || typeof parent === "number") return String(parent);
  return parent.document_id ?? parent.documentId ?? null;
}
</script>
