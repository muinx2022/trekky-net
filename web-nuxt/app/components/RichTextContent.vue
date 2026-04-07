<template>
  <div :class="className" v-html="safeHtml" />
</template>

<script setup lang="ts">
import { sanitizeCommentHtml, sanitizeRichHtml } from "../../shared/seo";

const props = withDefaults(
  defineProps<{
    html: string;
    className?: string;
    mode?: "default" | "comment";
  }>(),
  {
    className: "richtext-content leading-7 text-slate-700",
    mode: "default",
  },
);

const config = useRuntimeConfig();
const safeHtml = computed(() =>
  props.mode === "comment" ? sanitizeCommentHtml(props.html ?? "") : sanitizeRichHtml(props.html ?? "", config.public.apiUrl),
);
</script>
