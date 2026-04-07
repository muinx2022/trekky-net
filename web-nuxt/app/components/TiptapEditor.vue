<template>
  <div :class="containerClass" class="tiptap-editor-container">
    <div v-if="showToolbar" :class="toolbarClass" class="tiptap-editor-toolbar">
      <div class="flex flex-wrap items-center gap-1">
        <button type="button" :class="buttonClass(editor?.isActive('bold'))" @click="editor?.chain().focus().toggleBold().run()">B</button>
        <button type="button" :class="buttonClass(editor?.isActive('italic'))" @click="editor?.chain().focus().toggleItalic().run()">I</button>
        <button type="button" :class="buttonClass(editor?.isActive('heading', { level: 2 }))" @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()">H2</button>
        <button type="button" :class="buttonClass(editor?.isActive('bulletList'))" @click="editor?.chain().focus().toggleBulletList().run()">•</button>
        <button type="button" :class="buttonClass(editor?.isActive('orderedList'))" @click="editor?.chain().focus().toggleOrderedList().run()">1.</button>
        <button type="button" :class="buttonClass(editor?.isActive('blockquote'))" @click="editor?.chain().focus().toggleBlockquote().run()">"</button>

        <template v-if="allowMedia">
          <span class="mx-0.5 h-5 w-px bg-zinc-200" />
          <button type="button" :class="buttonClass(false)" @click="openImageChooser">Anh</button>
          <button type="button" :class="buttonClass(false)" @click="videoInputEl?.click()">Video</button>
          <button type="button" :class="buttonClass(youtubeOpen)" @click="youtubeOpen = !youtubeOpen">YouTube</button>
        </template>
      </div>

      <div v-if="allowMedia && youtubeOpen" class="flex items-center gap-1.5">
        <input
          v-model="youtubeUrl"
          type="url"
          :class="youtubeInputClass"
          placeholder="https://youtube.com/watch?v=..."
          @keydown.enter.prevent="handleYoutubeInsert"
          @keydown.esc="youtubeOpen = false; youtubeUrl = ''"
        />
        <button type="button" class="rounded bg-gray-500 px-2.5 py-1 text-xs font-medium text-white transition-colors hover:bg-gray-600" @click="handleYoutubeInsert">
          Chen
        </button>
        <button type="button" class="rounded px-2 py-1 text-xs text-zinc-500 transition-colors hover:bg-zinc-100" @click="youtubeOpen = false; youtubeUrl = ''">
          Huy
        </button>
      </div>
    </div>

    <div :class="editorViewportClass" class="tiptap-editor-viewport">
      <EditorContent v-if="editor" :editor="editor" :class="editorClass" />
    </div>

    <div v-if="allowMedia && imageModalOpen" class="fixed inset-0 z-[100] md:hidden">
      <button type="button" class="absolute inset-0 bg-black/45" aria-label="Dong" @click="imageModalOpen = false" />
      <div class="absolute inset-x-0 bottom-0 rounded-t-2xl bg-white p-4 shadow-2xl">
        <div class="mb-3 flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-zinc-900">Chen anh</p>
            <p class="text-xs text-zinc-500">Chon cach them anh vao noi dung</p>
          </div>
          <button type="button" class="inline-flex h-9 w-9 items-center justify-center rounded-full text-zinc-500 hover:bg-zinc-100" aria-label="Dong" @click="imageModalOpen = false">×</button>
        </div>

        <div class="grid gap-3">
          <button type="button" class="flex w-full items-center gap-3 rounded-xl border border-zinc-200 px-4 py-4 text-left hover:bg-zinc-50" @click="imageModalOpen = false; imageInputEl?.click()">
            <span class="inline-flex h-11 w-11 items-center justify-center rounded-full bg-zinc-100 text-zinc-700">Ả</span>
            <span>
              <span class="block text-sm font-medium text-zinc-900">Chon tu thu vien</span>
              <span class="block text-xs text-zinc-500">Mo anh co san tren thiet bi</span>
            </span>
          </button>

          <button type="button" class="flex w-full items-center gap-3 rounded-xl border border-zinc-200 px-4 py-4 text-left hover:bg-zinc-50" @click="imageModalOpen = false; cameraInputEl?.click()">
            <span class="inline-flex h-11 w-11 items-center justify-center rounded-full bg-zinc-100 text-zinc-700">📷</span>
            <span>
              <span class="block text-sm font-medium text-zinc-900">Dung may anh</span>
              <span class="block text-xs text-zinc-500">Chup anh moi roi chen vao bai</span>
            </span>
          </button>
        </div>
      </div>
    </div>

    <input ref="imageInputEl" type="file" accept="image/*" class="hidden" @change="handleImagePick" />
    <input ref="cameraInputEl" type="file" accept="image/*" capture="environment" class="hidden" @change="handleImagePick" />
    <input ref="videoInputEl" type="file" accept="video/*" class="hidden" @change="handleVideoPick" />
  </div>
