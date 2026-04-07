<template>
  <div ref="containerRef">
    <RichTextContent :html="html" :class-name="className" />
  </div>
  <Lightbox
    v-if="lightbox"
    :images="lightbox.images"
    :index="lightbox.index"
    @close="lightbox = null"
    @navigate="(index) => lightbox && (lightbox = { ...lightbox, index })"
  />
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    html: string;
    className?: string;
  }>(),
  {
    className: "richtext-content",
  },
);

const containerRef = ref<HTMLElement | null>(null);
const lightbox = ref<{ images: Array<{ src: string; alt?: string }>; index: number } | null>(null);

watch(
  () => props.html,
  async () => {
    await nextTick();
    const root = containerRef.value;
    if (!root) return;
    const imgs = Array.from(root.querySelectorAll("img"));
    const images = imgs.map((img) => ({ src: img.src, alt: img.alt || undefined }));
    imgs.forEach((img, index) => {
      img.style.cursor = "zoom-in";
      img.onclick = () => {
        lightbox.value = { images, index };
      };
    });
  },
  { immediate: true },
);
</script>
