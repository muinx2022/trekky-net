<template>
  <div class="mobile-right-drawer md:hidden" :class="{ 'pointer-events-auto': drawer.drawerOpen.value === 'right' }">
    <button
      type="button"
      class="mobile-right-overlay"
      :class="{ 'opacity-100': drawer.drawerOpen.value === 'right' }"
      aria-label="Đóng menu"
      @click="drawer.closeDrawer()"
    />
    <aside class="mobile-right-panel" :class="{ 'translate-x-0': drawer.drawerOpen.value === 'right' }">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-base font-semibold text-gray-800">Khám phá</h3>
        <button
          type="button"
          class="rounded-md p-2 text-gray-500 hover:bg-gray-100"
          aria-label="Đóng"
          @click="drawer.closeDrawer()"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6 6 18" />
            <path d="m6 6 12 12" />
          </svg>
        </button>
      </div>
      <MobileDrawerAutoClose>
        <slot />
      </MobileDrawerAutoClose>
    </aside>
  </div>
</template>

<script setup lang="ts">
const drawer = useDrawer();
</script>