</template>

<script setup lang="ts">
import { Node, mergeAttributes } from "@tiptap/core";
import Image from "@tiptap/extension-image";
import Youtube from "@tiptap/extension-youtube";
import StarterKit from "@tiptap/starter-kit";
import { EditorContent, useEditor } from "@tiptap/vue-3";
import { nameContentFile } from "~~/shared/media-naming";

const MAX_INLINE_IMAGE_SIZE = 5 * 1024 * 1024;
const MAX_INLINE_VIDEO_SIZE = 200 * 1024 * 1024;

const props = withDefaults(
  defineProps<{
    showToolbar?: boolean;
    compact?: boolean;
    allowMedia?: boolean;
    editable?: boolean;
    theme?: "default" | "comment-dark";
  }>(),
  {
    showToolbar: true,
    compact: false,
    allowMedia: true,
    editable: true,
    theme: "default",
  },
);

const model = defineModel<string>({ default: "<p></p>" });
const emit = defineEmits<{
  mediaPicked: [blobUrl: string, file: File];
  mediaError: [message: string | null];
}>();

const imageInputEl = ref<HTMLInputElement | null>(null);
const cameraInputEl = ref<HTMLInputElement | null>(null);
const videoInputEl = ref<HTMLInputElement | null>(null);
const youtubeOpen = ref(false);
const youtubeUrl = ref("");
const imageModalOpen = ref(false);
const isCommentDark = computed(() => props.theme === "comment-dark");

const VideoNode = Node.create({
  name: "customVideo",
  group: "block",
  atom: true,
  draggable: true,
  addAttributes() {
    return { src: { default: null } };
  },
  parseHTML() {
    return [{ tag: "video[src]" }];
  },
  renderHTML({ HTMLAttributes }) {
    return ["video", mergeAttributes({ controls: true, style: "max-width:100%;border-radius:6px;display:block" }, HTMLAttributes)];
  },
});

const editor = useEditor({
  editable: props.editable,
  content: model.value || "<p></p>",
  extensions: [
    StarterKit.configure({ heading: { levels: [2, 3] } }),
    Image.configure({ inline: false, allowBase64: false }),
    Youtube.configure({ nocookie: true, modestBranding: true }),
    VideoNode,
  ],
  editorProps: {
    attributes: {
      class: "richtext-content prose prose-sm prose-zinc focus:outline-none w-full min-h-[72px]",
    },
  },
  onUpdate: ({ editor }) => {
    model.value = editor.getHTML();
  },
  immediatelyRender: false,
});

watch(
  model,
  (nextValue) => {
    if (!editor.value) return;
    if (editor.value.getHTML() !== nextValue) {
      editor.value.commands.setContent(nextValue || "<p></p>", false);
    }
  },
);

watch(
  () => props.editable,
  (nextValue) => {
    editor.value?.setEditable(nextValue);
  },
);

