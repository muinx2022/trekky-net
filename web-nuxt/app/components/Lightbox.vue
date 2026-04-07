<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[120] flex items-center justify-center bg-black/90 p-4" @click.self="emit('close')">
      <button type="button" class="absolute right-4 top-4 text-white" aria-label="Đóng" @click="emit('close')">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6 6 18" />
          <path d="m6 6 12 12" />
        </svg>
      </button>

      <button
        v-if="images.length > 1"
        type="button"
        class="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white/10 p-3 text-white hover:bg-white/20"
        aria-label="Ảnh trước"
        @click="navigate(-1)"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="m15 18-6-6 6-6" />
        </svg>
      </button>

      <img :src="current.src" :alt="current.alt ?? ''" class="max-h-[88vh] max-w-[88vw] object-contain" />

      <button
        v-if="images.length > 1"
        type="button"
        class="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-white/10 p-3 text-white hover:bg-white/20"
        aria-label="Ảnh tiếp"
        @click="navigate(1)"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="m9 18 6-6-6-6" />
        </svg>
      </button>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  images: Array<{ src: string; alt?: string }>;
  index: number;
}>();

const emit = defineEmits<{
  close: [];
  navigate: [index: number];
}>();

const current = computed(() => props.images[props.index] ?? props.images[0]);
let keydownHandler: ((event: KeyboardEvent) => void) | null = null;

function navigate(delta: number) {
  const next = (props.index + delta + props.images.length) % props.images.length;
  emit("navigate", next);
}

onMounted(() => {
  keydownHandler = (event: KeyboardEvent) => {
    if (event.key === "Escape") emit("close");
    if (event.key === "ArrowLeft") navigate(-1);
    if (event.key === "ArrowRight") navigate(1);
  };
  document.addEventListener("keydown", keydownHandler);
});

onBeforeUnmount(() => {
  if (keydownHandler) document.removeEventListener("keydown", keydownHandler);
});
</script>
