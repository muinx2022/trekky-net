<template>
  <div v-if="images.length" class="select-none overflow-hidden rounded-xl bg-gray-900">
    <div class="relative">
      <video
        v-if="images[index]?.mime?.startsWith('video/')"
        :src="current.src"
        class="max-h-[520px] w-full bg-gray-900 object-contain"
        controls
        playsinline
      />
      <button v-else type="button" class="block w-full cursor-zoom-in" aria-label="Mo anh lon" @click="lightboxIndex = index">
        <img :src="current.src" :alt="current.alt" class="max-h-[520px] w-full bg-gray-900 object-contain" draggable="false" />
      </button>

      <template v-if="images.length > 1">
        <button
          type="button"
          class="absolute left-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white transition-colors hover:bg-black/70"
          aria-label="Anh truoc"
          @click="index = (index - 1 + images.length) % images.length"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m15 18-6-6 6-6" /></svg>
        </button>
        <button
          type="button"
          class="absolute right-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white transition-colors hover:bg-black/70"
          aria-label="Anh tiep"
          @click="index = (index + 1) % images.length"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m9 18 6-6-6-6" /></svg>
        </button>
        <span class="absolute right-3 top-3 rounded-full bg-black/50 px-2.5 py-0.5 text-xs leading-5 text-white">{{ index + 1 }}/{{ images.length }}</span>
      </template>

      <button
        v-if="!images[index]?.mime?.startsWith('video/')"
        type="button"
        class="absolute bottom-3 right-3 flex h-8 w-8 items-center justify-center rounded-full bg-black/50 text-white transition-colors hover:bg-black/70"
        aria-label="Phong to"
        @click="lightboxIndex = index"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" /></svg>
      </button>
    </div>

    <div v-if="images.length > 1" class="flex gap-1.5 overflow-x-auto bg-gray-800 p-2">
      <button
        v-for="(image, imageIndex) in images"
        :key="image.id"
        type="button"
        class="h-12 w-16 shrink-0 overflow-hidden rounded border-2 transition-all"
        :class="imageIndex === index ? 'border-white opacity-100' : 'border-transparent opacity-50 hover:opacity-75'"
        @click="index = imageIndex"
      >
        <video v-if="image.mime?.startsWith('video/')" :src="image.url" class="h-full w-full object-cover" muted playsinline preload="metadata" />
        <img v-else :src="image.url" alt="" class="h-full w-full object-cover" draggable="false" />
      </button>
    </div>
  </div>

  <Lightbox
    v-if="lightboxIndex !== null"
    :images="lightboxImages"
    :index="lightboxIndex"
    @close="lightboxIndex = null"
    @navigate="(nextIndex) => (lightboxIndex = nextIndex)"
  />
</template>

<script setup lang="ts">
import type { Media } from "../../shared/types";

const props = defineProps<{
  images: Media[];
}>();

const index = ref(0);
const lightboxIndex = ref<number | null>(null);
const lightboxImages = computed(() => props.images.map((img) => ({ src: img.url, alt: img.alternativeText ?? "" })));
const current = computed(() => lightboxImages.value[index.value] ?? { src: "", alt: "" });
</script>