function buttonClass(active = false) {
  const base = "inline-flex items-center justify-center rounded px-2 py-1 text-xs font-medium transition-colors";
  if (isCommentDark.value) {
    return `${base} ${active ? "bg-slate-700 text-sky-300" : "text-slate-300 hover:bg-slate-700"}`;
  }
  return `${base} ${active ? "bg-zinc-100 text-blue-600" : "text-zinc-600 hover:bg-zinc-100"}`;
}

const containerClass = computed(() =>
  isCommentDark.value
    ? "flex w-full flex-col rounded-xl border border-slate-700 bg-slate-900 text-slate-100"
    : "flex w-full flex-col rounded-xl border border-gray-200 bg-white",
);

const toolbarClass = computed(() =>
  isCommentDark.value
    ? "mb-0 space-y-1.5 border-b border-slate-700 bg-slate-900 p-2"
    : "mb-0 space-y-1.5 border-b border-zinc-200 p-2",
);

const youtubeInputClass = computed(() =>
  isCommentDark.value
    ? "flex-1 rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-slate-100 focus:border-transparent focus:outline-none focus:ring-1 focus:ring-sky-500"
    : "flex-1 rounded border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-800 focus:border-transparent focus:outline-none focus:ring-1 focus:ring-zinc-400",
);

const editorViewportClass = computed(() => {
  const sizeClass = props.compact ? "min-h-[120px] max-h-[200px]" : "h-[340px]";
  if (isCommentDark.value) {
    return `${sizeClass} overflow-hidden rounded-[18px] border border-slate-700 bg-slate-950 px-4 py-3`;
  }
  return `${sizeClass} overflow-hidden rounded-[18px] border border-zinc-200 bg-white px-4 py-3`;
});

const editorClass = computed(() => (isCommentDark.value ? "tiptap-editor-root w-full text-sm text-slate-100" : "tiptap-editor-root w-full text-sm text-gray-800"));

function openImageChooser() {
  if (window.innerWidth >= 768) {
    imageInputEl.value?.click();
    return;
  }
  imageModalOpen.value = true;
}

function handleYoutubeInsert() {
  if (!editor.value || !youtubeUrl.value.trim()) return;
  editor.value.commands.setYoutubeVideo({ src: youtubeUrl.value.trim() });
  youtubeUrl.value = "";
  youtubeOpen.value = false;
}

function handleImagePick(event: Event) {
  const file = (event.currentTarget as HTMLInputElement).files?.[0];
  if (!file || !editor.value) return;
  if (imageInputEl.value) imageInputEl.value.value = "";
  if (cameraInputEl.value) cameraInputEl.value.value = "";
  if (file.size > MAX_INLINE_IMAGE_SIZE) {
    emit("mediaError", "Anh trong noi dung toi da 5MB");
    return;
  }
  imageModalOpen.value = false;
  emit("mediaError", null);
  const renamed = nameContentFile(file);
  const blobUrl = URL.createObjectURL(file);
  editor.value.chain().focus().setImage({ src: blobUrl, alt: renamed.name }).run();
  emit("mediaPicked", blobUrl, renamed);
}

function handleVideoPick(event: Event) {
  const file = (event.currentTarget as HTMLInputElement).files?.[0];
  if (!file || !editor.value) return;
  if (videoInputEl.value) videoInputEl.value.value = "";
  if (file.size > MAX_INLINE_VIDEO_SIZE) {
    emit("mediaError", "Video trong noi dung toi da 200MB");
    return;
  }
  emit("mediaError", null);
  const renamed = nameContentFile(file);
  const blobUrl = URL.createObjectURL(file);
  editor.value.commands.insertContent(`<video src="${blobUrl}" controls="true"></video>`);
  emit("mediaPicked", blobUrl, renamed);
}
</script>

<style scoped>
:deep(.tiptap-editor-root .ProseMirror) {
  min-height: 100%;
  outline: none;
  border-radius: 14px;
}

:deep(.tiptap-editor-root .ProseMirror p:first-child) {
  margin-top: 0;
}

:deep(.tiptap-editor-root .ProseMirror p:last-child) {
  margin-bottom: 0;
}
</style>
